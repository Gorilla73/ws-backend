#!/bin/bash

# Путь к виртуальному окружению
source /Users/antongavrilov/PycharmProjects/WolframScore/backend/WolframScore/venv/bin/activate

# Путь к проекту
# shellcheck disable=SC2164
cd /Users/antongavrilov/PycharmProjects/WolframScore/backend/WolframScore

# Выгрузка данных
python manage.py loaddata dataJson/hockey/championship_data.json
python manage.py loaddata dataJson/hockey/season_data.json
python manage.py loaddata dataJson/hockey/team_data.json
python manage.py loaddata dataJson/hockey/teamChampionship_data.json
python manage.py loaddata dataJson/hockey/player_data.json
python manage.py loaddata dataJson/hockey/teamPlayer_data.json
python manage.py loaddata dataJson/hockey/coach_data.json
python manage.py loaddata dataJson/hockey/teamCoach_data.json
python manage.py loaddata dataJson/hockey/referee_data.json
python manage.py loaddata dataJson/hockey/refereeChampionship_data.json
python manage.py loaddata dataJson/hockey/match_data.json
python manage.py loaddata dataJson/hockey/matchOdds_data.json
python manage.py loaddata dataJson/hockey/lineup_data.json
python manage.py loaddata dataJson/hockey/matchStats_data.json
python manage.py loaddata dataJson/hockey/matchReferee_data.json
python manage.py loaddata dataJson/hockey/playerMatchStats_data.json

echo "Hockey data load completed."