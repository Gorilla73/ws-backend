import copy

default_initial_match_result = {
    "1st_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "2nd_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "3rd_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "main_time": {
        "home": {
            "result": None
        },
        "away": {
            "result": None
        },
    },
    "overtime": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "shootouts": {
        "home": {
            "result": None
        },
        "away": {
            "result": None
        },
    },
    "result": {
        "home": {
            "result": None
        },
        "away": {
            "result": None
        },
    }
}


default_initial_match_statistic = {
    "1st_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "2nd_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "3rd_period": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "main_time": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "overtime": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    },
    "match": {
        "home": {
            "time_to_point": {},
            "result": None
        },
        "away": {
            "time_to_point": {},
            "result": None
        }
    }
}


def get_default_initial_match_result():
    return copy.deepcopy(default_initial_match_result)


def get_default_initial_match_statistic():
    return copy.deepcopy(default_initial_match_statistic)
