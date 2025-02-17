#!/bin/bash

# Путь к виртуальному окружению
source /Users/antongavrilov/PycharmProjects/WolframScore/backend/WolframScore/venv/bin/activate

# Путь к проекту
# shellcheck disable=SC2164
cd /Users/antongavrilov/PycharmProjects/WolframScore/backend/WolframScore

# Выгрузка данных
python manage.py dumpdata parserHockey.Championship --indent 2 > dataJson/hockey/championship_data.json
python manage.py dumpdata parserHockey.Season --indent 2 > dataJson/hockey/season_data.json
python manage.py dumpdata parserHockey.Team --indent 2 > dataJson/hockey/team_data.json
python manage.py dumpdata parserHockey.TeamChampionship --indent 2 > dataJson/hockey/teamChampionship_data.json
python manage.py dumpdata parserHockey.Player --indent 2 > dataJson/hockey/player_data.json
python manage.py dumpdata parserHockey.TeamPlayer --indent 2 > dataJson/hockey/teamPlayer_data.json
python manage.py dumpdata parserHockey.Coach --indent 2 > dataJson/hockey/coach_data.json
python manage.py dumpdata parserHockey.TeamCoach --indent 2 > dataJson/hockey/teamCoach_data.json
python manage.py dumpdata parserHockey.Referee --indent 2 > dataJson/hockey/referee_data.json
python manage.py dumpdata parserHockey.RefereeChampionship --indent 2 > dataJson/hockey/refereeChampionship_data.json
python manage.py dumpdata parserHockey.Match --indent 2 > dataJson/hockey/match_data.json
python manage.py dumpdata parserHockey.MatchOdds --indent 2 > dataJson/hockey/matchOdds_data.json
python manage.py dumpdata parserHockey.Lineup --indent 2 > dataJson/hockey/lineup_data.json
python manage.py dumpdata parserHockey.MatchStats --indent 2 > dataJson/hockey/matchStats_data.json
python manage.py dumpdata parserHockey.MatchReferee --indent 2 > dataJson/hockey/matchReferee_data.json
python manage.py dumpdata parserHockey.PlayerMatchStats --indent 2 > dataJson/hockey/playerMatchStats_data.json

echo "Hockey data dump completed."