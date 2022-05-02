from django.urls import path
from main.views import HomeView, CustomLoginView, CustomLogoutView, CustomUserSignUpView, RoomView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('room/<id>/', RoomView.as_view(), name='room'),
    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', CustomUserSignUpView.as_view(), name='signup'),
]