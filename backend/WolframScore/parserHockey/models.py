import copy

from django.db import models

from baseModels.baseModelsTeamSports.base import BaseChampionship, BaseSeason, BaseTeam, BaseTeamChampionship, \
    BaseCoach, BaseTeamCoach, BaseReferee, BaseMatch, BaseMatchOdds, BaseMatchStats, \
    BaseMatchReferee, BaseRefereeChampionship, get_default_odds
from parserHockey.parserSharedUtils import get_default_initial_match_statistic


class Championship(BaseChampionship):

    def get_sport_name(self):
        return "hockey"


class Season(BaseSeason):
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, verbose_name="Чемпионат",
                                     related_name='seasons')

    def __str__(self):
        return f"{self.championship.name} {self.season}"

    def get_sport_name(self):
        return "hockey"


class Team(BaseTeam):

    def get_sport_name(self):
        return "hockey"


class TeamChampionship(BaseTeamChampionship):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Команда")
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, verbose_name="Чемпионат")

    def __str__(self):
        return f"{self.team} в {self.championship}"


class Coach(BaseCoach):

    def get_sport_name(self):
        return "hockey"


class TeamCoach(BaseTeamCoach):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Команда")
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, verbose_name="Тренер")

    def __str__(self):
        return f"{self.coach} тренер команды {self.team}"


class Referee(BaseReferee):
    MAIN_REFEREE = "MR"
    LINE_REFEREE = "LR"
    REFEREE_POSITION_CHOICES = [
        (MAIN_REFEREE, 'Главный арбитр'),
        (LINE_REFEREE, 'Линейный арбитр'),
    ]

    position = models.CharField(max_length=2, choices=REFEREE_POSITION_CHOICES, verbose_name="Позиция", default='?')

    def get_sport_name(self):
        return "hockey"


class RefereeChampionship(BaseRefereeChampionship):
    referee = models.ForeignKey(Referee, on_delete=models.CASCADE, verbose_name="Судья")
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, verbose_name="Чемпионат")

    def __str__(self):
        return f"{self.referee} в {self.championship}"


class Match(BaseMatch):
    METHOD_END_MATCH = [
        ('MT', 'Основное время'),
        ('OT', 'Овертайм'),
        ('SO', 'Буллиты')
    ]
    STATUS_CHOICES = [
        ('cancelled', 'Отменен'),
        ('postponed', 'Перенесен'),
        ('completed', 'Завершен'),
        ('in_progress', 'Идет'),
        ('not_started', 'Не начался')
    ]
    season = models.ForeignKey(Season, on_delete=models.CASCADE, verbose_name="Сезон", blank=True, null=True)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, verbose_name="Чемпионат")
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE,
                                  verbose_name="Домашняя команда")
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE,
                                  verbose_name="Гостевая команда")
    winner = models.ForeignKey(Team, related_name='won_match', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Победитель")

    method_end_match = models.CharField(max_length=2, choices=METHOD_END_MATCH, default="MT",
                                        verbose_name="Способ окончания матча", blank=True, null=True)
    overtime_count = models.PositiveIntegerField(verbose_name="Количество овертаймов", default=0, blank=True, null=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.date}"


class MatchOdds(BaseMatchOdds):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='odds', verbose_name="Матч")

    shots_on_goals = models.JSONField(default=get_default_odds, verbose_name='Броски в створ ворот')
    two_minutes_penalties_time = models.JSONField(default=get_default_odds, verbose_name='Штрафное время')
    faceoffs_won = models.JSONField(default=get_default_odds, verbose_name="Выигранные вбрасывания")
    power_play_goals = models.JSONField(default=get_default_odds, verbose_name="Голы в большинстве")

    def __str__(self):
        return f"Коэффициенты {self.bookmaker} для {self.match}"


class MatchStats(BaseMatchStats):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name="Матч")

    shots = models.JSONField(verbose_name="Броски в сторону ворот", default=get_default_initial_match_statistic)
    shots_on_goals = models.JSONField(verbose_name="Броски в створ ворот", default=get_default_initial_match_statistic)
    shots_off_goal = models.JSONField(verbose_name="Броски мимо", default=get_default_initial_match_statistic)
    shooting_percentage = models.JSONField(verbose_name="Реализация бросков, %",
                                           default=get_default_initial_match_statistic)

    blocked_shots = models.JSONField(verbose_name="Заблокированные броски", default=get_default_initial_match_statistic)
    goalkeeper_saves = models.JSONField(verbose_name="Отраженные броски", default=get_default_initial_match_statistic)
    goalkeeper_saves_percentage = models.JSONField(verbose_name="Отраженные броски, %",
                                                   default=get_default_initial_match_statistic)

    penalties = models.JSONField(verbose_name="Кол-во удалений", default=get_default_initial_match_statistic)

    two_minutes_penalties = models.JSONField(verbose_name="Кол-во 2-х минутных удалений",
                                             default=get_default_initial_match_statistic)
    five_minutes_penalties = models.JSONField(verbose_name="Кол-во 5-х минутных удалений",
                                              default=get_default_initial_match_statistic)

    two_minutes_penalties_time = models.JSONField(verbose_name="Штрафное время 2-х минутных удалений",
                                                  default=get_default_initial_match_statistic)
    five_minutes_penalties_time = models.JSONField(verbose_name="Штрафное время 5-х минутных удалений",
                                                   default=get_default_initial_match_statistic)

    power_play_goals = models.JSONField(verbose_name="Голы в большинстве", default=get_default_initial_match_statistic)
    shorthanded_goals = models.JSONField(verbose_name="Голы в меньшинстве", default=get_default_initial_match_statistic)
    power_play_percentage = models.JSONField(verbose_name="Процент реализации большинства",
                                             default=get_default_initial_match_statistic)
    penalty_kill_percentage = models.JSONField(verbose_name="Процент игры в меньшинстве",
                                               default=get_default_initial_match_statistic)

    hits = models.JSONField(verbose_name="Силовые приемы", default=get_default_initial_match_statistic)
    faceoffs_won = models.JSONField(verbose_name="Выигранные вбрасывания", default=get_default_initial_match_statistic)
    faceoffs_won_percentage = models.JSONField(verbose_name="Процент выигранных вбрасываний",
                                               default=get_default_initial_match_statistic)

    giveaways = models.JSONField(verbose_name="Потери", default=get_default_initial_match_statistic)
    takeaways = models.JSONField(verbose_name="Перехваты", default=get_default_initial_match_statistic)
    empty_net_goal = models.JSONField(verbose_name="Голы в пустые ворота", default=get_default_initial_match_statistic)


class MatchReferee(BaseMatchReferee):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name="Матч")
    referee = models.ForeignKey(Referee, on_delete=models.CASCADE, verbose_name="Судья")

    def __str__(self):
        return f"Судья {self.referee} на матче {self.match}"




