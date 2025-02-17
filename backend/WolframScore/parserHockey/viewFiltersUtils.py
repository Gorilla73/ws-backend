type_statistic = {
    "mainTypeStatistic": [
        {"key": "goals", "value": "Голы"},
        {"key": "shotsOnGoal", "value": "Броски в створ ворот"},
        {"key": "minorPenalties", "value": "Кол-во 2-х минутных удалений"},
        {"key": "powerplayGoals", "value": "Голы в большинстве"},
        {"key": "faceoffsWon", "value": "Выигранные вбрасывания"},
        {"key": "faceoffsPercentage", "value": "Процент выигранных вбрасываний"},
        {"key": "hits", "value": "Силовые приемы"},
    ],
    "otherTypeStatistic": [
        {"key": "shotsOffGoal", "value": "Броски мимо"},
        {"key": "shootingPercentage", "value": "Реализация бросков, %"},
        {"key": "blockedShots", "value": "Заблокированные броски"},
        {"key": "penalties", "value": "Кол-во удалений"},
        {"key": "majorPenalties", "value": "Кол-во 5-х минутных удалений"},
        {"key": "minorPenaltyTime", "value": "Штрафное время 2-х минутных удалений"},
        {"key": "majorPenaltyTime", "value": "Штрафное время 5-х минутных удалений"},
        {"key": "shorthandedGoals", "value": "Голы в меньшинстве"},
        {"key": "powerplayPercentage", "value": "Процент реализации большинства"},
        {"key": "penaltyKillPercentage", "value": "Процент игры в меньшинстве"},
        {"key": "giveaways", "value": "Потери"},
        {"key": "takeaways", "value": "Перехваты"},
        {"key": "emptyNetGoals", "value": "Голы в пустые ворота"}
    ],
}

count_matches = ["5", "10", "20", "30", "40", "50", "100"]
place_filters = [
    {"key": "home", "value": "Дома"},
    {"key": "away", "value": "На выезде"},
    {"key": "all", "value": "Все"}
]
periods = [
    {"key": "firstPeriod", "value": "1-й период"},
    {"key": "secondPeriod", "value": "2-й период"},
    {"key": "thirdPeriod", "value": "3-й период"},
    {"key": "afterFirstPeriod", "value": "После 1-го периода"},
    {"key": "allMatch", "value": "Весь матч"},

]
coach_filters = [
    {"key": "currentCoach", "value": "Только с текущим тренером"},
    {"key": "all", "value": "Все"}
]
result_after_period = [
    {"key": 'winAfterFirstPeriod', "value": 'Ведет после 1-го периода'},
    {"key": 'drawAfterFirstPeriod', "value": 'Ничья после 1-го периода'},
    {"key": 'loseAfterFirstPeriod', "value": 'Проигрывает после 1-го периода'},
    {"key": 'winAfterSecondPeriod', "value": 'Ведет после 2-го периода'},
    {"key": 'drawAfterSecondPeriod', "value": 'Ничья после 2-го периода'},
    {"key": 'loseAfterSecondPeriod', "value": 'Проигрывает после 2-го периода'},
    {"key": 'all', "value": 'Все'}
]

default_select_match_filters = {
    "shared_filters": {
        "typeStatistic": type_statistic["mainTypeStatistic"][0]["key"],
        "countMatches": {
            # "selectCount": count_matches[len(count_matches) // 2],
            "selectCount": count_matches[-1],
            "customCount": False,
        },
        "period": "allMatch"
    },
    "home_team_filters": {
        "place": "all",
        "championships": "all",
        "seasons": "all",
        "resultAfterPeriod": "all",
        "odds": {
            "selectOdds": "all",
            "customOdds": False
        },
        "coach": "all",
    },
    "away_team_filters": {
        "place": "all",
        "championships": "all",
        "seasons": "all",
        "resultAfterPeriod": "all",
        "odds": {
            "selectOdds": "all",
            "customOdds": False
        },
        "coach": "all",
    }
}

default_select_championship_filters = {
    "dependentFilters": {
        "typeStatistic": type_statistic["mainTypeStatistic"][0]["key"],
        "countMatches": {
            "selectCount": count_matches[len(count_matches) // 2],
            "customCount": False,
        },
        "period": "allMatch",
    },
    "independentFilters": {
        "place": "all",
        "seasons": "all",
        "resultAfterPeriod": "all",
        "odds": {
            "selectOdds": "all",
            "customOdds": False
        },
        "coach": "all",
    }

}
