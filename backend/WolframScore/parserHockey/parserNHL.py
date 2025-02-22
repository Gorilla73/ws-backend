from datetime import datetime

import pytz

from parsing.requests import get_request


class ParserNHL:

    def __init__(self, _calendar_url=None, _play_by_play_url=None, _game_center_url=None, _headers=None):
        self._calendar_url = _calendar_url
        self._play_by_play_url = _play_by_play_url
        self._game_center_url = _game_center_url

        self._headers = _headers

        self._game_type_to_championship_name = {
            2: "НХЛ",

        }

    def get_json_response_by_date(self, date):
        url = self._calendar_url + date
        response = get_request(url=url, params=None, headers=self._headers)
        return response

    def get_date(self, response_play_by_play):
        date_utc = response_play_by_play.get("startTimeUTC")
        date = self.format_date(date_utc)
        return date

    def format_date(self, date_str):
        # Преобразуем строку в datetime, указывая, что время в UTC
        utc_datetime = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)

        # Переводим время в московскую временную зону
        moscow_timezone = pytz.timezone("Europe/Moscow")
        moscow_datetime = utc_datetime.astimezone(moscow_timezone)

        return moscow_datetime

    def get_season(self, response_play_by_play):
        season = str(response_play_by_play.get("season"))
        format_season = f"{season[:4]}/{season[4:]}"
        return format_season

    def get_teams_info(self, response_play_by_play):
        teams = {
            "home": {},
            "away": {}
        }

        place_home_team = response_play_by_play.get("homeTeam").get("placeName").get("default")
        name_home_team = response_play_by_play.get("homeTeam").get("commonName").get("default")

        # teams["home"]["name"] = f"{place_home_team} {name_home_team}"
        teams["home"]["name"] = name_home_team
        teams["home"]["image"] = response_play_by_play.get("homeTeam").get("logo")

        place_away_team = response_play_by_play.get("awayTeam").get("placeName").get("default")
        name_away_team = response_play_by_play.get("awayTeam").get("commonName").get("default")
        # teams["away"]["name"] = f"{place_away_team} {name_away_team}"
        teams["away"]["name"] = name_away_team
        teams["away"]["image"] = response_play_by_play.get("awayTeam").get("logo")

        return teams
