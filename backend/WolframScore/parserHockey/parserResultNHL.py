import os

from parserHockey.parserNHL import ParserNHL

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

import django

django.setup()

from datetime import datetime

import pytz

from parserHockey.addMatchesToDB import AddMatchesToDBHockey
from parserHockey.applyFiltersUtils import sum_safe
from parserHockey.dictionary_models import models_hockey
from parserHockey.parserSharedUtils import get_default_initial_match_result, get_default_initial_match_statistic
from parserHockey.parserHockeyUtils import time_to_seconds
from parsing.requests import get_request


class ParserResultNHL(ParserNHL):

    def __init__(self, _calendar_url, _play_by_play_url, _game_center_url, _headers):
        super().__init__(_calendar_url=_calendar_url, _play_by_play_url=_play_by_play_url,
                         _game_center_url=_game_center_url, _headers=_headers)

    def parsing(self, start_date, end_date):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        current_date = start_date

        matches = []
        while current_date <= end_date:
            print(f"Обрабатываю дату: {current_date}")
            next_current_date, matches_id = self.get_next_date_and_link_games(current_date, end_date)

            matches_by_week = self.get_matches_data_by_week(matches_id)
            matches.extend(matches_by_week)

            current_date = next_current_date

        add_matches_obj = AddMatchesToDBHockey(
            _models=models_hockey, _dictionary_championships_with_matches={"НХЛ": matches})
        add_matches_obj.add_championships_with_matches_to_db()

    def get_next_date_and_link_games(self, current_date, end_date):

        date_to_request = datetime.strftime(current_date, "%Y-%m-%d")
        response_by_date = self.get_json_response_by_date(date_to_request)
        next_current_date = response_by_date.get("nextStartDate")
        matches_id = []
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
                if game_type != 2 or game_state != "OFF":
                    continue
                match_id = game.get("id")
                matches_id.append(match_id)

        return next_current_date, matches_id

    def get_match_data(self, match_id):
        response_play_by_play = self.get_json_play_by_play(match_id)
        match_info = self.get_match_info(response_play_by_play)
        match_statistic = self.get_match_statistic(response_play_by_play, match_info["method_end_match"])
        coaches = self.get_coaches(match_id)
        lineups = {
            "home": None,
            "away": None,
            "coach_home": {
                "name": coaches["home"]["name"],
                "start_date": match_info["date"].date()
            },
            "coach_away": {
                "name": coaches["away"]["name"],
                "start_date": match_info["date"].date()
            }
        }
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

    def get_json_play_by_play(self, match_id):
        url = f"{self._play_by_play_url}{match_id}/play-by-play"
        response = get_request(url=url, params=None, headers=self._headers)
        return response

    def get_match_info(self, response_play_by_play):
        date = self.get_date(response_play_by_play)
        teams = self.get_teams_info(response_play_by_play)
        season = self.get_season(response_play_by_play)
        game_type = response_play_by_play.get("gameType")

        print(teams["home"]["name"], teams["away"]["name"], date)
        method_end_match, match_result = self.get_method_end_match_and_result(response_play_by_play)

        match_info = {
            "home": {
                "name": teams["home"]["name"],
                "image": teams["home"]["image"]
            },
            "away": {
                "name": teams["away"]["name"],
                "image": teams["away"]["image"]
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
            "status": "completed",
            "method_end_match": method_end_match,
            "overtime_count": 1 if method_end_match == "OT" or method_end_match == "SO" else 0,
            "result": match_result,
        }

        return match_info

    def get_match_statistic(self, response_play_by_play, method_end_match):
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

        event_name_to_statistic_name = {
            "goal": "shots_on_goals",
            "shot-on-goal": "shots_on_goals",
            "blocked-shot": "blocked_shots",
            "missed-shot": "shots_off_goal",
            "hit": "hits",
            "faceoff": "faceoffs_won",
            "giveaway": "giveaways",
            "takeaway": "takeaways",
        }

        all_periods = ["1st_period", "2nd_period", "3rd_period", "main_time", "match"]
        if method_end_match == "OT" or method_end_match == "SO":
            all_periods.append("overtime")

        for statistic in match_statistic:
            for period in all_periods:
                for team in ["home", "away"]:
                    match_statistic[statistic][period][team]["result"] = 0

        key_periods = {
            1: "1st_period",
            2: "2nd_period",
            3: "3rd_period",
        }

        id_home_team = response_play_by_play.get("homeTeam").get("id")
        id_away_team = response_play_by_play.get("awayTeam").get("id")
        translate_id_team_to_key = {
            id_home_team: "home",
            id_away_team: "away"
        }

        events_match = response_play_by_play.get("plays")
        for event in events_match:
            event_name = event.get("typeDescKey")

            if event_name in event_name_to_statistic_name or event_name == "penalty":
                id_team = event.get("details").get("eventOwnerTeamId")
                key_team = translate_id_team_to_key[id_team]
                period_number = event.get("periodDescriptor").get("number")
                period_type = event.get("periodDescriptor").get("periodType")
                time_period = event.get("timeInPeriod")
                time_in_seconds = time_to_seconds(time_period)
                if period_number >= 2:
                    time_in_seconds += (period_number - 1) * 20 * 60

                if period_type == "REG":
                    period = key_periods[period_number]
                elif period_type == "OT":
                    period = "overtime"
                else:
                    continue

                if event_name == "penalty":
                    match_statistic = self.update_penalty_match_statistic(match_statistic, event, period, key_team,
                                                                          time_in_seconds)
                    continue

                statistic_name = event_name_to_statistic_name[event_name]

                if time_in_seconds not in match_statistic[statistic_name][period][key_team]["time_to_point"]:
                    match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] = 1
                else:
                    match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] += 1
                match_statistic[statistic_name][period][key_team]["result"] += 1

        for statistic in match_statistic:
            for team in ["home", "away"]:
                match_statistic[statistic]["main_time"][team]["time_to_point"] = {
                    **match_statistic[statistic]["1st_period"][team]["time_to_point"],
                    **match_statistic[statistic]["2nd_period"][team]["time_to_point"],
                    **match_statistic[statistic]["3rd_period"][team]["time_to_point"],
                }
                match_statistic[statistic]["main_time"][team]["result"] = (
                        match_statistic[statistic]["1st_period"][team]["result"] +
                        match_statistic[statistic]["2nd_period"][team]["result"] +
                        match_statistic[statistic]["3rd_period"][team]["result"]
                )

                if method_end_match == "OT" or method_end_match == "SO":
                    match_statistic[statistic]["match"][team]["time_to_point"] = {
                        **match_statistic[statistic]["main_time"][team]["time_to_point"],
                        **match_statistic[statistic]["overtime"][team]["time_to_point"]
                    }
                    match_statistic[statistic]["match"][team]["result"] = (
                            match_statistic[statistic]["main_time"][team]["result"] +
                            match_statistic[statistic]["overtime"][team]["result"]
                    )

        # for statistic in match_statistic:
        #     print(statistic)
        #     print(match_statistic[statistic])

        match_statistic = self.update_shots_match_statistic(match_statistic, method_end_match)
        return match_statistic

    def update_penalty_match_statistic(self, match_statistic, event, period, key_team, time_in_seconds):

        translate_time_to_name_statistics = {
            120: ["two_minutes_penalties", "two_minutes_penalties_time"],
            # Случай, когда удаление 4 мин, в нашем случае 2 + 2
            240: ["two_minutes_penalties", "two_minutes_penalties_time"],
            300: ["five_minutes_penalties", "five_minutes_penalties_time"]
        }

        penalty_time = event.get("details").get("duration")
        penalty_seconds = penalty_time * 60
        penalty_type = event.get("details").get("descKey")

        if penalty_type == "fighting" or penalty_seconds not in translate_time_to_name_statistics:
            return match_statistic

        for statistic_name in translate_time_to_name_statistics[penalty_seconds]:
            if "time" in statistic_name:
                if time_in_seconds not in match_statistic[statistic_name][period][key_team]["time_to_point"]:
                    if penalty_seconds == 240:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] = 4
                        match_statistic[statistic_name][period][key_team]["result"] += 4
                    else:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][
                            time_in_seconds] = penalty_time
                        match_statistic[statistic_name][period][key_team]["result"] += penalty_time
                else:
                    if penalty_seconds == 240:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] += 4
                        match_statistic[statistic_name][period][key_team]["result"] += 4
                    else:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][
                            time_in_seconds] += penalty_time
                        match_statistic[statistic_name][period][key_team]["result"] += penalty_time
            else:
                if time_in_seconds not in match_statistic[statistic_name][period][key_team]["time_to_point"]:
                    if penalty_seconds == 240:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] = 2
                        match_statistic[statistic_name][period][key_team]["result"] += 2
                    else:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] = 1
                        match_statistic[statistic_name][period][key_team]["result"] += 1
                else:
                    if penalty_seconds == 240:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] += 2
                        match_statistic[statistic_name][period][key_team]["result"] += 2
                    else:
                        match_statistic[statistic_name][period][key_team]["time_to_point"][time_in_seconds] += 1
                        match_statistic[statistic_name][period][key_team]["result"] += 1

        return match_statistic

    def update_shots_match_statistic(self, match_statistic, method_end_match):

        all_periods = ["1st_period", "2nd_period", "3rd_period"]
        if method_end_match == "OT" or method_end_match == "SO":
            all_periods.append("overtime")

        reverse_key_team = {
            "home": "away",
            "away": "home"
        }
        for period in all_periods:
            for key_team in ["home", "away"]:
                match_statistic["shots"][period][key_team]["result"] = sum_safe(
                    match_statistic["shots_on_goals"][period][key_team]["result"],
                    match_statistic["shots_off_goal"][period][key_team]["result"],
                    match_statistic["blocked_shots"][period][reverse_key_team[key_team]]["result"]
                )

        for key_team in ["home", "away"]:
            match_statistic["shots"]["main_time"][key_team]["result"] = sum_safe(
                match_statistic["shots"]["1st_period"][key_team]["result"],
                match_statistic["shots"]["2nd_period"][key_team]["result"],
                match_statistic["shots"]["3rd_period"][key_team]["result"]
            )

        if method_end_match == "OT" or method_end_match == "SO":
            for key_team in ["home", "away"]:
                match_statistic["shots"]["match"][key_team]["result"] = (
                        match_statistic["shots"]["main_time"][key_team]["result"] +
                        match_statistic["shots"]["overtime"][key_team]["result"]
                )
        else:
            for key_team in ["home", "away"]:
                match_statistic["shots"]["match"][key_team]["result"] = (
                    match_statistic["shots"]["main_time"][key_team]["result"]
                )

        return match_statistic

    def get_method_end_match_and_result(self, response_play_by_play):
        translate_method_end_match = {
            "REG": "MT",
            "OT": "OT",
            "SO": "SO"
        }
        method_end_match = translate_method_end_match[response_play_by_play.get("gameOutcome").get("lastPeriodType")]
        events_match = response_play_by_play.get("plays")
        result = get_default_initial_match_result()
        all_periods = ["1st_period", "2nd_period", "3rd_period"]
        for period in all_periods:
            for team in ["home", "away"]:
                result[period][team]["result"] = 0

        if method_end_match == "OT":
            for team in ["home", "away"]:
                result["overtime"][team]["result"] = 0

        if method_end_match == "SO":
            for period in ["overtime", "shootouts"]:
                for team in ["home", "away"]:
                    result[period][team]["result"] = 0

        key_periods = {
            1: "1st_period",
            2: "2nd_period",
            3: "3rd_period",
        }

        id_home_team = response_play_by_play.get("homeTeam").get("id")
        home_team_result = response_play_by_play.get("homeTeam").get("score")
        id_away_team = response_play_by_play.get("awayTeam").get("id")
        away_team_result = response_play_by_play.get("awayTeam").get("score")
        translate_id_team_to_key = {
            id_home_team: "home",
            id_away_team: "away"
        }
        for event in events_match:
            if event.get("typeDescKey") != "goal":
                continue
            event_time = event.get("timeInPeriod")
            time_in_seconds = time_to_seconds(event_time)
            number_period = event.get("periodDescriptor").get("number")
            period_type = event.get("periodDescriptor").get("periodType")
            owner_event_team_id = event.get("details").get("eventOwnerTeamId")
            key_team = translate_id_team_to_key[owner_event_team_id]

            if period_type == "REG":
                period = key_periods[number_period]
                # Каждый период имеет время от 0 до 20, поэтому необходимо перевести в отрезок от 0 до 60
                if number_period >= 2:
                    time_in_seconds += (number_period - 1) * 20 * 60

            elif period_type == "OT":
                period = "overtime"
            else:
                period = "shootouts"

            if period != "shootouts":
                result[period][key_team]["time_to_point"][time_in_seconds] = 1
            result[period][key_team]["result"] += 1

        result["main_time"]["home"]["result"] = (result["1st_period"]["home"]["result"] +
                                                 result["2nd_period"]["home"]["result"] +
                                                 result["3rd_period"]["home"]["result"])

        result["main_time"]["away"]["result"] = (result["1st_period"]["away"]["result"] +
                                                 result["2nd_period"]["away"]["result"] +
                                                 result["3rd_period"]["away"]["result"])

        result["result"]["home"]["result"] = home_team_result
        result["result"]["away"]["result"] = away_team_result

        return method_end_match, result

    def get_coaches(self, match_id):
        coaches = {
            "home": {},
            "away": {}
        }

        response_right_rail = self.get_json_right_rail(match_id)
        coaches["home"]["name"] = response_right_rail.get("gameInfo").get("homeTeam").get("headCoach").get("default")
        coaches["away"]["name"] = response_right_rail.get("gameInfo").get("awayTeam").get("headCoach").get("default")

        return coaches

    def get_json_right_rail(self, match_id):
        url = f"{self._game_center_url}{match_id}/right-rail"
        response = get_request(url=url, params=None, headers=self._headers)
        return response


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
    Parser = ParserResultNHL(_calendar_url=calendar_url, _play_by_play_url=play_by_play_url,
                             _game_center_url=game_center_url, _headers=headers)
    # Parser.parsing(start_date="2024-09-30", end_date="2025-02-02")
    # Parser.parsing(start_date="2024-09-30", end_date="2025-01-03")
    # Parser.parsing(start_date="2024-02-10", end_date="2025-02-22")
    Parser.parsing(start_date="2025-03-24", end_date="2025-03-25")
