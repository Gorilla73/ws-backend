from parserHockey.apiUrls import TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE


def sum_safe(*args):
    if None in args:
        return None
    return sum(arg for arg in args if isinstance(arg, (int, float)))


def format_numeric_value(value):
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, int):
        return value
    raise ValueError("Unsupported type. Expected float, int, or None.")


def get_list_matches(matches):
    result = []
    for match in matches:
        # print(match)
        result_score = {
            "homeTeam": match.result["result"]["home"]["result"] if match.result is not None else None,
            "awayTeam": match.result["result"]["away"]["result"] if match.result is not None else None
        }
        # print(match.home_team.name, "-", match.away_team.name, match.date.strftime("%d.%m.%Y"), match.season)
        match = {
            "id": match.pk,
            "championship": {
                "id": match.championship.pk,
                "name": match.championship.name,
            },
            "season": match.season.season if match.season is not None else None,
            "date": match.date.strftime("%d.%m.%Y"),
            "homeTeam": {
                "id": match.home_team.pk,
                "name": match.home_team.name,
            },
            "awayTeam": {
                "id": match.away_team.pk,
                "name": match.away_team.name,
            },
            "statistic": {
                "homeTeam": None,
                "awayTeam": None
            },
            "methodEndMatch": TRANSLATE_METHOD_END_MATCH_TO_RUSSIAN_LANGUAGE[match.method_end_match]
            if match.method_end_match is not None else None,
            "scoreResult": result_score,
        }
        result.append(match)

    return result
