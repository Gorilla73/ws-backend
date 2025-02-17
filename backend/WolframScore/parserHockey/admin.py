from django.contrib import admin

from parserHockey.models import Championship, Season, Team, TeamChampionship, Coach, TeamCoach, \
    Referee, RefereeChampionship, Match, MatchOdds, MatchStats, MatchReferee

admin.site.register(Championship)
admin.site.register(Season)
admin.site.register(TeamChampionship)
admin.site.register(Team)
admin.site.register(Coach)
admin.site.register(TeamCoach)
admin.site.register(Referee)
admin.site.register(RefereeChampionship)
admin.site.register(MatchOdds)
# admin.site.register(MatchStats)
admin.site.register(MatchReferee)


class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'match_display',  # Используем метод для отображения матча
        'get_home_team',
        'get_away_team',
    )
    list_filter = (
        ('home_team', admin.RelatedOnlyFieldListFilter),
        ('away_team', admin.RelatedOnlyFieldListFilter),
    )

    def match_display(self, obj):
        return str(obj)  # Вызовет метод __str__ модели Match

    match_display.short_description = 'Матч'

    def get_home_team(self, obj):
        return obj.home_team

    get_home_team.admin_order_field = 'home_team'
    get_home_team.short_description = 'Домашняя команда'

    def get_away_team(self, obj):
        return obj.away_team

    get_away_team.admin_order_field = 'away_team'
    get_away_team.short_description = 'Гостевая команда'


admin.site.register(Match, MatchAdmin)


class MatchStatsAdmin(admin.ModelAdmin):
    list_display = (
        'match',
        'get_home_team',  # Добавьте метод для отображения домашней команды
        'get_away_team',  # Добавьте метод для отображения гостевой команды
        # и другие поля
    )
    list_filter = (
        'match__home_team',  # Фильтр по домашней команде
        'match__away_team',  # Фильтр по гостевой команде
    )

    def get_home_team(self, obj):
        return obj.match.home_team

    get_home_team.admin_order_field = 'match__home_team'  # Позволяет сортировать по этому полю
    get_home_team.short_description = 'Домашняя команда'

    def get_away_team(self, obj):
        return obj.match.away_team

    get_away_team.admin_order_field = 'match__away_team'  # Позволяет сортировать по этому полю
    get_away_team.short_description = 'Гостевая команда'


admin.site.register(MatchStats, MatchStatsAdmin)
