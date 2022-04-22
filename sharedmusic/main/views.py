from django.shortcuts import render, redirect, reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic import DetailView
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404
from main.models import Room, Soundtrack, Playlist
from main.forms import CustomUserCreationForm, RoomCreationForm
from main import consts


class HomeView(LoginRequiredMixin, CreateView):
    form_class = RoomCreationForm
    model = Room
    template_name = 'home.html'

    def get_success_url(self):
        url = reverse('room', kwargs={ "code": self.object.code })
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        if "room_code" in request.POST:
            # Join to existing room
            room_code = request.POST.get("room_code")
            room_url = reverse('room', kwargs={ "code": room_code })
            # Check if room exists
            room_exists = self.model.objects.filter(code=room_code).exists()
            if room_exists:
                return redirect(room_url)
            else:
                raise Http404(consts.ROOM_NOT_FOUND)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.host = self.request.user
        # Create new playlist
        playlist = Playlist.objects.create()
        form.instance.playlist = playlist
        return super().form_valid(form)


class RoomView(LoginRequiredMixin, TemplateView):
    template_name = 'room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["room"] = Room.objects.filter(code=kwargs["code"]).first()
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
