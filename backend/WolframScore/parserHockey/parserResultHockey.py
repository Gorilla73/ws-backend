import copy
import json
import os
from datetime import timedelta, datetime

import django

from parserHockey.dictionary_models import models_hockey
from parserHockey.parserSharedUtils import safe_division, get_default_initial_match_statistic

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

django.setup()

from requests.exceptions import RequestException

from parserHockey.addMatchesToDB import AddMatchesToDBHockey
from parserHockey.parserResultHockeyUtils import TRANSLATE_NAME_STATISTIC
from parserHockey.parserSharedUtils import BLACK_LIST_CHAMPIONSHIPS, default_initial_match_result, \
    default_initial_match_statistic
from parsing.requests import get_request


class ParserResultHockey:
    def __init__(self, _url_championships, _url_games, _sportId):
        """
            Конструктор класса ParserResultHockey.

            Инициализирует объект с параметрами для парсинга данных о хоккейных матчах.

            Параметры:
            _url_championships (str): URL для получения данных о чемпионатах.
            _url_games (str): URL для получения данных о матчах.
            _sportId (int): ID спорта, который будет использоваться для фильтрации данных (например, 2 для хоккея).

            Атрибуты:
            __url_championships (str): Приватный URL для чемпионатов.
            __url_games (str): Приватный URL для матчей.
            __headers (dict): Заголовки HTTP-запроса для получения данных.
            __sportId (int): Приватный ID спорта.
            """
        self.__url_championships = _url_championships
        self.__url_games = _url_games
        self.__headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        self.__sportId = _sportId

    def parsing(self, start_date, end_date):
        """
        Основной метод для парсинга данных о матчах в заданном диапазоне дат.

        Этот метод выполняет последовательные запросы к API для получения данных о чемпионатах и матчах.
        Он фильтрует чемпионаты, исключая те, которые находятся в черном списке, и затем подготавливает данные
        для записи в файл и (потенциально) добавления в базу данных.

        Параметры:
        start_date (str): Начальная дата парсинга в формате "ГГГГ-ММ-ДД".
        end_date (str): Конечная дата парсинга в формате "ГГГГ-ММ-ДД".

        Процесс:
        - Запрос данных о чемпионатах и матчах на каждую дату.
        - Фильтрация чемпионатов по черному списку.
        - Подготовка данных для добавления в БД.
        - Запись данных в файл JSON.

        Пример:
        parser.parsing("2024-09-03", "2024-09-04")
        """

        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        while current_date < end_date:
            date_from = current_date.strftime("%Y-%m-%d 23:59:59")
            next_day = current_date + timedelta(days=1)
            date_to = next_day.strftime("%Y-%m-%d 23:59:59")

            date_from_ts = int(datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S").timestamp())
            date_to_ts = int(datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S").timestamp())

            championships = self.get_championships(date_from_ts, date_to_ts)

            if not championships:
                print(f"Не удалось получить данные о чемпионатах для даты {current_date.strftime('%Y-%m-%d')}")
                current_date = next_day
                continue

            championships = self.delete_black_championships(championships)

            games = self.get_games(championships, date_from_ts, date_to_ts)

            if not games:
                print(f"Не удалось получить данные о матчах для даты {current_date.strftime('%Y-%m-%d')}")
                current_date = next_day
                continue

            prepared_data_for_db = {}
            for championship in games:
                prepared_data_for_db[championship] = self.prepare_data_for_db(games[championship])

            # with open('data.json', 'w') as file:
            #     json.dump(prepare_data, file)

            # add_championships_with_matches_to_db(prepare_data)
            add_matches_obj = AddMatchesToDBHockey(
                _models=models_hockey, _dictionary_championships_with_matches=prepared_data_for_db)
            add_matches_obj.add_championships_with_matches_to_db()

            current_date = next_day

    def get_championships(self, date_from_ts, date_to_ts):
        """
            Выполняет запрос к API для получения данных о чемпионатах в указанном временном диапазоне.

            Параметры:
            date_from_ts (int): Временная метка начала периода в формате UNIX (timestamp).
            date_to_ts (int): Временная метка конца периода в формате UNIX (timestamp).

            Возвращает:
            dict: Данные о чемпионатах, полученные от API. В случае ошибки запроса возвращает None.

            Исключения:
            - Обрабатывает RequestException, возникающие при сетевых ошибках или проблемах с сервером,
              и выводит сообщение об ошибке в консоль.

            Пример:
            championships = self.get_championships(1693766400, 1693852800)

            """
        params = {
            "dateFrom": date_from_ts,
            "dateTo": date_to_ts,
            "sportIds": self.__sportId,
            "ref": 1,
            "gr": 285
        }

        try:
            championships = get_request(url=self.__url_championships, params=params, headers=self.__headers)
        except RequestException as e:
            print(f"Ошибка сети или сервера при запросе чемпионатов: {e}")
            return None

        return championships

    @staticmethod
    def delete_black_championships(championships):
        """
            Удаляет чемпионаты, которые содержатся в черном списке, из переданного списка чемпионатов.

            Параметры:
            championships (dict): Словарь с ключами "items" (список чемпионатов) и "count" (общее количество чемпионатов).

            Возвращает:
            dict: Обновленный словарь чемпионатов с исключенными элементами, находящимися в черном списке.

            Логика:
            - Фильтрует чемпионаты, проверяя их названия через метод `is_valid_championship`.
            - Рассчитывает количество удаленных чемпионатов и уменьшает общий счетчик ("count").

            Пример:
            filtered_championships = ParserResultHockey.delete_black_championships(championships)
            """
        filtered_championships = [ch for ch in championships["items"] if
                                  ParserResultHockey.is_valid_championship(ch["name"])]

        removed_count = len(championships["items"]) - len(filtered_championships)
        championships["items"] = filtered_championships
        championships["count"] -= removed_count

        return championships

    @staticmethod
    def is_valid_championship(championship):
        """
            Проверяет, находится ли название чемпионата в черном списке.

            Параметры:
            championship (str): Название чемпионата для проверки.

            Возвращает:
            bool: Возвращает True, если чемпионат не содержится в черном списке, иначе False.

            Логика:
            - Проходит по списку черных чемпионатов (BLACK_LIST_CHAMPIONSHIPS).
            - Если часть названия черного чемпионата содержится в названии переданного чемпионата,
              возвращает False, иначе True.

            Пример:
            is_valid = ParserResultHockey.is_valid_championship("Континентальная хоккейная лига")
            """
        if championship == "КХЛ" or championship == "NHL":
            return True
        return False
        # for black_championship in BLACK_LIST_CHAMPIONSHIPS:
        #     if black_championship in championship:
        #         return False
        # return True

    def get_games(self, championships, date_from_ts, date_to_ts):
        """
            Получает список игр для каждого чемпионата в указанный временной диапазон.

            Параметры:
            championships (dict): Словарь с информацией о чемпионатах, включая их ID.
            date_from_ts (int): Временная метка начала периода (timestamp).
            date_to_ts (int): Временная метка конца периода (timestamp).

            Возвращает:
            dict: Словарь, где ключами являются названия чемпионатов, а значениями — список игр для каждого чемпионата.
                  Если в данных чемпионатов нет ключа 'items', возвращает None.

            Логика:
            - Проверяет наличие игр для каждого чемпионата на основе его ID.
            - Выполняет запрос к API для каждого чемпионата, передавая его ID в параметрах запроса.
            - Собирает все игры в словарь, где ключ — это название чемпионата, а значение — список игр.

            Пример:
            games = self.get_games(championships, 1693766400, 1693852800)
            """
        params = {
            "dateFrom": date_from_ts,
            "dateTo": date_to_ts,
            "champId": None,
            "ref": 1,
            "gr": 285
        }
        games = {}

        if 'items' not in championships:
            return None

        for championship in championships['items']:
            params['champId'] = championship['id']

            games_championship = get_request(url=self.__url_games, params=params, headers=self.__headers)

            if games_championship is not None:
                games[championship['name']] = games_championship['items']

        return games

    @staticmethod
    def prepare_data_for_db(matches):
        """
            Подготавливает данные матчей для вставки в базу данных.

            Параметры:
            matches (list): Список матчей, содержащих информацию о командах, результатах, статистике и прочем.

            Возвращает:
            list: Список словарей, каждый из которых представляет подготовленные данные для одного матча,
                  включая информацию о командах, результатах, методе завершения матча, овертаймах и статистике.

            Логика:
            - Фильтрует матчи, которые не соответствуют нужным критериям (например, если это серия игр или команды имеют неправильные имена).
            - Использует вспомогательные методы для обработки результата матча и его статистики.
            - Формирует финальный формат данных, включая имена команд, результаты и дополнительную информацию о матче, готовый для записи в БД.

            Пример:
            prepared_data = ParserResultHockey.prepare_data_for_db(matches)
            """
        url_logo = "https://v3.traincdn.com/resized/size16/sfiles/logo_teams/"
        prepared_data = []

        for match in matches:

            print(match["champName"], match["opp1"], "-", match["opp2"])

            if "matchInfosFull" in match and ("Серия игр" in match["matchInfosFull"] or
                                              "матчей" in match["matchInfosFull"] or
                                              "матча" in match["matchInfosFull"]):
                continue
            if len(match["opp1"].split("/")) > 1 or len(match["opp2"].split("/")) > 1:
                continue
            if match["opp1"] == "Хозяева" or match["opp2"] == "Гости":
                continue

            sub_games = match.get("subGame", [])
            method_end_match, overtime_count, result_score = ParserResultHockey.get_result(match["score"], sub_games)

            prepared_match = {
                "match_info": {
                    "home": {
                        "name": match["opp1"],
                        "image": url_logo + match["opp1Images"][0]
                    },
                    "away": {
                        "name": match["opp2"],
                        "image": url_logo + match["opp2Images"][0]
                    },
                    "championship": {
                        "name": match["champName"]
                    },
                    "season": {
                        "years": None,
                    },
                    # Подумать, как правильно записать None, чтобы не было проблем с добавлением в бд
                    "referee": None,
                    "date": datetime.fromtimestamp(match['dateStart']),
                    # "date": datetime.fromtimestamp(match['dateStart']).isoformat(),
                    # "odds": odds,
                    "status": "completed",
                    "method_end_match": method_end_match,
                    "overtime_count": overtime_count,
                    "result": result_score
                },
                "lineups": {
                    "home": None,
                    "away": None,
                },
                "player_statistics": {
                    "home": None,
                    "away": None
                },
                "match_statistics": ParserResultHockey.get_match_statistics(sub_games)
            }

            prepared_data.append(prepared_match)

        # with open('data.json', 'w', encoding='utf-8') as f:
        #     json.dump(prepared_data, f, ensure_ascii=False, indent=4)
        #     exit()

        return prepared_data

    @staticmethod
    def get_result(score, sub_games):
        """
            Обрабатывает результат матча и информацию о субиграх, возвращает метод завершения матча, количество овертаймов и результаты.

            Параметры:
            score (str): Строка с общим результатом и счетами по периодам. Пример: "106:88 (28:18, 39:28, 19:21, 20:21)"
            sub_games (list): Список субигр, где каждая субигра представлена словарем с информацией о результате и типе.

            Возвращает:
            tuple: Кортеж из трех элементов:
                - method_end_match (str): Метод завершения матча ("MT" для основного времени, "OT" для овертайма, "SO" для буллитов).
                - overtime_count (int): Количество овертаймов.
                - result_score (dict): Словарь с результатами матча, включая основной результат, овертаймы, буллиты и периоды.
            """

        method_end_match = "MT"
        overtime_count = 0
        result_score = copy.deepcopy(default_initial_match_result)

        # Разделяем общий счет и счета по периодам
        # score = 2:6 (0:2,0:2,2:2)
        result_match, score_periods = ParserResultHockey.parse_score(score)

        # Обработка периодов
        periods = ["1st_period", "2nd_period", "3rd_period"]
        if len(score_periods) >= 3:  # Если есть информация по каждому периоду
            for i, period in enumerate(periods):
                home_score, away_score = map(int, score_periods[i].split(":"))
                result_score[period]["home"]["result"] = home_score
                result_score[period]["away"]["result"] = away_score

        # Обработка итогового результата
        home_result, away_result = map(int, result_match.split(":"))
        result_score["result"]["home"]["result"] = home_result
        result_score["result"]["away"]["result"] = away_result

        # Обработка овертайма и буллитов
        for sub_game in sub_games:
            if "score" not in sub_game:
                continue
            result_score_sub_game = sub_game["score"].split()[0]
            home_score, away_score = map(int, result_score_sub_game.split(":"))
            if sub_game["title"] == "Овертайм":
                method_end_match = "OT"
                overtime_count += 1
                result_score["overtime"]["home"]["result"] = home_score
                result_score["overtime"]["away"]["result"] = away_score
            elif sub_game["title"] == "Серия буллитов":
                method_end_match = "SO"
                result_score["shootouts"]["home"]["result"] = home_score
                result_score["shootouts"]["away"]["result"] = away_score

        # Обработка результата основного времени
        if method_end_match == "MT":
            result_score["main_time"]["home"]["result"] = home_result
            result_score["main_time"]["away"]["result"] = away_result
        else:
            result_score["main_time"]["home"]["result"] = min(home_result, away_result)
            result_score["main_time"]["away"]["result"] = min(home_result, away_result)

        return method_end_match, overtime_count, result_score

    @staticmethod
    def parse_score(score):
        """
        Парсит общий результат и разбивку по периодам из строки.

        Пример входной строки: "106:88 (28:18, 39:28, 19:21, 20:21)"

        :param score: Строка с результатом матча и счетами по периодам.
        :return: Кортеж из общего результата и списка с разбивкой по периодам.
        """
        result_match, score_periods = score.split()  # Пример: "106:88 (28:18, 39:28, 19:21, 20:21)"
        score_periods = score_periods[1:-1].split(',')  # Пример: ['28:18', '39:28', '19:21', '20:21']
        return result_match, score_periods

    @staticmethod
    def get_match_statistics(sub_games):
        """
            Обрабатывает статистику матчей из списка субигр и возвращает статистику по матчам.

            Параметры:
            sub_games (list): Список субигр, каждая из которых представлена словарем с информацией о названии и результате.

            Возвращает:
            dict: Словарь, где ключи - это названия статистик (переведенные с помощью TRANSLATE_NAME_STATISTIC),
                  а значения - это статистика матчей, включающая информацию по периодам и основному времени.
            """
        match_statistics = {}
        for sub_game in sub_games:
            if sub_game.get("title", None) in TRANSLATE_NAME_STATISTIC:
                name_statistic = TRANSLATE_NAME_STATISTIC[sub_game["title"]]
                match_statistics[name_statistic] = copy.deepcopy(
                    default_initial_match_statistic)
                score = sub_game.get("score", None)
                if score is None:
                    continue
                result_match, score_periods = ParserResultHockey.parse_score(score)

                periods = ["1st_period", "2nd_period", "3rd_period"]
                match_statistics[name_statistic] = get_default_initial_match_statistic()
                if len(score_periods) >= 3:  # Если есть информация по каждому периоду
                    for i, period in enumerate(periods):
                        home_score, away_score = map(int, score_periods[i].split(":"))
                        match_statistics[name_statistic][period]["home"]["result"] = home_score
                        match_statistics[name_statistic][period]["away"]["result"] = away_score

                # Обработка итогового результата
                home_result, away_result = map(int, result_match.split(":"))
                match_statistics[name_statistic]["main_time"]["home"]["result"] = home_result
                match_statistics[name_statistic]["main_time"]["away"]["result"] = away_result

                if name_statistic == "two_minutes_penalties_time":
                    match_statistics.update({"two_minutes_penalties": ParserResultHockey.get_two_minutes_penalties(
                        match_statistics["two_minutes_penalties_time"])})

        return match_statistics

    @staticmethod
    def get_two_minutes_penalties(two_minutes_penalties_time):
        two_minutes_penalties = copy.deepcopy(default_initial_match_statistic)
        periods = ["1st_period", "2nd_period", "3rd_period", "main_time", "overtime", "match"]
        for period in periods:
            two_minutes_penalties[period]["home"]["result"] = safe_division(
                two_minutes_penalties_time[period]["home"]["result"], 2)
            two_minutes_penalties[period]["away"]["result"] = safe_division(
                two_minutes_penalties_time[period]["away"]["result"], 2)

        return two_minutes_penalties


if __name__ == '__main__':
    root_url = "https://1xlite-581089.top/"
    url_championships = root_url + "service-api/result/web/api/v1/champs"
    url_games = root_url + "service-api/result/web/api/v1/games"
    sportId = 2

    # if not os.getenv('DJANGO_SETTINGS_MODULE'):
    #     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WolframScore.settings')
    #
    # django.setup()

    parser = ParserResultHockey(_url_championships=url_championships,
                                _url_games=url_games,
                                _sportId=sportId)
    # parser.parsing("2024-09-03", "2024-12-21")
    parser.parsing("2024-12-18", "2024-12-21")

# Формат даты: (ГГГГ-MM-ДД)
# Для parser.parsing("2024-05-16", "2024-05-17") - Data from 2024-05-16 23:59:59 to 2024-05-17 23:59:59
