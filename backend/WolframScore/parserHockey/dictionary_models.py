import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WolframScore.settings")

import django

django.setup()

from parserHockey.models import Championship, Season, Team, TeamChampionship, Coach, TeamCoach, \
    Referee, RefereeChampionship, Match, MatchOdds, MatchStats, MatchReferee

models_hockey = {
    "Championship": Championship,
    "Season": Season,
    "Team": Team,
    "TeamChampionship": TeamChampionship,
    "Coach": Coach,
    "TeamCoach": TeamCoach,
    "Referee": Referee,
    "RefereeChampionship": RefereeChampionship,
    "Match": Match,
    "MatchOdds": MatchOdds,
    "MatchStats": MatchStats,
    "MatchReferee": MatchReferee,
}
