from django.db.models import Q

from parserHockey.applyFilters import apply_shared_filters, apply_place, apply_seasons, \
    apply_result_after_period, apply_coach
from parserHockey.applyFiltersUtils import get_list_matches
from parserHockey.models import Championship, TeamChampionship, Match
from datetime import datetime, timedelta

import numpy as np


def apply_championship_filters(id_championship, filters):
    championship = Championship.objects.get(id=id_championship)
    print(championship)
    all_team_championship = TeamChampionship.objects.filter(championship=championship).values_list("team__id",
                                                                                                   "team__name")

    sorted_team_names = [team_name for _, team_name in sorted(all_team_championship, key=lambda x: x[1])]

    yesterday = datetime.now() - timedelta(days=1)

    table_championship_data = []

    for team in all_team_championship:
        team_id, team_name = team  # Распаковываем кортеж
        team_matches = get_list_matches(Match.objects.filter(
            Q(home_team=team_id) | Q(away_team=team_id),
            date__lt=yesterday,  # Условие на дату
            championship=championship,
        ).order_by('-date'))
        owner_team = {
            "id": team_id,
            "name": team_name,
        }

        team_matches = apply_championship_filters_for_team(team_matches, owner_team, filters["dependentFilters"],
                                                           filters["independentFilters"])
        number_team = sorted_team_names.index(team_name) + 1
        table_team_championship = get_table_championship_data(team_matches, number_team, owner_team)

        table_championship_data.append(table_team_championship)

    sorted_table_championship_data = sorted(table_championship_data, key=lambda x: x["numberTeam"])
    return sorted_table_championship_data


def apply_championship_filters_for_team(team_matches, owner_team, dependent_filters, independent_filters):
    result_matches = apply_shared_filters(team_matches, dependent_filters)
    result_matches = apply_championship_independent_filters_for_team(result_matches, owner_team, independent_filters)

    return result_matches


def apply_championship_independent_filters_for_team(team_matches, owner_team, independent_filters):
    result_matches = apply_place(team_matches, independent_filters["place"], owner_team)
    # result_matches = apply_championships(result_matches, independent_filters["championships"])
    result_matches = apply_seasons(result_matches, independent_filters["seasons"])

    result_matches = apply_result_after_period(result_matches, independent_filters["resultAfterPeriod"], owner_team)
    result_matches = apply_coach(result_matches, independent_filters["coach"], owner_team)

    return result_matches


def get_table_championship_data(team_matches, number_team, owner_team):
    result = {
        "numberTeam": number_team,
        "team": {
            "id": owner_team["id"],
            "name": owner_team["name"],
        },
        "countMatches": len(team_matches),
        "win": 0,
        "draw": 0,
        "lose": 0,
        "averageDifference": 0,
        "averageIndividualTotal": 0,
        "averageIndividualTotalOpponent": 0,
        "averageTotal": 0,
        "meanSquareDeviationIndividualTotal": 0,
        "meanSquareDeviationIndividualTotalOpponent": 0,
        "meanSquareDeviationTotal": 0,
    }

    undefined_statistic_count = 0

    statistic_owner_team_data = []
    statistic_opponent_team_data = []
    statistic_total_data = []

    for match in team_matches:

        if owner_team["id"] == match["homeTeam"]["id"]:
            key_owner_team = "homeTeam"
            key_opponent_team = "awayTeam"
        else:
            key_owner_team = "awayTeam"
            key_opponent_team = "homeTeam"

        if match["statistic"]["homeTeam"] and match["statistic"]["awayTeam"]:

            if match["statistic"][key_owner_team] > match["statistic"][key_opponent_team]:
                result["win"] += 1
            elif match["statistic"][key_owner_team] == match["statistic"][key_opponent_team]:
                result["draw"] += 1
            else:
                result["lose"] += 1

            result["averageDifference"] += (match["statistic"][key_owner_team] - match["statistic"][key_opponent_team])
            result["averageIndividualTotal"] += match["statistic"][key_owner_team]
            result["averageIndividualTotalOpponent"] += match["statistic"][key_opponent_team]
            result["averageTotal"] += (match["statistic"][key_owner_team] + match["statistic"][key_opponent_team])

            statistic_owner_team_data.append(match["statistic"][key_owner_team])
            statistic_opponent_team_data.append(match["statistic"][key_opponent_team])
            statistic_total_data.append(match["statistic"][key_owner_team] + match["statistic"][key_opponent_team])
        else:
            undefined_statistic_count += 1

    if undefined_statistic_count == len(team_matches):
        return {
            "numberTeam": number_team,
            "team": {
                "id": owner_team["id"],
                "name": owner_team["name"],
            },
            "countMatches": len(team_matches),
            "win": None,
            "draw": None,
            "lose": None,
            "averageDifference": None,
            "averageIndividualTotal": None,
            "averageIndividualTotalOpponent": None,
            "averageTotal": None,
            "meanSquareDeviationIndividualTotal": None,
            "meanSquareDeviationIndividualTotalOpponent": None,
            "meanSquareDeviationTotal": None,
        }

    result["countMatches"] -= undefined_statistic_count

    result["averageDifference"] = round(result["averageDifference"] / result["countMatches"], 2)
    result["averageIndividualTotal"] = round(result["averageIndividualTotal"] / result["countMatches"], 2)
    result["averageIndividualTotalOpponent"] = round(result["averageIndividualTotalOpponent"] / result["countMatches"],
                                                     2)
    result["averageTotal"] = round(result["averageTotal"] / result["countMatches"], 2)

    result["meanSquareDeviationIndividualTotal"] = get_std(statistic_owner_team_data)
    result["meanSquareDeviationIndividualTotalOpponent"] = get_std(statistic_opponent_team_data)
    result["meanSquareDeviationTotal"] = get_std(statistic_total_data)

    return result


def get_std(data):
    if len(data) <= 1:  # Нельзя вычислить стандартное отклонение
        return None
    std_dev_sample = np.std(data, ddof=1)
    return round(std_dev_sample, 2)
