
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView, RegisterView, ProfileView, SendConfirmationEmailView, ConfirmEmailView, \
    LogoutView

app_name = 'userApi'

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),

    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email/<str:confirmation_key>/', ConfirmEmailView.as_view(), name='confirm_email'),
    path('send-confirmation-email/', SendConfirmationEmailView.as_view(), name='send_confirmation_email'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileView.as_view(), name='update-profile'),

]
