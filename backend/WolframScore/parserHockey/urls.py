from django.urls import path

from parserHockey.views import GetChampionshipsView, GetMatchesByChampionshipView, GetMatchInfoView, FilterInfoView, \
    GetMatchesWithFiltersView, GetChampionshipInfoView, GetChampionshipFiltersView, GetTableChampionshipWithFiltersView

app_name = "parserHockey"

urlpatterns = [
    path('hockey/getChampionships/', GetChampionshipsView.as_view(), name='getChampionships'),
    path('hockey/getMatchesByChampionship/', GetMatchesByChampionshipView.as_view(), name='getMatchesByChampionship'),
    path('hockey/getMatchInfo/', GetMatchInfoView.as_view(), name='getMatchInfo'),
    path('hockey/getFiltersMatchInfo/', FilterInfoView.as_view(), name='getFiltersInfo'),
    path('hockey/getMatchesWithFilters/', GetMatchesWithFiltersView.as_view(), name='getMatchesWithFilters'),

    path('hockey/getChampionshipInfo/', GetChampionshipInfoView.as_view(), name='getChampionshipInfo'),
    path('hockey/getFiltersChampionshipInfo/', GetChampionshipFiltersView.as_view(), name='getChampionshipFilters'),
    path('hockey/getTableChampionshipWithFilters/', GetTableChampionshipWithFiltersView.as_view(),
         name='getTableChampionshipWithFilters')
]
