import hashlib
from abc import abstractmethod
from datetime import datetime, timedelta, date
from countries.models import Country
from parsing.parserUtils import download_image


class BaseAddMatchesToDB:
    def __init__(self, _models, _type_sport, _list_matches=None, _dictionary_championships_with_matches=None,
                 _dictionary_teams_with_matches=None, ):
        self._list_matches = _list_matches
        self._dictionary_championships_with_matches = _dictionary_championships_with_matches
        self.__dictionary_teams_with_matches = _dictionary_teams_with_matches

        self._models = _models
        self._type_sport = _type_sport

    def _images_equal(self, existing_image, new_image_file):
        """Сравнивает изображения по хешу содержимого"""
        if not existing_image:
            return False

        existing_hash = hashlib.md5(existing_image.read()).hexdigest()
        new_hash = hashlib.md5(new_image_file.read()).hexdigest()
        return existing_hash == new_hash

    def _save_image(self, image_field, filename, content):
        """Безопасное сохранение изображения с удалением старой версии"""
        if image_field:
            image_field.delete(save=False)
        image_field.save(filename, content, save=True)

    @staticmethod
    def check_need_update_team_coach_end_date(model, team):
        coaches_records = list(model.objects.filter(team=team).order_by('start_date'))

        if len(coaches_records) < 2:
            return False

        for i in range(len(coaches_records) - 1):
            current_coach = coaches_records[i]
            next_coach = coaches_records[i+1]

            if current_coach.end_date is None or next_coach.start_date - timedelta(days=1):
                return True
        return False

    def add_championships_with_matches_to_db(self):
        for championship, matches in self._dictionary_championships_with_matches.items():
            self.add_matches_to_db(matches)

    def add_teams_with_matches_to_db(self):

        for team, matches in self.__dictionary_teams_with_matches.items():
            self.add_matches_to_db(matches)
            last_match = matches[-1] if matches else None

            if not last_match:
                return

            if matches[-1]["match_info"]["home"]["name"] == team:
                team_info = {
                    "name": matches[-1]["match_info"]["home"]["name"],
                    "uuid": matches[-1]["match_info"]["home"]["uuid"]
                }
            else:
                team_info = {
                    "name": matches[-1]["match_info"]["away"]["name"],
                    "uuid": matches[-1]["match_info"]["away"]["uuid"]
                }
            self.update_team_last_update(self._models["Team"], team_info, matches[-1]["match_info"]["date"])

    @abstractmethod
    def add_matches_to_db(self, list_matches):
        raise NotImplementedError("Этот метод должен быть реализован в дочернем классе")

    @staticmethod
    @abstractmethod
    def add_match_to_db(match):
        raise NotImplementedError("Этот метод должен быть реализован в дочернем классе")

    def get_or_update_or_create_country(self, country_name, image_url=None):
        """Создает или обновляет страну с изображением"""
        country, created = Country.objects.get_or_create(
            name__iexact=country_name,
            defaults={'name': country_name}
        )

        if image_url:
            new_image = download_image(image_url)
            if not country.image or not self._images_equal(country.image, new_image):
                filename = f"countries/{country.pk}.jpg"
                self._save_image(country.image, filename, new_image)

        return country

    def get_or_update_or_create_championship(self, championship_info):
        model_championship = self._models["Championship"]

        name = championship_info.get("name")
        country_name = championship_info.get("country_name", "").strip()
        image_championship_url = championship_info.get("image_championship")

        if not name:
            raise ValueError("Обязательное поле 'name' отсутствует")

        # Обработка страны
        country = None
        if country_name:
            country = self.get_or_update_or_create_country(
                country_name=country_name,
                image_url=championship_info.get("image_country")
            )

        # Создание/обновление чемпионата
        championship, created = model_championship.objects.update_or_create(
            name=name,
            defaults={
                'country': country,
            }
        )

        # Обработка изображения чемпионата
        if image_championship_url:
            new_image = download_image(image_championship_url)
            if not championship.image_championship or not self._images_equal(championship.image_championship, new_image):
                filename = f"{championship.pk}.jpg"
                self._save_image(championship.image_championship, filename, new_image)

        return championship

    def get_or_create_season(self, season_info, championship):
        model_season = self._models["Season"]
        season_years = season_info.get("years", None)
        # season_type = season_info.get("season_type", None)

        if not season_years:
            # raise KeyError("Поле 'years' обязательно для заполнения в season_info")
            return None

        # if season_type not in [Season.REGULAR_SEASON, Season.PLAYOFF]:
        #     # raise ValueError("Неверное значение для 'season_type'")
        #     return None

        season, created = model_season.objects.get_or_create(
            championship=championship,
            season=season_years,
            # season_type=season_type
        )

        return season

    def get_or_create_team(self, team_info):
        model_team = self._models["Team"]

        team_name = team_info.get("name", None)
        image_url = team_info.get("image", None)

        if not team_name:
            raise KeyError("Поле 'team_name' обязательно для заполнения в team_info")

        team, created = model_team.objects.get_or_create(
            name=team_name,
        )

        if image_url:
            new_image = download_image(image_url)
            print(team)
            if not team.image or not self._images_equal(team.image, new_image):
                filename = f"{team.pk}.jpg"
                self._save_image(team.image, filename, new_image)

        return team

    def get_or_create_team_championship(self, team, championship):
        model_team_championship = self._models["TeamChampionship"]

        team_championship, created = model_team_championship.objects.get_or_create(
            team=team,
            championship=championship
        )
        return team_championship

    def get_or_create_coach(self, coach_info):
        model_coach = self._models["Coach"]

        # Извлечение и нормализация данных
        name = coach_info.get("name", "").strip()
        nationality = coach_info.get("nationality", "").strip()
        birthdate = coach_info.get("birthdate", "")
        image_nationality_url = coach_info.get("image_nationality_url")
        image_coach_url = coach_info.get("image_coach_url")

        # Валидация обязательных полей
        if not name:
            raise ValueError("'name' обязательно для заполнения")

        # # Обработка даты рождения
        # birthdate = None
        # if birthdate_str:
        #     try:
        #         birthdate = make_aware(datetime.strptime(birthdate_str, "%Y-%m-%d"))
        #     except (ValueError, TypeError):
        #         pass

        # Обработка национальности (страны)
        country = None
        if nationality:
            country = self.get_or_update_or_create_country(
                country_name=nationality,
                image_url=image_nationality_url
            )

        # Создание/обновление тренера
        coach, created = model_coach.objects.update_or_create(
            name=name,
            defaults={
                # 'birthdate': birthdate,
                'nationality': country,
            }
        )

        # Обработка изображения тренера
        if image_coach_url:
            new_image = download_image(image_coach_url)
            if not self._images_equal(coach.image_coach, new_image):
                filename = f"coaches/{coach.pk}.jpg"
                self._save_image(coach.image_coach, filename, new_image)

        return coach

    def get_or_create_coach_team(self, coach, team, coach_info):
        model_coach_team = self._models["TeamCoach"]

        # Обработка даты начала
        start_date = coach_info.get("start_date")
        if not isinstance(start_date, date):
            raise ValueError("Неподдерживаемый формат даты")

        # Получаем последнюю запись для команды
        last_coach_team = model_coach_team.objects.filter(
            team=team
        ).order_by("-start_date").first()

        # Логика определения необходимости новой записи
        new_record_needed = True
        if last_coach_team:
            if last_coach_team.coach == coach:
                return last_coach_team

            if last_coach_team.start_date >= start_date:
                new_record_needed = False

        # Создаем или обновляем запись
        if new_record_needed:
            # Закрываем предыдущую запись
            if last_coach_team and not last_coach_team.end_date:
                last_coach_team.end_date = start_date - timedelta(days=1)
                last_coach_team.save()

            # Создаем новую запись
            team_coach = model_coach_team.objects.create(
                coach=coach,
                team=team,
                start_date=start_date,
                end_date=None
            )
            return team_coach

        # Обновляем существующую запись если нужно
        if last_coach_team.start_date < start_date:
            last_coach_team.start_date = start_date
            last_coach_team.save()
            return last_coach_team

        return last_coach_team

    def get_or_create_referee(self, referee_info):
        model_referee = self._models["Referee"]

        # Извлечение и нормализация данных
        name = referee_info.get("name", "").strip()
        uuid = referee_info.get("uuid", "").strip()
        nationality = referee_info.get("nationality", "").strip()
        birthdate = referee_info.get("birthdate", "")
        image_nationality_url = referee_info.get("image_nationality_url")
        image_referee_url = referee_info.get("image_referee_url")

        # Валидация обязательных полей
        if not name:
            raise ValueError("'name' обязательно для заполнения")
        if not uuid:
            raise ValueError("'uuid' обязательно для заполнения")

        # Обработка даты рождения
        # birthdate = None
        # if birthdate_str:
        #     try:
        #         birthdate = make_aware(datetime.strptime(birthdate_str, "%Y-%m-%d"))
        #     except (ValueError, TypeError):
        #         pass

        # Обработка национальности (страны)
        country = None
        if nationality:
            country = self.get_or_update_or_create_country(
                country_name=nationality,
                image_url=image_nationality_url
            )

        # Создание/обновление арбитра
        referee, created = model_referee.objects.update_or_create(
            name=name,
            defaults={
                'nationality': country,
                # 'birthdate': birthdate,
                # 'position': model_referee.MAIN_REFEREE,
            }
        )

        # Обработка изображения арбитра
        if image_referee_url:
            new_image = download_image(image_referee_url)
            if not self._images_equal(referee.image_referee, new_image):
                filename = f"{referee.pk}.jpg"
                self._save_image(referee.image_referee, filename, new_image)

        return referee

    def get_or_create_referee_championship(self, referee, championship):
        model_referee_championship = self._models["RefereeChampionship"]

        referee_championship, created = model_referee_championship.objects.get_or_create(
            referee=referee,
            championship=championship
        )
        return referee_championship

    @staticmethod
    def update_team_last_update(model_team, team_info, date_last_update):
        print(team_info["name"], team_info["uuid"])
        team = model_team.objects.get(name=team_info["name"], uuid=team_info["uuid"])
        team.last_update_date = date_last_update
        team.save()
        return team
