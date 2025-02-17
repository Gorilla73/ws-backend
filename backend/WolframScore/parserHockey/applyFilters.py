from datetime import datetime

from django.db.models import Q

from parserHockey.applyFiltersUtils import sum_safe, format_numeric_value, get_list_matches
from parserHockey.models import Match, MatchStats, TeamCoach
from parserHockey.apiUrls import PERIODS, TYPE_STATISTIC


def apply_filters(id_match, filters):
    match = Match.objects.get(id=id_match)
    home_team = match.home_team
    owner_home_team = {
        "id": home_team.pk,
        "name": home_team.name,
    }
    away_team = match.away_team
    owner_away_team = {
        "id": away_team.pk,
        "name": away_team.name,
    }

    all_matches_home_team = get_list_matches(
        Match.objects.filter(
            Q(home_team=home_team) | Q(away_team=home_team),
            date__lt=match.date  # Условие на дату
        ).order_by('-date'),
    )
    all_matches_home_team = add_coach_matches(all_matches_home_team, owner_home_team)

    # Получаем все матчи гостевой команды до даты текущего матча
    all_matches_away_team = get_list_matches(
        Match.objects.filter(
            Q(home_team=away_team) | Q(away_team=away_team),
            date__lt=match.date  # Условие на дату
        ).order_by('-date'),
    )
    all_matches_away_team = add_coach_matches(all_matches_away_team, owner_away_team)

    home_team_matches = apply_team_filters(all_matches_home_team, owner_home_team, filters["dependentFilters"],
                                           filters["homeTeamFilters"])
    away_team_matches = apply_team_filters(all_matches_away_team, owner_away_team, filters["dependentFilters"],
                                           filters["awayTeamFilters"])

    result = {
        "homeTeamMatches": home_team_matches,
        "ownerHomeTeam": owner_home_team,
        "awayTeamMatches": away_team_matches,
        "ownerAwayTeam": owner_away_team,
    }
    return result


def add_coach_matches(matches, owner_team):
    for match in matches:
        current_coach = get_coach_match(match["date"], owner_team)
        if current_coach:
            match["currentCoach"] = {
                "id": current_coach.pk,
                "name": current_coach.name
            }

    return matches


def get_coach_match(match_date, owner_team):
    try:
        # Преобразуем match_date в формат datetime.date, если это строка
        if isinstance(match_date, str):
            match_date = datetime.strptime(match_date, "%d.%m.%Y").date()

        # Используем filter для сложных условий с Q-объектами
        current_team_coach = TeamCoach.objects.filter(
            Q(end_date__gte=match_date) | Q(end_date__isnull=True),  # Дата окончания >= даты матча или отсутствует
            team=owner_team["id"],  # Передаем сам объект owner_team, а не его ID
            start_date__lte=match_date  # Дата начала <= даты матча
        ).get()  # Проверяем, что результат только один
        return current_team_coach.coach
    except TeamCoach.DoesNotExist:
        return None
    except ValueError as e:
        # Обработка некорректного формата даты
        raise ValueError(f"Неверный формат даты: {e}")


def apply_team_filters(matches, owner_team, shared_filters, team_filters):
    # {'customSelectFilters': True,
    #  'sharedFilters': {'typeStatistic': 'goals', 'countMatches': {'selectCount': '30', 'customCount': False}, 'period': 'allMatch'},
    #  'homeTeamFilters':
    #      {'place': 'all',
    #       'championships': 'all',
    #       'seasons': 'all',
    #       'resultAfterPeriod': 'all',
    #       'odds': {'selectOdds': 'all', 'customOdds': False},
    #       'coach': 'all'},
    #  'awayTeamFilters':
    #      {'place': 'all',
    #        'championships': 'all',
    #       'seasons': 'all',
    #       'resultAfterPeriod': 'all',
    #       'odds': {'selectOdds': 'all', 'customOdds': False},
    #       'coach': 'all'}
    #  }
    # Общие фильтры
    result_matches = apply_shared_filters(matches, shared_filters)
    # Командные фильтры
    result_matches = apply_place(result_matches, team_filters["place"], owner_team)
    result_matches = apply_championships(result_matches, team_filters["championships"])
    result_matches = apply_seasons(result_matches, team_filters["seasons"])

    result_matches = apply_result_after_period(result_matches, team_filters["resultAfterPeriod"], owner_team)
    result_matches = apply_coach(result_matches, team_filters["coach"], owner_team)

    return result_matches


def apply_shared_filters(matches, shared_filters):
    result_matches = apply_count_matches(matches, int(shared_filters["countMatches"]["selectCount"]))
    result_matches = apply_period_and_type_statistic(result_matches, shared_filters["period"],
                                                     shared_filters["typeStatistic"])
    return result_matches


def apply_count_matches(matches, count_matches):
    return matches[:count_matches]


def apply_period_and_type_statistic(matches, period, type_statistic):
    result = []
    for match in matches:
        try:
            match_stat = MatchStats.objects.get(match=match["id"])
        except MatchStats.DoesNotExist:
            # result.append({})
            continue
        if type_statistic == "goals":
            match_type_statistic_value = Match.objects.get(id=match["id"]).result
        else:
            match_type_statistic_value = getattr(match_stat, TYPE_STATISTIC[type_statistic], None)

        period_value = PERIODS[period]
        if period_value in ["1st_period", "2nd_period", "3rd_period"]:
            match["statistic"]["homeTeam"] = match_type_statistic_value[period_value]["home"]["result"]
            match["statistic"]["awayTeam"] = match_type_statistic_value[period_value]["away"]["result"]
        elif period_value == "afterFirstPeriod":
            match["statistic"]["homeTeam"] = sum_safe(match_type_statistic_value["2nd_period"]["home"]["result"],
                                                      match_type_statistic_value["3rd_period"]["home"]["result"])
            match["statistic"]["awayTeam"] = sum_safe(match_type_statistic_value["2nd_period"]["away"]["result"],
                                                      match_type_statistic_value["3rd_period"]["away"]["result"])
        else:
            match["statistic"]["homeTeam"] = match_type_statistic_value["main_time"]["home"]["result"]
            match["statistic"]["awayTeam"] = match_type_statistic_value["main_time"]["away"]["result"]

        match["statistic"]["homeTeam"] = format_numeric_value(match["statistic"]["homeTeam"])
        match["statistic"]["awayTeam"] = format_numeric_value(match["statistic"]["awayTeam"])

        result.append(match)

    return result


def apply_place(matches, place, owner_team):
    if place == "all":
        return matches

    result = []
    if place == "home":
        key_team = "homeTeam"
    else:
        key_team = "awayTeam"
    for match in matches:
        if match[key_team]["name"] == owner_team["name"]:
            result.append(match)

    return result


def apply_championships(matches, championships):
    if championships == "all":
        return matches

    result = []
    for match in matches:
        if match["championship"]["name"] in championships:
            result.append(match)

    return result


def apply_seasons(matches, seasons):
    if seasons == "all":
        return matches

    result = []
    for match in matches:
        if match["season"] in seasons:
            result.append(match)

    return result


def apply_odds(matches, odds):
    pass


def get_team_score(match_result, period_keys):
    home_score = sum_safe(*(match_result[period]["home"]["result"] for period in period_keys))
    away_score = sum_safe(*(match_result[period]["away"]["result"] for period in period_keys))
    return home_score, away_score


def filter_matches(matches, owner_team, condition_func):
    result = []
    for match in matches:
        match_result = Match.objects.get(id=match["id"]).result

        print(match["id"], match["championship"]["name"], match["date"], match["homeTeam"]["name"], "-", match["awayTeam"]["name"])
        # print(match_result, "\n\n")
        if condition_func(match, match_result, owner_team):
            result.append(match)
    return result


def win_after_period_condition(match, match_result, owner_team, periods):
    home_score, away_score = get_team_score(match_result, periods)
    if home_score > away_score and match["homeTeam"]["name"] == owner_team["name"]:
        return True
    if home_score < away_score and match["awayTeam"]["name"] == owner_team["name"]:
        return True
    return False


def draw_after_period_condition(match, match_result, owner_team, periods):
    home_score, away_score = get_team_score(match_result, periods)
    return home_score == away_score


def lose_after_period_condition(match, match_result, owner_team, periods):
    home_score, away_score = get_team_score(match_result, periods)
    if home_score > away_score and match["homeTeam"]["name"] != owner_team["name"]:
        return True
    if home_score < away_score and match["awayTeam"]["name"] != owner_team["name"]:
        return True
    return False


def apply_result_after_period(matches, result_after_period, owner_team):
    if result_after_period == "all":
        return matches

    period_mapping = {
        "winAfterFirstPeriod": (win_after_period_condition, ["1st_period"]),
        "drawAfterFirstPeriod": (draw_after_period_condition, ["1st_period"]),
        "loseAfterFirstPeriod": (lose_after_period_condition, ["1st_period"]),
        "winAfterSecondPeriod": (win_after_period_condition, ["1st_period", "2nd_period"]),
        "drawAfterSecondPeriod": (draw_after_period_condition, ["1st_period", "2nd_period"]),
        "loseAfterSecondPeriod": (lose_after_period_condition, ["1st_period", "2nd_period"]),
    }

    if result_after_period in period_mapping:
        condition_func, periods = period_mapping[result_after_period]
        return filter_matches(matches, owner_team,
                              lambda match, result, team: condition_func(match, result, team, periods))

    return []


def apply_coach(matches, coach, owner_team):
    if coach == "all":
        return matches

    # Получить последнего тренера, если он есть
    last_coach = TeamCoach.objects.filter(team=owner_team["id"]).order_by('-start_date').first()

    # # Если тренера не найдено, возвращаем пустой результат или весь список матчей
    # if not last_coach:
    #     return []

    # Фильтруем матчи, когда команда была под руководством последнего тренера
    result = []
    for match in matches:
        # Преобразуем строку с датой в объект даты
        match_date = datetime.strptime(match["date"], "%d.%m.%Y").date()

        # Предполагаем, что сравнение должно быть "если дата матча >= дате начала работы тренера"
        if match_date >= last_coach.start_date:
            result.append(match)

    return result
