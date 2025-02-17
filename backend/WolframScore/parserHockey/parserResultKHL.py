import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

import django

django.setup()


import logging
import pprint
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup, Tag

from parserHockey.addMatchesToDB import AddMatchesToDBHockey
from parserHockey.applyFiltersUtils import sum_safe
from parserHockey.parserKHL import ParserKHL
from parserHockey.parserSharedUtils import get_default_initial_match_result, get_default_initial_match_statistic
from parserHockey.parserHockeyUtils import time_to_seconds
from parsing.requests import fetch_html
from parserHockey.dictionary_models import models_hockey

logger = logging.getLogger("ParserResultKHL")
logger.info("Логирование настроено правильно!")


class ParserResultKHL(ParserKHL):

    def __init__(self, _header, _url_calendar, _season_id):
        super().__init__(_header, _url_calendar, _season_id)

    def parsing(self, start_date, end_date):
        logger.info(f"Начало парсинга с {start_date} по {end_date}")

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        logger.info(f"Переменные 'start_date' и 'end_date' преобразованы в формат datetime")

        current_date = start_date
        matches = []
        while current_date <= end_date:
            print(f"Обрабатываю дату: {current_date}")
            logger.info(f"Обрабатывается дата: {current_date}")

            html_page_schedule_matches = self.fetch_html_schedule_by_date(date=current_date)
            links = self.get_links_matches_by_html_schedule(html_page_schedule_matches)

            print(links)

            for link in links:
                match_page_html = self.fetch_html_match_page(link)
                match_page_html_play_by_play = self.fetch_html_match_play_by_play(link)

                status = self.get_status_match(match_page_html)
                if status != "матч завершен":
                    continue

                match_data = self.get_match_data(match_page_html, match_page_html_play_by_play, current_date)
                matches.append(match_data)

            current_date += timedelta(days=1)

        add_matches_obj = AddMatchesToDBHockey(
            _models=models_hockey, _dictionary_championships_with_matches={"КХЛ": matches})
        add_matches_obj.add_championships_with_matches_to_db()

        logger.info("Парсинг завершён успешно")

    @staticmethod
    def get_links_matches_by_html_schedule(html_page):
        soup = BeautifulSoup(html_page, 'html.parser')

        links = soup.find_all('a', string=re.compile(r"^\s*Текст\s*$"))
        hrefs = [link['href'] for link in links]

        logger.info(f"Получены ссылки на матчи: {hrefs}")
        return hrefs

    def fetch_html_match_page(self, url):
        params = {}
        response_status, response_html = fetch_html(url=url, headers=self._headers, params=params, logger=logger)
        return response_html

    def fetch_html_match_play_by_play(self, url):
        params = {}
        url_play_by_play = url + "#play-by-play"
        response_status, response_html = fetch_html(url=url_play_by_play, headers=self._headers, params=params,
                                                    logger=logger)
        return response_html

    @staticmethod
    def get_status_match(html_match_page):
        soup = BeautifulSoup(html_match_page, 'html.parser')
        p_tag = soup.select_one('.preview-frame .preview-frame__center .preview-frame__center-text')
        return p_tag.get_text(strip=True)

    def get_match_data(self, match_page_html, match_page_html_play_by_play, current_date):
        match_info, original_team_names, coach_names = self.get_match_info(match_page_html, current_date)
        # match_statistic = get_default_initial_match_statistic()
        team_image_paths = {
            "home": match_info["home"]["image"],
            "away": match_info["away"]["image"]
        }
        lineups = {
            "home": None,
            "away": None,
            "coach_home": {
                "name": coach_names["home_team"],
                "start_date": match_info["date"]
            },
            "coach_away": {
                "name": coach_names["away_team"],
                "start_date": match_info["date"]
            }
        }
        match_statistic = {
            "two_minutes_penalties": get_default_initial_match_statistic(),
            "five_minutes_penalties": get_default_initial_match_statistic(),
            "two_minutes_penalties_time": get_default_initial_match_statistic(),
            "five_minutes_penalties_time": get_default_initial_match_statistic(),
            "shots": get_default_initial_match_statistic(),
            "shots_on_goals": get_default_initial_match_statistic(),
            "shooting_percentage": get_default_initial_match_statistic(),
            "blocked_shots": get_default_initial_match_statistic(),
            "shots_off_goal": get_default_initial_match_statistic(),
            "goalkeeper_saves": get_default_initial_match_statistic(),
            "goalkeeper_saves_percentage": get_default_initial_match_statistic(),
            # "penalties": get_default_initial_match_statistic(),
            # "power_play_goals": get_default_initial_match_statistic(),
            # "shorthanded_goals": get_default_initial_match_statistic(),
            # "power_play_percentage": get_default_initial_match_statistic(),
            # "penalty_kill_percentage": get_default_initial_match_statistic(),
            "hits": get_default_initial_match_statistic(),
            "faceoffs_won": get_default_initial_match_statistic(),
            "faceoffs_won_percentage": get_default_initial_match_statistic(),
            # "empty_net_goal": get_default_initial_match_statistic(),
            "giveaways": get_default_initial_match_statistic(),
            "takeaways": get_default_initial_match_statistic()
        }
        match_statistic = self.get_penalties(match_statistic, original_team_names, match_page_html,
                                             match_info["method_end_match"])

        match_statistic = self.get_match_statistic_play_by_play(match_page_html_play_by_play, match_statistic,
                                                                team_image_paths, match_info["method_end_match"])
        result = {
            "match_info": match_info,
            "lineups": lineups,
            "match_statistics": match_statistic,
            "player_statistics": {
                "home": None,
                "away": None
            }
        }
        return result

    def get_match_info(self, html_match_page, current_date):

        soup = BeautifulSoup(html_match_page, 'html.parser')
        preview_frame = soup.find(class_='preview-frame__clubs')

        date = self.get_date(soup, current_date)
        score_and_method_end_match = self.get_method_end_match_and_result_score(soup)
        shootouts_score = {
            "home": None,
            "away": None
        }
        if score_and_method_end_match["method_end_match"] == "SO":
            shootouts_score = self.get_shootouts_score(soup)

        # Ищем все <div> с классом 'row' внутри preview-frame__clubs
        rows = preview_frame.find_all('div', class_='row')

        images_team = self.get_image_paths(rows[0])
        logger.info(f"image_paths: \n{pprint.pformat(images_team, width=120, indent=2)}")

        team_names, original_team_names = self.get_team_names_with_cities(rows[1], rows[2])
        logger.info(f"team_names: \n{pprint.pformat(team_names, width=120, indent=2)}")
        logger.info(f"original_team_names: \n{pprint.pformat(original_team_names, width=120, indent=2)}")
        coach_names = self.extract_coach_names(rows[3])
        logger.info(f"coach_names: \n{pprint.pformat(coach_names, width=120, indent=2)}")
        match_result = self.get_match_result(rows[4], score_and_method_end_match, shootouts_score)

        overtime_count = 1 if score_and_method_end_match["method_end_match"] == "OT" or score_and_method_end_match[
            "method_end_match"] == "SO" else 0

        match_info = {
            "home": {
                "name": team_names["home_team"],
                "image": images_team["home_team"]
            },
            "away": {
                "name": team_names["away_team"],
                "image": images_team["away_team"]
            },
            "season": {
                "years": "2024/2025",
            },
            "championship": {
                "name": "КХЛ",
                "country": "Россия"
            },
            "referee": None,
            # datetime.fromtimestamp(game_detail["D"])
            "date": date,
            "status": "completed",
            "method_end_match": score_and_method_end_match["method_end_match"],
            "overtime_count": overtime_count,
            "result": match_result,
        }
        logger.info(f"match_info: \n{pprint.pformat(match_info, width=120, indent=2)}")
        return match_info, original_team_names, coach_names

    def get_penalties(self, match_statistic, original_team_names, html_match_page, method_end_match):
        key_team_places = {
            original_team_names["home_team"]: "home",
            original_team_names["away_team"]: "away",
        }
        soup = BeautifulSoup(html_match_page, 'html.parser')
        penalties = {
            "home": [],
            "away": []
        }
        events = soup.find_all('div', class_="textBroadcast-item")
        for event in events:
            event_name = event.find("strong", class_="d-block_mob")
            if event_name:
                if event_name.text.strip() == "Удаление.":
                    team_name, penalty_time, penalty_type = self._extract_penalty_time_and_team_name_and_type_penalty(
                        event)
                    seconds_event = self._extract_seconds_event(event)
                    # Проверка, что удаление не за драку и, что удаление было на 2 или 5 минут
                    if penalty_type != "Драка" and (penalty_time == 120 or penalty_time == 300):
                        penalties[key_team_places[team_name]].append({
                            "time": seconds_event,
                            "penalty_time": penalty_time,
                        })
        logger.info(f"penalties: \n{pprint.pformat(penalties, width=120, indent=2)}")
        self.update_penalties_in_match_statistic(match_statistic, "home", penalties["home"], method_end_match)
        self.update_penalties_in_match_statistic(match_statistic, "away", penalties["away"], method_end_match)

        logger.info(f"two_minutes_penalties: \n{pprint.pformat(match_statistic["two_minutes_penalties"], width=120, indent=2)}")
        logger.info(f"two_minutes_penalties_time: \n{pprint.pformat(match_statistic["two_minutes_penalties_time"], width=120, indent=2)}")
        logger.info(f"five_minutes_penalties: \n{pprint.pformat(match_statistic["five_minutes_penalties"], width=120, indent=2)}")
        logger.info(f"five_minutes_penalties_time: \n{pprint.pformat(match_statistic["five_minutes_penalties_time"], width=120, indent=2)}")
        return match_statistic

    def _extract_penalty_time_and_team_name_and_type_penalty(self, event):
        p_tag = event.find('p', class_='textBroadcast-item__right-text')

        if not p_tag:
            return None

        text = p_tag.get_text(strip=True)
        parts = [part.strip() for part in text.split(".") if part.strip()]
        # ['Удаление', 'Северсталь', 'Командный штраф', '2 мин', 'Нарушение численного состава', 'Отбывал:99', 'Ильин Михаил']
        # ['Удаление', 'Барыс', '19', 'Эллисон Уэйд', '2 мин', 'Толчок на борт']
        if 'Командный штраф' in parts:
            index_team = 1
            index_time = 3
            index_type_penalty = 4
        else:
            index_team = 1
            index_time = 4
            index_type_penalty = -1
        # Разделяет строку "2 мин" | "5 мин" | "10 мин" | "20 мин" и переводит минуты в секунды
        seconds_penalty = int(parts[index_time].split()[0]) * 60
        # ['Удаление', 'СКА', '84', 'Выдренков Иван', '2 мин', 'Задержка соперника клюшкой']
        # Возвращает команду, время удалений в секундах и тип удаления(за что было получено)
        return parts[index_team], seconds_penalty, parts[index_type_penalty]

    def update_penalties_in_match_statistic(self, match_statistic, key_team, penalties, method_end_match):
        time_period = 20 * 60 + 1
        key_periods = {
            0: "1st_period",
            1: "2nd_period",
            2: "3rd_period",
            3: "overtime"
        }

        all_statistic_penalties = ["two_minutes_penalties", "two_minutes_penalties_time", "five_minutes_penalties",
                                   "five_minutes_penalties_time"]
        key_statistic_penalties = {
            120: ["two_minutes_penalties", "two_minutes_penalties_time"],
            300: ["five_minutes_penalties", "five_minutes_penalties_time"]
        }

        # Инициализация
        for statistic in all_statistic_penalties:
            match_statistic[statistic]["1st_period"][key_team]["result"] = 0
            match_statistic[statistic]["2nd_period"][key_team]["result"] = 0
            match_statistic[statistic]["3rd_period"][key_team]["result"] = 0
            # match_statistic[statistic]["main_time"][key_team]["result"] = 0
            # match_statistic[statistic]["result"][key_team]["result"] = 0
            if method_end_match == "OT" or method_end_match == "SO":
                match_statistic[statistic]["overtime"][key_team]["result"] = 0

        for penalty in penalties:
            for statistic in key_statistic_penalties[penalty["penalty_time"]]:
                period = key_periods[penalty["time"] // time_period]
                if "time" in statistic:
                    if penalty["time"] not in match_statistic[statistic][period][key_team]["time_to_point"]:
                        match_statistic[statistic][period][key_team]["time_to_point"][penalty["time"]] = (penalty[
                                                                                                              "penalty_time"] // 60)
                    else:
                        match_statistic[statistic][period][key_team]["time_to_point"][penalty["time"]] += (penalty[
                                                                                                               "penalty_time"] // 60)
                    match_statistic[statistic][period][key_team]["result"] += (penalty["penalty_time"] // 60)
                else:
                    if penalty["time"] not in match_statistic[statistic][period][key_team]["time_to_point"]:
                        match_statistic[statistic][period][key_team]["time_to_point"][penalty["time"]] = 1
                    else:
                        match_statistic[statistic][period][key_team]["time_to_point"][penalty["time"]] += 1
                    match_statistic[statistic][period][key_team]["result"] += 1

        for statistic in all_statistic_penalties:
            match_statistic[statistic]["main_time"][key_team]["result"] = sum_safe(
                match_statistic[statistic]["1st_period"][key_team]["result"],
                match_statistic[statistic]["2nd_period"][key_team]["result"],
                match_statistic[statistic]["3rd_period"][key_team]["result"])
            match_statistic[statistic]["main_time"][key_team]["time_to_point"] = {
                **match_statistic[statistic]["1st_period"][key_team]["time_to_point"],
                **match_statistic[statistic]["2nd_period"][key_team]["time_to_point"],
                **match_statistic[statistic]["3rd_period"][key_team]["time_to_point"]
            }
            if method_end_match == "OT" and method_end_match == "SO":
                match_statistic[statistic]["match"][key_team]["result"] += sum_safe(
                    match_statistic[statistic]["main_time"][key_team]["result"],
                    match_statistic[statistic]["overtime"][key_team]["result"])
                match_statistic[statistic]["match"][key_team]["time_to_point"] = {
                    **match_statistic[statistic]["main_time"][key_team]["time_to_point"],
                    **match_statistic[statistic]["overtime"][key_team]["time_to_point"]
                }
            else:
                match_statistic[statistic]["match"][key_team]["result"] = \
                    match_statistic[statistic]["main_time"][key_team]["result"]
                match_statistic[statistic]["match"][key_team]["time_to_point"] = \
                    match_statistic[statistic]["main_time"][key_team]["time_to_point"]

        return match_statistic

    def get_match_statistic_play_by_play(self, match_page_html_play_by_play, match_statistic, team_image_paths,
                                         method_end_match):
        team_keys = {
            team_image_paths["home"]: "home",
            team_image_paths["away"]: "away",
        }
        soup = BeautifulSoup(match_page_html_play_by_play, 'html.parser')
        play_by_play_periods_html = soup.find_all("div", class_="legend-events-wrapper")
        all_statistics = ["shots", "shots_on_goals", "shooting_percentage", "blocked_shots", "shots_off_goal",
                          "goalkeeper_saves", "goalkeeper_saves_percentage", "hits", "faceoffs_won",
                          "faceoffs_won_percentage", "giveaways", "takeaways"]

        # Инициализация
        for statistic in all_statistics:
            for key_team in ["home", "away"]:
                match_statistic[statistic]["1st_period"][key_team]["result"] = 0
                match_statistic[statistic]["2nd_period"][key_team]["result"] = 0
                match_statistic[statistic]["3rd_period"][key_team]["result"] = 0
                match_statistic[statistic]["main_time"][key_team]["result"] = 0
                match_statistic[statistic]["match"][key_team]["result"] = 0
                if method_end_match == "OT" or method_end_match == "SO":
                    match_statistic[statistic]["overtime"][key_team]["result"] = 0

        key_periods = {
            0: "1st_period",
            1: "2nd_period",
            2: "3rd_period",
            3: "overtime",
        }

        for period, period_events_html in enumerate(play_by_play_periods_html):
            if period >= 3 and (method_end_match != "OT" or method_end_match != "SO"):
                continue
            match_statistic = self.get_statistic_by_events_period(match_statistic, key_periods[period],
                                                                  period_events_html, team_keys)

        for statistic in all_statistics:
            for key_team in ["home", "away"]:
                match_statistic[statistic]["main_time"][key_team]["result"] = sum_safe(
                    match_statistic[statistic]["1st_period"][key_team]["result"],
                    match_statistic[statistic]["2nd_period"][key_team]["result"],
                    match_statistic[statistic]["3rd_period"][key_team]["result"]
                )
                if method_end_match == "OT" or method_end_match == "SO":
                    match_statistic[statistic]["main_time"][key_team]["result"] = sum_safe(
                        match_statistic[statistic]["main_time"][key_team]["result"],
                        match_statistic[statistic]["overtime"][key_team]["result"]
                    )

            logger.info(f"{statistic}: \n{pprint.pformat(match_statistic[statistic], width=120, indent=2)}")
        return match_statistic

    def get_statistic_by_events_period(self, match_statistic, period, period_events_html, team_keys):
        event_name_to_statistic_name = {
            "Бросок (В створ)": "shots_on_goals",
            "Гол": "shots_on_goals",
            "Бросок (Блокирован)": "blocked_shots",
            "Бросок (Мимо)": "shots_off_goal",
            "Вбрасывание": "faceoffs_won",
            "Силовой приём": "hits",
            "Потеря": "giveaways",
            "Перехват": "takeaways",
        }
        match_statistic = self.get_shots_by_events_period(match_statistic, period, period_events_html)

        events = period_events_html.find_all("div", class_="textBroadcast-item")
        for event in events:
            event_name_div = event.find("div", class_="game-legend-item-info-event")
            if event_name_div:
                event_name = event_name_div.find("span").text.strip()
                if event_name in event_name_to_statistic_name:
                    time_str = event.find("div", class_="game-legend-item-info-time").text.strip()
                    time = time_to_seconds(time_str)
                    image_team_path_tag = event.find("source")
                    if image_team_path_tag:
                        image_team_path = image_team_path_tag.get("srcset")
                        image_team_path = self.format_image_path(image_team_path)

                        statistic = event_name_to_statistic_name[event_name]
                        team_key = team_keys[image_team_path]
                        if time not in match_statistic[statistic][period][team_key]["time_to_point"]:
                            match_statistic[statistic][period][team_key]["time_to_point"][time] = 1
                        else:
                            match_statistic[statistic][period][team_key]["time_to_point"][time] += 1
                        match_statistic[statistic][period][team_key]["result"] += 1
        return match_statistic

    def get_shots_by_events_period(self, match_statistic, period, period_events_html):
        statistic_by_period_raw_text = period_events_html.find("div", class_="textBroadcast-item").text.strip()
        statistic_by_period_text = re.sub(r'\s+', ' ', statistic_by_period_raw_text).strip()
        # Регулярное выражение для извлечения бросков
        shots = re.search(r'Броски: (\d+)-(\d+)', statistic_by_period_text)

        if shots:
            shots_home, shots_away = int(shots.group(1)), int(shots.group(2))
            logger.info(f"{period} shots: home: {shots_home}, away: {shots_away}")

            match_statistic["shots"][period]["home"]["result"] = shots_home
            match_statistic["shots"][period]["away"]["result"] = shots_away
        else:
            logger.warning(f"{period}: Нет информации о бросках")

        return match_statistic

    def _extract_seconds_event(self, event):
        time_str = event.find("time", class_="textBroadcast-item__left-time").text
        seconds = time_to_seconds(time_str)
        return seconds

    def get_method_end_match_and_result_score(self, html_match_page):
        translate_method_end_match = {
            "ОТ": "OT",
            "Б": "SO"
        }
        # Ищем элемент с классом preview-frame__center-score
        html_score_info = html_match_page.find('p', class_='preview-frame__center-score')
        logger.info(f"html_score_info: \n{html_score_info.prettify()}")

        # Извлекаем данные
        home_score = html_score_info.contents[0].strip()  # Первый текст (2)
        away_score = html_score_info.find('b').text.strip()  # Текст внутри <b> (3)
        logger.info(f"Результат матча home_score: {home_score}, away_score: {away_score}")
        method_end_match = html_score_info.find('span', class_='preview-frame__ots')  # Текст внутри <span> (Б)
        logger.info(f"method_end_match: {method_end_match}")
        if method_end_match is not None:
            method_end_match = translate_method_end_match[method_end_match.text.strip()]
        else:
            method_end_match = "MT"

        return {
            "home": int(home_score),
            "away": int(away_score),
            "method_end_match": method_end_match,
        }

    @staticmethod
    def get_shootouts_score(html_match_page):

        logger.info("Получение счета послематчевых бросков")
        shootouts = {
            "home": None,
            "away": None
        }
        events = html_match_page.find_all('div', class_="textBroadcast-item")
        for event in events:
            event_name = event.find('strong', 'd-block_mob')
            if event_name:
                event_name = event_name.text
                if event_name == "Послематчевый буллит:":
                    score_num = event.find('p', class_='score-re__num')

                    # Извлекаем все <b> внутри этого элемента
                    scores = score_num.find_all('b')
                    shootouts["home"] = int(scores[0].text.strip())
                    shootouts["away"] = int(scores[1].text.strip())

                    return shootouts

        logger.info(f"shootouts: \n{pprint.pformat(shootouts, width=120, indent=2)}")
        return shootouts

    def get_date(self, html_match_page, current_date):
        html_date = html_match_page.find("div", class_="card-infos__item")
        logger.info(f"html_date: \n{html_date.prettify()}")
        date_text = html_date.find("div", class_="card-infos__item-info").text.strip()
        logger.info(f"date_text: {date_text}")

        # Разделяем дату и время
        time_part = date_text.split(", ")[-1].strip()
        logger.info(f"time_part: {time_part}")
        date = self.format_date(current_date, time_part)
        logger.info(f"date: {date}")
        return date

    def get_image_paths(self, soup):
        """
        Извлекает пути к изображениям домашних и гостевых команд из объекта BeautifulSoup.

        :param soup: Объект BeautifulSoup с HTML данными команды
        :return: Словарь с путями к изображениям (home_team, away_team)
        """
        if not isinstance(soup, (BeautifulSoup, Tag)):
            raise TypeError(f"Ожидается объект BeautifulSoup или Tag, получен: {type(soup)}")

        # Извлекаем пути к изображениям для home_team и away_team
        return {
            "home_team": self._extract_image_src(soup, 'col-left', 'preview-frame__club-img'),
            "away_team": self._extract_image_src(soup, 'col-right', 'preview-frame__club-img')
        }

    def _extract_image_src(self, soup, column_class, img_class):
        img_tag = soup.find('div', class_=column_class).find('img', class_=img_class)
        img_src = img_tag.get("src")

        # такой return, потому что img_src = "////www.khl.ru/images/teams/ru/1288/7.png"
        return self.format_image_path(img_src)

    @staticmethod
    def format_image_path(img_path):
        if img_path.startswith("////"):
            return f"https:{img_path[2:]}"
        if img_path.startswith("//"):
            return f"https:{img_path}"

    def get_team_names_with_cities(self, team_names_row, team_cities_row):
        team_names = self.extract_team_names(team_names_row)
        team_cities = self.extract_team_cities(team_cities_row)

        original_team_names = {
            "home_team": team_names["home_team"],
            "away_team": team_names["away_team"]
        }

        team_names["home_team"] = self.add_city_to_team_name(team_names["home_team"], team_cities['home_team'])
        team_names["away_team"] = self.add_city_to_team_name(team_names["away_team"], team_cities['away_team'])

        return team_names, original_team_names

    def get_coach_names(self, row):
        """Получает имена тренеров и меняет местами имя и фамилию."""
        coach_names = self.extract_coach_names(row)

        # Меняем местами имя и фамилию для home_team и away_team
        coach_names["home_team"] = self._reverse_name_format(coach_names["home_team"])
        coach_names["away_team"] = self._reverse_name_format(coach_names["away_team"])

        return coach_names

    @staticmethod
    def _reverse_name_format(name):
        """
        Меняет местами имя и фамилию в строке с учетом возможных ошибок.

        :param name: Строка с именем и фамилией
        :return: Строка с переставленными местами фамилией и именем или оригинал в случае ошибки
        """
        try:
            # Проверка типа данных
            if not isinstance(name, str):
                raise TypeError(f"Ожидается строка, получен: {type(name)}")

            # Удаление лишних пробелов и разделение строки на части
            parts = name.strip().split()

            # Проверка количества частей
            if len(parts) != 2:
                raise ValueError(f"Неверный формат имени: '{name}'. Ожидается 'Фамилия Имя'.")

            # Перестановка фамилии и имени
            return f"{parts[1]} {parts[0]}"
        except (TypeError, ValueError) as e:
            # Логирование ошибки или возврат дефолтного значения
            print(f"Ошибка при обработке имени: {e}")
            return name  # Возвращаем оригинальную строку в случае ошибки

    def get_match_result(self, row, score_and_method_end_match, shootouts_score):

        home_team_column = row.find('div', class_="col-left")
        away_team_column = row.find('div', class_="col-right")

        goals_by_time = {
            "home_team": self._extract_times_with_seconds(home_team_column, "resp-table-row"),
            "away_team": self._extract_times_with_seconds(away_team_column, "resp-table-row")
        }
        match_result = get_default_initial_match_result()
        match_result = self.get_match_result_dictionary(match_result, goals_by_time["home_team"], "home",
                                                        shootouts_score["home"], score_and_method_end_match["home"])
        match_result = self.get_match_result_dictionary(match_result, goals_by_time["away_team"], "away",
                                                        shootouts_score["away"], score_and_method_end_match["away"])
        return match_result

    def get_match_result_dictionary(self, match_result, list_points, key_team, team_score_shootouts, team_score_result):
        twenty_minutes_in_seconds = 20 * 60
        key_periods = {
            0: "1st_period",
            1: "2nd_period",
            2: "3rd_period",
            3: "overtime"
        }

        match_result["1st_period"][key_team]["result"] = 0
        match_result["2nd_period"][key_team]["result"] = 0
        match_result["3rd_period"][key_team]["result"] = 0

        for point in list_points:
            # Если изменение произошло изменение произошло на 65:00, то не учитываем
            if point != 20 * 60 + 5 * 60:
                key_period = key_periods[point // twenty_minutes_in_seconds]
                match_result[key_period][key_team]["time_to_point"][point] = 1
                if match_result[key_period][key_team]["result"] is None:
                    match_result[key_period][key_team]["result"] = 1
                else:
                    match_result[key_period][key_team]["result"] += 1

        match_result["shootouts"][key_team]["result"] = team_score_shootouts
        match_result["result"][key_team]["result"] = team_score_result

        match_result["main_time"][key_team]["result"] = sum_safe(match_result["1st_period"][key_team]["result"],
                                                                 match_result["2nd_period"][key_team]["result"],
                                                                 match_result["3rd_period"][key_team]["result"]
                                                                 )
        return match_result

    def extract_coach_names(self, row):
        return self._extract_p_tag_by_class_name(row, "preview-frame__club-nameTrainer")

    def extract_team_names(self, row):
        """Извлекает названия домашних и гостевых команд из HTML строки."""
        return self._extract_p_tag_by_class_name(row, 'preview-frame__club-nameClub')

    def extract_team_cities(self, row):
        """Извлекает города домашних и гостевых команд из HTML строки."""
        return self._extract_p_tag_by_class_name(row, 'preview-frame__club-local')

    def _extract_p_tag_by_class_name(self, soup, class_name):
        """Универсальный метод для извлечения информации по заданному классу из объекта BeautifulSoup."""
        if not isinstance(soup, (BeautifulSoup, Tag)):
            raise TypeError(f"Ожидается объект BeautifulSoup или Tag, получен: {type(soup)}")

        # Извлекаем информацию из колонок 'col-left' и 'col-right'
        return {
            "home_team": self._extract_text_from_column(soup, 'col-left', class_name),
            "away_team": self._extract_text_from_column(soup, 'col-right', class_name)
        }

    @staticmethod
    def _extract_text_from_column(soup, column_class, target_class):
        """Извлекает текст из заданного столбца и класса."""
        column = soup.find('div', class_=column_class)
        if column:
            p_tag = column.find('p', class_=target_class)
            if p_tag:
                return p_tag.get_text(strip=True).strip()
        return None

    @staticmethod
    def _extract_times_with_seconds(soup, class_name):
        times_in_seconds = []
        rows = soup.find_all("div", class_=class_name)

        if not rows:
            return []

        for row in rows:
            try:
                time_cell = row.find_all("div", class_="table-body-cell")[-1]
                if not time_cell:
                    raise ValueError("Не найдено поле с временем в строке")

                time_str = time_cell.get_text(strip=True)
                total_seconds = time_to_seconds(time_str)
                times_in_seconds.append(total_seconds)

            except Exception as e:
                raise ValueError(f"Ошибка при обработке строки: {e}")

        return times_in_seconds


if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    url_calendar = "https://www.khl.ru/calendar/"

    season_id = "1288"
    parser = ParserResultKHL(headers, url_calendar, season_id)

    # Пример вызова с датами
    # parser.parsing(start_date="2024-09-06", end_date="2025-01-05")
    # parser.parsing(start_date="2024-09-03", end_date="2024-09-30")
    parser.parsing(start_date="2024-09-03", end_date="2025-02-16")
    # parser.parsing(start_date="2025-01-31", end_date="2025-02-02")
