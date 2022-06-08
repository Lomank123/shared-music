from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from main.forms import CustomUserCreationForm, RoomCreationForm
from main.models import Room, RoomPlaylist


class HomeView(CreateView):
    form_class = RoomCreationForm
    model = Room
    template_name = 'home.html'
    login_url = '/signup/'

    def post(self, request):
        if request.user.is_authenticated:
            return super().post(request)
        else:
            return HttpResponseRedirect(reverse('signup'))

    def get_success_url(self):
        return reverse('room', kwargs={"id": self.object.id})

    def form_valid(self, form):
        # Attach user as a host
        form.instance.host = self.request.user
        response = super().form_valid(form)
        RoomPlaylist.objects.create(room_id=self.object.id)
        return response


class RoomView(LoginRequiredMixin, TemplateView):
    template_name = 'room.html'
    login_url = '/signup/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = Room.objects.filter(id=kwargs["id"]).first()
        context["is_banned"] = room.ban_list.filter(id=self.request.user.id).exists()
        context["room"] = room
        return context


class CustomLoginView(LoginView):
    template_name = "auth/login.html"


class CustomLogoutView(LogoutView):
    next_page = '/login/'


class CustomUserSignUpView(CreateView):
    model = get_user_model()
    form_class = CustomUserCreationForm
    template_name = 'auth/signup.html'
    success_url = '/'

    def form_valid(self, form):
        valid = super(CustomUserSignUpView, self).form_valid(form)
        raw_password = form.cleaned_data.get('password1')
        username = form.cleaned_data.get('username')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        return valid
