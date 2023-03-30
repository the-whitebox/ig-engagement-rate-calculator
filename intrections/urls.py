from django.urls import path
from .views import user_info
from .views import CustomUserLogin


urlpatterns = [
    path('user_info/<str:username>/', user_info, name='user_info'),
    path('login/', CustomUserLogin.as_view(), name='login'),


]
