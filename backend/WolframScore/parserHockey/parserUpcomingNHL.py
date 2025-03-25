import os

from parserHockey.parserNHL import ParserNHL

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

import django

django.setup()

from datetime import datetime

import pytz

from parserHockey.addMatchesToDB import AddMatchesToDBHockey
from parserHockey.dictionary_models import models_hockey
from parsing.requests import get_request


class ParserUpcomingNHL(ParserNHL):

    def __init__(self, _calendar_url, _headers):
        super().__init__(_calendar_url=_calendar_url, _headers=_headers)

    def parsing(self, start_date, end_date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        current_date = start_date

        matches_data = []
        while current_date <= end_date:
            print(f"Обрабатываю дату: {current_date}")
            next_current_date, matches = self.get_next_date_and_games(current_date, end_date)

            matches_by_week = self.get_matches_data_by_week(matches)
            matches_data.extend(matches_by_week)

            current_date = next_current_date

        add_matches_obj = AddMatchesToDBHockey(
            _models=models_hockey, _dictionary_championships_with_matches={"НХЛ": matches_data})
        add_matches_obj.add_championships_with_matches_to_db()

    def get_next_date_and_games(self, current_date, end_date):

        date_to_request = datetime.strftime(current_date, "%Y-%m-%d")
        response_by_date = self.get_json_response_by_date(date_to_request)
        next_current_date = response_by_date.get("nextStartDate")
        matches = []
        # Обработать, если нет "nextStartDate"
        next_current_date = datetime.strptime(next_current_date, "%Y-%m-%d").date()
        games_week = response_by_date.get("gameWeek")
        for info_day in games_week:
            date_by_day = info_day.get("date")
            date_by_day = datetime.strptime(date_by_day, "%Y-%m-%d").date()
            if date_by_day > end_date:
                break

            games_by_day = info_day.get("games")
            for game in games_by_day:
                game_type = game.get("gameType")
                game_state = game.get("gameState")
                if game_type != 2 or game_state != "FUT":
                    continue
                matches.append(game)

        return next_current_date, matches

    def get_match_data(self, game):
        match_info = self.get_match_info(game)
        lineups = {
            "home": None,
            "away": None,
            "coach_home": {},
            "coach_away": {},
        }
        result = {
            "match_info": match_info,
            "lineups": lineups,
            "match_statistics": None,
            "player_statistics": {
                "home": None,
                "away": None
            }
        }
        return result

    def get_match_info(self, response_play_by_play):
        date = self.get_date(response_play_by_play)
        teams = self.get_teams_info(response_play_by_play)
        season = self.get_season(response_play_by_play)
        game_type = response_play_by_play.get("gameType")

        print(teams["home"]["name"], teams["away"]["name"], date)

        match_info = {
            "home": {
                "name": teams["home"]["name"],
                "image": None
            },
            "away": {
                "name": teams["away"]["name"],
                "image": None
            },
            "season": {
                "years": season,
            },
            "championship": {
                "name": self._game_type_to_championship_name[game_type],
                "country": "США"
            },
            "referee": None,
            # datetime.fromtimestamp(game_detail["D"])
            "date": date,
            "status": "not_started",
            "method_end_match": None,
            "overtime_count": None,
            "result": None
        }

        return match_info


if __name__ == "__main__":
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "if-none-match": 'W/"6777b895--gzip"',
        "origin": "https://www.nhl.com",
        "referer": "https://www.nhl.com/",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    calendar_url = "https://api-web.nhle.com/v1/schedule/"
    play_by_play_url = "https://api-web.nhle.com/v1/gamecenter/"
    game_center_url = "https://api-web.nhle.com/v1/gamecenter/"
    Parser = ParserUpcomingNHL(_calendar_url=calendar_url, _headers=headers)
    # Parser.parsing(start_date="2024-09-30", end_date="2024-10-12")
    Parser.parsing(start_date="2025-03-12", end_date="2025-03-16")
    # Parser.parsing(start_date="2024-09-30", end_date="2024-10-03")
