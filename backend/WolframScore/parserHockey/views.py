import json
from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from parserHockey.apiUrls import TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE, TRANSLATE_STATUS_TO_RUSSIAN_LANGUAGE
from parserHockey.applyChampionshipFilters import apply_championship_filters
from parserHockey.applyFilters import apply_filters
from parserHockey.models import Match, TeamCoach, Coach, Championship
from parserHockey.viewFiltersUtils import type_statistic, count_matches, periods, place_filters, result_after_period, \
    coach_filters, default_select_match_filters, default_select_championship_filters


def get_last_matches(count_matches, model, team, date):
    matches = model.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        date__lt=date
    ).order_by('-date')[:count_matches]
    return matches[::-1]


def serializer_last_matches(matches):
    result = []
    for m in matches:
        obj_match = {
            "id": m.id,
            "date": m.date,
            "teamHomeName": m.home_team.name,
            "teamAwayName": m.away_team.name,
            "status": TRANSLATE_STATUS_TO_RUSSIAN_LANGUAGE.get(m.status, ""),
            "methodEndMatch": TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE.get(m.method_end_match, ""),
            "score": {
                "home": m.result["result"]["home"]["result"] if m.result else None,
                "away": m.result["result"]["away"]["result"] if m.result else None
            }
        }
        result.append(obj_match)
    return result


class GetChampionshipsView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # Получаем текущую дату из параметров запроса
        date_str = request.GET.get('date')
        if date_str:
            date_str = date_str.split('T')[0]
            date = parse_date(date_str)
        else:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что дата корректна
        if not date:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем все матчи на указанную дату
        matches_today = Match.objects.filter(date__date=date)

        # Собираем чемпионаты и количество матчей
        championships = {}
        for match in matches_today:
            championship = match.championship  # Предполагается, что в модели Match есть FK на Championship
            if championship.id not in championships:
                championships[championship.id] = {
                    'id': championship.id,
                    'name': championship.name,
                    'countAll': 1,
                    'countLive': 1,
                    'imageCountry': request.build_absolute_uri(
                        championship.image_championship.url) if championship.image_championship else None
                }
            else:
                championships[championship.id]['countAll'] += 1

        # Преобразуем в список для JSON ответа
        championships_data = list(championships.values())

        # Возвращаем данные
        return Response(championships_data, status=status.HTTP_200_OK)


class GetMatchesByChampionshipView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # Получаем параметры из GET-запроса
        date_str = request.GET.get('date')
        championship_id = request.GET.get('championshipId')

        # Проверяем наличие параметров
        if not date_str or not championship_id:
            return Response({'error': 'Date and championshipId parameters are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Преобразуем строку в объект даты
        date_str = date_str.split('T')[0]
        match_date = parse_date(date_str)
        if not match_date:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        # Определяем начало и конец дня (00:00 и 23:59)
        start_datetime = datetime.combine(match_date, datetime.min.time())  # 00:00 на указанную дату
        end_datetime = start_datetime + timedelta(days=1) - timedelta(seconds=1)  # 23:59:59 на указанную дату

        # Фильтруем матчи по диапазону времени и чемпионату
        matches = Match.objects.filter(
            date__range=(start_datetime, end_datetime),  # Фильтр по диапазону времени
            championship__id=championship_id
        )

        # Собираем данные о матчах для ответа
        matches_data = []
        for match in matches:
            home_score = away_score = None
            home_score_periods = []
            away_score_periods = []

            if match.result:
                home_score = match.result["result"]["home"]["result"]
                away_score = match.result["result"]["away"]["result"]

                home_score_periods.append(match.result["1st_period"]["home"]["result"])
                away_score_periods.append(match.result["1st_period"]["away"]["result"])

                home_score_periods.append(match.result["2nd_period"]["home"]["result"])
                away_score_periods.append(match.result["2nd_period"]["away"]["result"])

                home_score_periods.append(match.result["3rd_period"]["home"]["result"])
                away_score_periods.append(match.result["3rd_period"]["away"]["result"])

                print(match.date, match.home_team, match.away_team)
                print(match.result["overtime"])
                if match.result["overtime"]["home"]["result"] is not None:
                    home_score_periods.append(match.result["overtime"]["home"]["result"])
                    away_score_periods.append(match.result["overtime"]["away"]["result"])

                if match.result["shootouts"]["home"]["result"] is not None:
                    home_score_periods.append(match.result["shootouts"]["home"]["result"])
                    away_score_periods.append(match.result["shootouts"]["away"]["result"])

            matches_data.append({
                'id': match.pk,
                'homeTeamImage': request.build_absolute_uri(
                    match.home_team.image.url) if match.home_team.image else None,
                'homeTeam': match.home_team.name,
                'awayTeam': match.away_team.name,
                'awayTeamImage': request.build_absolute_uri(
                    match.away_team.image.url) if match.away_team.image else None,
                'time': localtime(match.date).strftime('%H:%M'),  # Форматируем дату и время
                'status': TRANSLATE_STATUS_TO_RUSSIAN_LANGUAGE[match.status],
                'methodEndMatch': TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE[
                    match.method_end_match] if match.method_end_match else None,
                'scoreResult': {
                    "homeScore": home_score,
                    "awayScore": away_score
                },
                "scorePeriods": {
                    "homeScore": home_score_periods,
                    "awayScore": away_score_periods
                }
            })

        # Возвращаем данные в формате JSON
        return Response(matches_data, status=status.HTTP_200_OK)


class GetMatchInfoView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        id_match = request.GET.get("id")

        try:
            match = Match.objects.get(id=id_match)
        except Match.DoesNotExist:
            return Response({"error": "Match not found"}, status=status.HTTP_404_NOT_FOUND)

        home_score_result = away_score_result = home_score_main_time = away_score_main_time = None
        if match.result:
            home_score_result = match.result["result"]["home"]["result"]
            away_score_result = match.result["result"]["away"]["result"]

            home_score_main_time = match.result["main_time"]["home"]["result"]
            away_score_main_time = match.result["main_time"]["away"]["result"]

        home_team_coach = TeamCoach.objects.filter(team=match.home_team).order_by('-start_date').first()
        away_team_coach = TeamCoach.objects.filter(team=match.away_team).order_by('-start_date').first()

        # Получение последних 5 матчей для домашней команды
        last_matches_home_team = get_last_matches(5, Match, match.home_team, match.date)
        last_matches_home_team = serializer_last_matches(last_matches_home_team)

        # Получение последних 5 матчей для гостевой команды
        last_matches_away_team = get_last_matches(5, Match, match.away_team, match.date)
        last_matches_away_team = serializer_last_matches(last_matches_away_team)

        match_info = {
            "teamHome": {
                "id": match.home_team.pk,
                "name": match.home_team.name,
                "image": request.build_absolute_uri(match.home_team.image.url) if match.home_team.image else None,
            },
            "teamAway": {
                "id": match.away_team.pk,
                "name": match.away_team.name,
                "image": request.build_absolute_uri(match.away_team.image.url) if match.away_team.image else None,
            },
            "date": match.date,
            "status": TRANSLATE_STATUS_TO_RUSSIAN_LANGUAGE.get(match.status, ""),
            "methodEndMatch": TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE.get(match.method_end_match, ""),
            "score": {
                "mainTime": {
                    "home": home_score_main_time,
                    "away": away_score_main_time,
                },
                "result": {
                    "home": home_score_result,
                    "away": away_score_result,
                },
            },
            "coaches": {
                "home": {
                    "id": home_team_coach.pk if home_team_coach else None,
                    "name": Coach.objects.get(id=home_team_coach.coach.pk).name if home_team_coach else None
                },
                "away": {
                    "id": away_team_coach.pk if away_team_coach else None,
                    "name": Coach.objects.get(id=away_team_coach.coach.pk).name if away_team_coach else None
                }
            },
            "lastHomeTeamMatches": last_matches_home_team,
            "lastAwayTeamMatches": last_matches_away_team
        }

        referee_info = [
            {
                "id": 1,
                "name": "Сергей Белов",
                "averageFouls": "3.54",
            },
            {
                "id": 2,
                "name": "Сергей Иванов",
                "averageFouls": "3.12",
            }
        ]

        result = {
            "matchInfo": match_info,
            "refereesInfo": referee_info,
        }

        return Response(result, status=status.HTTP_200_OK)


def sort_seasons(season_list):
    def season_key(season):
        # Разделяем сезоны по "/" если есть
        parts = season.split('/')

        # Преобразуем каждую часть в целое число
        return tuple(int(part) for part in parts)

    # Сортируем список по ключу
    return sorted(season_list, key=season_key)


class FilterInfoView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        id_match = request.GET.get("id")

        match = Match.objects.get(id=id_match)
        home_team = match.home_team
        away_team = match.away_team

        home_team_unique_championships = (
            Match.objects.filter(Q(home_team=home_team) | Q(away_team=home_team))
            .values_list('championship__name', flat=True)
            .distinct()
        )

        away_team_unique_championships = (
            Match.objects.filter(Q(home_team=away_team) | Q(away_team=away_team))
            .values_list('championship__name', flat=True)
            .distinct()
        )

        home_team_unique_seasons = (
            Match.objects.filter(Q(home_team=home_team) | Q(away_team=home_team))
            .exclude(season__season=None)  # Исключаем None
            .values_list('season__season', flat=True)
            .distinct()
        )

        away_team_unique_seasons = (
            Match.objects.filter(Q(home_team=away_team) | Q(away_team=away_team))
            .exclude(season__season=None)  # Исключаем None
            .values_list('season__season', flat=True)
            .distinct()
        )

        result = {
            "filterOptions": {
                "dependentFilters": {
                    "typeStatistic": type_statistic,
                    "countMatches": count_matches,
                    "periods": periods,
                },
                "homeTeamFilters": {
                    "place": place_filters,
                    "championships": list(sorted(home_team_unique_championships)),
                    "seasons": sort_seasons(list(home_team_unique_seasons)),
                    "resultAfterPeriod": result_after_period,
                    "coach": coach_filters
                },
                "awayTeamFilters": {
                    "place": place_filters,
                    "championships": list(sorted(away_team_unique_championships)),
                    "seasons": sort_seasons(list(away_team_unique_seasons)),
                    "resultAfterPeriod": result_after_period,
                    "coach": coach_filters
                }
            },
            "selectFilters": {
                "customSelectFilters": True,
                "dependentFilters": default_select_match_filters["shared_filters"],
                "homeTeamFilters": default_select_match_filters["home_team_filters"],
                "awayTeamFilters": default_select_match_filters["away_team_filters"]
            }
        }

        return Response(result)


@method_decorator(csrf_protect, name='dispatch')
class GetMatchesWithFiltersView(APIView):

    def post(self, request):
        try:
            data = json.loads(request.body)
            id_match = data.get('id')
            filters = data.get('filters')

            # print(id_match)
            # print(filters)

            # Здесь вы должны использовать id_match и filters для получения данных о матчах
            result = apply_filters(id_match, filters)
            # print(result)

            return JsonResponse(result, safe=True)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


class GetChampionshipInfoView(APIView):

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        id_championship = request.GET.get('id')
        championship = Championship.objects.get(id=id_championship)
        championshipInfo = {
            "id": championship.pk,
            "name": championship.name,
            "image": request.build_absolute_uri(
                championship.image_country.url) if championship.image_country else None,
            "averageTotalGoals": 5.43,
            "averageTotalShotsOnGoal": 58.7,
            "averageTotalMinorPenalties": 4.67,
            "averageTotalFaceoffsWon": 61.02,
        }

        return JsonResponse(championshipInfo, safe=True)


class GetChampionshipFiltersView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        id_championship = request.GET.get('id')
        championship = Championship.objects.get(id=id_championship)

        championship_unique_seasons = (
            Match.objects.filter(championship=championship)
            .exclude(season__season=None)
            .values_list('season__season', flat=True)
            .distinct()
        )

        resultFilters = {
            "filtersOptions": {
                "dependentFilters": {
                    "typeStatistic": type_statistic,
                    "countMatches": count_matches,
                    "periods": periods,
                },
                "independentFilters": {
                    "place": place_filters,
                    "seasons": sort_seasons(list(championship_unique_seasons)),
                    "resultAfterPeriod": result_after_period,
                    "coach": coach_filters
                }
            },
            "selectFilters": {
                "dependentFilters": default_select_championship_filters["dependentFilters"],
                "independentFilters": default_select_championship_filters["independentFilters"],
            }
        }

        return JsonResponse(resultFilters, safe=True)


class GetTableChampionshipWithFiltersView(APIView):

    @method_decorator(csrf_protect)
    def post(self, request):
        # Используйте request.data вместо request.body
        data = request.data
        id_championship = data.get("id")
        filters = data.get("filters")

        list_table_championship_data = apply_championship_filters(id_championship, filters)
        headers = [
            {"header": "#",
             "sortField": "numberTeam",
             "typeSort": "number",
             },
            {"header": "Название",
             "sortField": "team",
             "typeSort": "string",
             },
            {"header": "Игр",
             "sortField": "countMatches",
             "typeSort": "number",
             },
            {"header": "В",
             "sortField": "win",
             "typeSort": "number",
             },
            {"header": "Н",
             "sortField": "draw",
             "typeSort": "number",
             },
            {"header": "П",
             "sortField": "lose",
             "typeSort": "number",
             },
            {"header": "Ср. разница",
             "sortField": "averageDifference",
             "typeSort": "number",
             },
            {"header": "ср.инд.Т",
             "sortField": "averageIndividualTotal",
             "typeSort": "number",
             },
            {"header": "ср.инд.Т соп.",
             "sortField": "averageIndividualTotalOpponent",
             "typeSort": "number",
             },
            {"header": "Ср. Т",
             "sortField": "averageTotal",
             "typeSort": "number",
             },
            {"header": "CКО инд.Т",
             "sortField": "meanSquareDeviationIndividualTotal",
             "typeSort": "number",
             },
            {"header": "CКО инд.Т соп.",
             "sortField": "meanSquareDeviationIndividualTotalOpponent",
             "typeSort": "number",
             },
            {"header": "CКО Т",
             "sortField": "meanSquareDeviationTotal",
             "typeSort": "number",
             },
        ]
        result = {
            "headers": headers,
            "tableChampionshipData": list_table_championship_data
        }

        # Здесь добавьте логику для обработки id_championship и filters

        return JsonResponse(result, safe=True)
