from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from WolframScore import settings

api_urls = [
    # path('', include('ParserFlashScore.urls')),
    path('', include('userApi.urls')),
    path('', include('parserHockey.urls'))
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

