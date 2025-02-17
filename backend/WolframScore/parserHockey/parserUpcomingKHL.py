import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

import django

django.setup()


from datetime import timedelta, datetime

import pytz
from bs4 import BeautifulSoup

from parserHockey.addMatchesToDB import AddMatchesToDBHockey
from parserHockey.dictionary_models import models_hockey
from parserHockey.parserKHL import ParserKHL


class ParserUpcomingKHL(ParserKHL):

    def parsing(self, start_date, end_date):
        # Преобразуем строки в объекты даты, если это нужно
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Ваша логика обхода по датам
        current_date = start_date
        matches = []
        while current_date <= end_date:
            print(f"Обрабатываю дату: {current_date}")

            html_page_schedule_matches = self.fetch_html_schedule_by_date(date=current_date)
            matches_by_date = self.get_matches_by_date(html_page_schedule_matches, current_date)

            current_date += timedelta(days=1)

            matches.extend(matches_by_date)

        add_matches_obj = AddMatchesToDBHockey(
            _models=models_hockey, _dictionary_championships_with_matches={"КХЛ": matches})
        add_matches_obj.add_championships_with_matches_to_db()

    def get_matches_by_date(self, html_page_schedule_matches, current_date):
        matches = []
        soup = BeautifulSoup(html_page_schedule_matches, 'html.parser')
        matches_html = soup.find_all("div", class_=["card-game", "card-game--calendar"])

        for match_html in matches_html:
            match_data = self.get_match_data(match_html, current_date)
            matches.append(match_data)
        return matches

    def get_match_data(self, match_html, current_date):
        home_team = match_html.find("a", class_="card-game__club card-game__club_left")
        home_team_name = home_team.find("p", class_="card-game__club-name").text.strip()
        home_team_city = home_team.find("p", class_="card-game__club-local").text.strip()
        home_team_name = self.add_city_to_team_name(home_team_name, home_team_city)

        away_team = match_html.find("a", class_="card-game__club card-game__club_right")
        away_team_name = away_team.find("p", class_="card-game__club-name").text.strip()
        away_team_city = away_team.find("p", class_="card-game__club-local").text.strip()
        away_team_name = self.add_city_to_team_name(away_team_name, away_team_city)

        time = self.get_time_match(match_html)
        match_date = self.format_date(current_date, time)

        lineups = {
            "home": None,
            "away": None,
            "coach_home": {},
            "coach_away": {},
        }

        prepared_match = {
            "match_info": {
                "home": {
                    "name": home_team_name,
                    "image": None
                },
                "away": {
                    "name": away_team_name,
                    "image": None
                },
                "championship": {
                    "name": "КХЛ"
                },
                "season": {
                    "years": "2024/2025",
                },
                # Подумать, как правильно записать None, чтобы не было проблем с добавлением в бд
                "referee": None,
                "date": match_date,
                # "date": datetime.fromtimestamp(match['S']).isoformat(),
                "odds": None,
                "status": "not_started",
                "method_end_match": None,
                "overtime_count": None,
                "result": None
            },
            "lineups": lineups,
            "player_statistics": {
                "home": None,
                "away": None
            },
            "match_statistics": None
        }

        return prepared_match

    def get_time_match(self, match_html):
        time_element = match_html.find("p", class_="card-game__center-time")
        if time_element:
            time = time_element.text.strip().split('мск')[0].strip()
        else:
            print("Не удалось найти элемент с временем.")
            return None
        return time


if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    url_calendar = "https://www.khl.ru/calendar/"

    season_id = "1288"
    Parser = ParserUpcomingKHL(headers, url_calendar, season_id)

    # Пример вызова с датами
    # Parser.parsing(start_date="2025-01-03", end_date="2025-01-10")
    Parser.parsing(start_date="2025-02-17", end_date="2025-03-01")
