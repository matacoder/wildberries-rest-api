from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class LoginView(FormView):
    success_url = reverse_lazy("index")
    template_name = "registration/login.html"


class LogoutView(TemplateView):
    template_name = "registration/logged_out.html"


class PasswordResetView(FormView):
    template_name = "registration/password_reset_form.html"


class PasswordResetDoneView(TemplateView):
    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmView(FormView):
    template_name = "registration/password_reset_confirm.html"


class PasswordResetCompleteView(TemplateView):
    template_name = "registration/password_reset_complete.html"


class PasswordChangeView(FormView):
    template_name = "registration/password_change_form.html"


class PasswordChangeDoneView(TemplateView):
    template_name = "registration/password_change_done.html"
