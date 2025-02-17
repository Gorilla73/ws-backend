import copy

from django.db import models

import os


# Пока тут, потом вынести в baseModels/utils
def get_upload_path(instance, filename, folder_name):
    """
    Абстрагированная функция для формирования пути загрузки файлов.

    Args:
        instance: Экземпляр модели (например, Team или Championship).
        filename: Имя загружаемого файла.
        folder_name: Название папки для типа сущности (например, 'team_images' или 'championship_images').

    Returns:
        str: Путь для загрузки файла.
    """
    sport_name = instance.get_sport_name()

    # Пример: 'hockey/team_images/filename.jpg'
    return os.path.join(f'{sport_name}/{folder_name}', filename)


def get_upload_championship_path(instance, filename):
    return get_upload_path(instance, filename, 'championships_images')


def get_upload_team_path(instance, filename):
    return get_upload_path(instance, filename, 'team_images')


def get_upload_coach_path(instance, filename):
    return get_upload_path(instance, filename, 'coaches_images')


def get_upload_referee_path(instance, filename):
    return get_upload_path(instance, filename, 'referee_images')


class BaseChampionship(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название чемпионата")
    image_championship = models.ImageField(
        upload_to=get_upload_championship_path,
        verbose_name='Изображение чемпионата', null=True, blank=True)
    country = models.ForeignKey("countries.Country", on_delete=models.CASCADE, null=True, blank=True,
                                related_name="%(class)s_championships", verbose_name="Страна")

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = "Чемпионат"
        verbose_name_plural = "Чемпионаты"

    def get_sport_name(self):
        raise NotImplementedError("Метод get_sport_name должен быть переопределен в дочернем классе")


class BaseSeason(models.Model):
    season = models.CharField(max_length=9, verbose_name="Сезон")  # Формат: "год" или "год/год"

    class Meta:
        abstract = True
        verbose_name = "Сезон"
        verbose_name_plural = "Сезоны"

    def get_sport_name(self):
        raise NotImplementedError("Метод get_sport_name должен быть переопределен в наследниках")

        # return "hockey" or "basketball" or ...


class BaseTeam(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название команды")
    # uuid = models.CharField(max_length=255, verbose_name="Уникальный идентификатор", blank=True, null=True)
    image = models.ImageField(upload_to=get_upload_team_path,
                              null=True, blank=True, verbose_name='Логотип команды')
    # home_city = baseModels.CharField(max_length=100, verbose_name="Город", default='?')

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = "Команда"
        verbose_name_plural = "Команды"

    def get_sport_name(self):
        raise NotImplementedError("Метод get_sport_name должен быть переопределен в дочернем классе")

        # return "hockey" or "basketball" or ...


class BaseTeamChampionship(models.Model):
    # start_date = baseModels.DateField(verbose_name="Дата начала")
    # end_date = baseModels.DateField(null=True, blank=True, verbose_name="Дата окончания")

    class Meta:
        abstract = True
        verbose_name = "Участие команды в чемпионате"
        verbose_name_plural = "Участия команды в чемпионатах"


class BaseCoach(models.Model):
    name = models.CharField(max_length=50, verbose_name="Имя")
    # uuid = models.CharField(max_length=255, verbose_name="Уникальный идентификатор", null=True, blank=True)
    nationality = models.ForeignKey(
        "countries.Country",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_coaches",
        verbose_name="Национальность"
    )

    image_coach = models.ImageField(
        upload_to=get_upload_coach_path,
        null=True, blank=True, verbose_name='Фото тренера'
    )
    birthdate = models.DateField(verbose_name="Дата рождения", null=True, blank=True, default='1971-01-01')

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = "Тренер"
        verbose_name_plural = "Тренеры"

    def get_sport_name(self):
        raise NotImplementedError("Метод get_sport_name должен быть переопределен в дочернем классе")


class BaseTeamCoach(models.Model):
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания", default=None)

    class Meta:
        abstract = True
        verbose_name = "Тренер команды"
        verbose_name_plural = "Тренеры команд"


class BaseReferee(models.Model):
    name = models.CharField(max_length=150, verbose_name="Имя")
    # uuid = models.CharField(max_length=255, verbose_name="Уникальный идентификатор", null=True, blank=True)
    nationality = models.ForeignKey(
        "countries.Country",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_referees",
        verbose_name="Национальность"
    )

    image_referee = models.ImageField(
        upload_to=get_upload_referee_path,
        null=True, blank=True, verbose_name='Фото судьи'
    )
    birthdate = models.DateField(verbose_name="Дата рождения", null=True, blank=True, default='1971-01-01')

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = "Судья"
        verbose_name_plural = "Судьи"

    def get_sport_name(self):
        raise NotImplementedError("Метод get_sport_name должен быть переопределен в дочернем классе")


class BaseRefereeChampionship(models.Model):
    # start_date = baseModels.DateField(verbose_name="Дата начала")
    # end_date = baseModels.DateField(null=True, blank=True, verbose_name="Дата окончания")

    class Meta:
        abstract = True
        verbose_name = "Участие судьи в чемпионате"
        verbose_name_plural = "Участия судьи в чемпионатах"


class BaseMatch(models.Model):
    STATUS_CHOICES = [
        ('cancelled', 'Отменен'),
        ('postponed', 'Перенесен'),
        ('completed', 'Завершен'),
        ('in_progress', 'Идет'),
        ('not_started', 'Не начался')
    ]

    date = models.DateTimeField(verbose_name="Дата и время")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='Статус')
    result = models.JSONField(verbose_name="Счет", default=dict, blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = "Матч"
        verbose_name_plural = "Матчи"


def get_default_odds():
    return copy.deepcopy(BaseMatchOdds.default_odds)


class BaseMatchOdds(models.Model):
    default_odds = {
        "line": [],
        "live": []
    }
    STATUS_CHOICES = [
        ('1xbet', '1xbet'),
        ('fonbet', 'Фонбет'),
        ('liga_stavok', 'Лига ставок')
    ]

    bookmaker = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='букмекер')

    score = models.JSONField(default=get_default_odds, verbose_name='Счет')

    class Meta:
        abstract = True
        verbose_name = "Коэффициенты матча"
        verbose_name_plural = "Коэффициенты матчей"


class BaseMatchStats(models.Model):
    class Meta:
        abstract = True
        verbose_name = "Статистика матча"
        verbose_name_plural = "Статистика матчей"


class BaseMatchReferee(models.Model):
    class Meta:
        abstract = True
        verbose_name = "Судья на матче"
        verbose_name_plural = "Судьи на матчах"
