import copy
import json
from abc import ABC
from datetime import datetime, date

from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.timezone import make_aware

from baseAddMatchesToDB.BaseAddMatchesToDBTeamSports.BaseAddMatchesToDBTeamSports import BaseAddMatchesToDB
from parserHockey.parserSharedUtils import default_initial_match_statistic


class AddMatchesToDBHockey(BaseAddMatchesToDB, ABC):

    def __init__(self, _models, _list_matches=None, _dictionary_championships_with_matches=None,
                 _dictionary_teams_with_matches=None):
        super().__init__(_models, "Hockey", _list_matches, _dictionary_championships_with_matches,
                         _dictionary_teams_with_matches)

    from django.utils import timezone
    from django.db import IntegrityError
    import logging

    logger = logging.getLogger(__name__)

    def get_or_update_or_create_match(self, match_info, season, championship, home_team, away_team):
        """
            Получает существующий матч или создает новый на основе предоставленной информации.
            Обновляет матч, если это необходимо, используя новые данные из `match_info`.

            Аргументы:
                match_info (dict): Информация о матче, включая дату, статус, результат и т.д.
                season (Optional[int]): ID сезона матча.
                championship (int): ID чемпионата матча.
                home_team (int): ID домашней команды.
                away_team (int): ID гостевой команды.

            Возвращает:
                Match: Найденный или только что созданный экземпляр матча.
            """
        model_match = self._models["Match"]

        try:
            # region Обработка даты
            match_date = match_info["date"]

            if not isinstance(match_date, datetime):
                raise ValueError("Неподдерживаемый формат даты")

            if not timezone.is_aware(match_date):
                match_date = make_aware(match_date)

            # Нормализованная дата для поиска (без времени)
            search_date = match_date.date()
            # endregion

            # region Поиск существующего матча
            match = model_match.objects.filter(
                date__date=search_date,
                championship=championship,
                home_team=home_team,
                away_team=away_team
            ).first()
            # endregion

            # region Подготовка данных для обновления
            result = match_info.get("result", None)
            winner = None
            if result:
                winner = home_team if result["result"]["home"]["result"] > result["result"]["away"][
                    "result"] else away_team

            result = match_info.get("result", {})
            defaults = {
                "date": match_date,  # Сохраняем оригинальное время
                "season": season,
                "status": match_info.get("status"),
                "method_end_match": match_info.get("method_end_match"),
                "overtime_count": match_info.get("overtime_count", 0),
                "result": result,
                "winner": winner,
            }
            # endregion

            # region Логика создания/обновления
            if match:
                # Обновляем только если есть изменения
                update_fields = {}
                for field, value in defaults.items():
                    if getattr(match, field) != value:
                        update_fields[field] = value

                if update_fields:
                    model_match.objects.filter(pk=match.pk).update(**update_fields)
                    match.refresh_from_db()

                return match
            else:
                # Создаем новую запись с оригинальной датой и временем
                new_match = model_match.objects.create(
                    **defaults,
                    championship=championship,
                    home_team=home_team,
                    away_team=away_team
                )
                return new_match
            # endregion

        except IntegrityError as e:
            # logger.error(f"Integrity error: {str(e)}")
            raise
        except Exception as e:
            # logger.error(f"Unexpected error: {str(e)}")
            raise

    # Необходимо переписать в будущем
    def get_or_create_or_update_odds(self, match, odds):
        model_match_odds = self._models["MatchOdds"]

        if not odds:
            return None

        match_odds, created = model_match_odds.objects.get_or_create(
            match=match,
            bookmaker=odds["bookmaker"]
        )

        fields_to_check = ["score", "shots_on_goals", "two_minutes_penalties_time", "faceoffs_won", "power_play_goals"]
        type_odds = odds["type_odds"]
        needs_saves = False

        for field in fields_to_check:
            if field not in odds:
                continue

            current_odds = odds[field]

            field_data = copy.deepcopy(getattr(match_odds, field))
            list_odds_in_db = field_data.get(type_odds, [])

            if list_odds_in_db:
                last_odds_in_db = list_odds_in_db[-1]
            else:
                field_data[type_odds].append(current_odds)
                needs_saves = True
                setattr(match_odds, field, field_data)
                continue

            if last_odds_in_db["odds"] != current_odds["odds"]:
                field_data[type_odds].append(current_odds)
                needs_saves = True

        if needs_saves:
            # print(match.pk)
            # print(odds)
            # print("\n\n")
            # print(len(match_odds.score["line"]))
            match_odds.save()

        return match_odds

    def get_or_create_referees(self, referee_data):
        referees = []
        if referee_data is None:
            return None

        for main_referee in referee_data.get("main_referee", []):
            referee = self.get_or_create_referee(main_referee)
            referees.append(referee)

        for line_referee in referee_data.get("line_referee", []):
            referee = self.get_or_create_referee(line_referee)
            referees.append(referee)

        return referees

    def get_or_create_referees_championship(self, referees, championship):
        if referees is None:
            return None

        referees_championship = []

        for referee in referees:
            referee_championship = self.get_or_create_referee_championship(referee, championship)
            referees_championship.append(referee_championship)

        return referees_championship

    def get_or_create_referee_match(self, match, referees):
        model_match_referee = self._models["MatchReferee"]
        if referees is None:
            return None

        match_referees = []

        for referee in referees:
            match_referee, created = model_match_referee.objects.get_or_create(match=match, referee=referee)
            match_referees.append(match_referee)

        return match_referees

    def get_or_update_or_create_match_stat(self, match, match_statistics):
        model_match_stat = self._models["MatchStats"]

        if match_statistics is None:
            return None
        match_stat, created = model_match_stat.objects.get_or_create(
            match=match,
            defaults={**match_statistics}
        )
        print(match.pk, match.home_team, match.away_team, match.date)
        ### ПРИОРИТЕТ ПАРСЕРА СТАТИСТИКИ ВАЖНЕЕ ЧЕМ ПАРСЕРА РЕЗУЛЬТАТОВ
        if not created:
            for key, value in match_statistics.items():
                current_stat = getattr(match_stat, key, value)
                # print("Равны ли текущие статистика и статистика хранящиеся в бд?", current_stat == value)
                # print("Текущая статистика равна статистике по умолчанию?", value == default_initial_match_statistic)
                need_update_attr = AddMatchesToDBHockey.need_update_match_statistic_field(value, current_stat)
                if need_update_attr:
                    # print("Прошли вниз условия")
                    setattr(match_stat, key, value)
            match_stat.save()

        return match_stat

    @staticmethod
    def need_update_match_statistic_field(current_value, value_in_db):
        if current_value == value_in_db:
            return False

        if value_in_db == default_initial_match_statistic and current_value != default_initial_match_statistic:
            return True
        list_periods = ["1st_period", "2nd_period", "3rd_period"]
        list_detail = ["main_time", "overtime", "match"]

        for period in list_periods:
            value_statistic_in_db_is_none = (value_in_db[period]["home"]["result"] is None or
                                             value_in_db[period]["home"]["result"] is None)
            value_statistic_current_value_is_not_none = (current_value[period]["home"]["result"] is not None and
                                                         current_value[period]["home"]["result"] is not None)
            if value_statistic_in_db_is_none and value_statistic_current_value_is_not_none:
                return True

        for detail in list_detail:
            value_statistic_in_db_is_none = (value_in_db[detail]["home"]["result"] is None or
                                             value_in_db[detail]["home"]["result"] is None)
            value_statistic_current_value_is_not_none = (current_value[detail]["home"]["result"] is not None and
                                                         current_value[detail]["home"]["result"] is not None)
            if value_statistic_in_db_is_none and value_statistic_current_value_is_not_none:
                return True

        return False

    def add_matches_to_db(self, list_matches):
        i = 0
        all_players_needs_update_end_date = []
        all_team_coaches_needs_update_last_date = []
        print(len(list_matches))
        for match in list_matches:

            result = self.add_match_to_db(match)

            i += 1
            if result:
                print(f"ПРОХОД: {i}/{len(list_matches)} успешно добавлено")
            else:
                print(f"ПРОХОД: {i}/{len(list_matches)} - ЧТО-ТО ПОШЛО НЕ ТАК")
            # if i == 5:
            #     break
            # exit()

    def add_match_to_db(self, match):
        # try:
        with transaction.atomic():
            championship = self.get_or_update_or_create_championship(match["match_info"]["championship"])
            season = self.get_or_create_season(match["match_info"]["season"], championship)
            home_team = self.get_or_create_team(match["match_info"]["home"])
            away_team = self.get_or_create_team(match["match_info"]["away"])
            self.get_or_create_team_championship(home_team, championship)
            self.get_or_create_team_championship(away_team, championship)

            if "coach_home" in match["lineups"] and match["lineups"]["coach_home"] != {}:
                home_team_coach = self.get_or_create_coach(match["lineups"]["coach_home"])
                home_team_coach_team = self.get_or_create_coach_team(home_team_coach, home_team, match["lineups"]["coach_home"])
            if "coach_away" in match["lineups"] and match["lineups"]["coach_away"] != {}:
                away_team_coach = self.get_or_create_coach(match["lineups"]["coach_away"])
                away_team_coach_team = self.get_or_create_coach_team(away_team_coach, away_team, match["lineups"]["coach_away"])

            match_id = self.get_or_update_or_create_match(match["match_info"], season, championship, home_team,
                                                          away_team)
            if "odds" in match["match_info"]:
                self.get_or_create_or_update_odds(match_id, match["match_info"]["odds"])
            if "referee" in match["match_info"]:
                referees = self.get_or_create_referees(match["match_info"]["referee"])
                self.get_or_create_referee_match(match_id, referees)
                self.get_or_create_referees_championship(referees, championship)
            self.get_or_update_or_create_match_stat(match_id, match["match_statistics"])

        return True
        # except KeyError as e:
        #     print(f"Отсутствует ключ в словаре match(add_match_to_db): {e}")
        # except IntegrityError as e:
        #     match["match_info"]["date"] = match["match_info"]["date"].isoformat()
        #     with open('data.json', 'w') as file:
        #         json.dump(match, file)
        #     print(f"Ошибка целостности базы данных(add_match_to_db): {e}")
        #     exit()
        # except Exception as e:
        #     print(f"An unexpected error occurred(Произошла непредвиденная ошибка): {e}")
        #     exit()
