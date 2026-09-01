from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User, Counselor


class CounselorAuthenticationForm(AuthenticationForm):
    """Web girişi sadece rehberlere açıktır; öğrenci/veli mobilden girer."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not (user.is_counselor or user.is_superuser):
            raise forms.ValidationError(
                "Bu giriş yalnızca rehberler içindir. Öğrenci ve veliler mobil uygulamayı kullanmalıdır.",
                code="not_counselor",
            )


class CounselorRegisterForm(UserCreationForm):
    """Web kaydı sadece rehber içindir; kaydolan kullanıcı Counselor olarak işaretlenir."""
    first_name = forms.CharField(max_length=150, required=True, label="Ad")
    last_name = forms.CharField(max_length=150, required=True, label="Soyad")
    email = forms.EmailField(required=True, label="E-posta")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_counselor = True
        if commit:
            user.save()
            Counselor.objects.create(user=user)
        return user
