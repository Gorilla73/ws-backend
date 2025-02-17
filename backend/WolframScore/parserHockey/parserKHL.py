import logging
from datetime import datetime
from bs4 import BeautifulSoup
import pytz

from parsing.requests import fetch_html

TEAMS_REQUIRING_CITY_NAMES = ["Динамо М", "Динамо Мн"]


class ParserKHL:

    def __init__(self, _header, _url_calendar, _season_id):
        self._teams_black_list = ["Див. Боброва", "Див. Тарасова", "Див. Чернышова", "Див. Харламова"]
        self._url_calendar = _url_calendar
        self._headers = _header
        self._season_id = _season_id

        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_html_schedule_by_date(self, date):
        params = {
            "day": date.day,
        }
        month_str = str(date.month).zfill(2)
        url = self._url_calendar + f"{self._season_id}/{month_str}/"
        self.logger.info(f"Получен url для получения html с расписанием: url: {url}, params: {params}")

        # Обработать выход
        max_retries = 0
        while True and max_retries < 5:
            response_status, response_html = fetch_html(url=url, headers=self._headers, params=params, logger=self.logger)
            print(f"Данные были корректно загружены", self.check_fetch_html_schedule_by_date(response_html))
            if self.check_fetch_html_schedule_by_date(response_html):
                return response_html
            max_retries += 1

    def check_fetch_html_schedule_by_date(self, html_schedule):
        # False - html содержит loader - данные не загружены
        # True - html не содержит loader - данные загружены
        soup = BeautifulSoup(html_schedule, "html.parser")
        loader = soup.find("div", {"id": "id_spinner"})
        if loader is None:
            return True
        return False

    def format_date(self, date, time):
        local_datetime_str = f"{date} {time}"
        local_timezone = pytz.timezone("Europe/Moscow")
        local_datetime = datetime.strptime(local_datetime_str, "%Y-%m-%d %H:%M")
        local_datetime = local_timezone.localize(local_datetime)

        return local_datetime

    @staticmethod
    def add_city_to_team_name(team_name, team_city):
        if team_name in TEAMS_REQUIRING_CITY_NAMES:
            team_name = f"{team_name.split()[0]} {team_city}"
        return team_name




