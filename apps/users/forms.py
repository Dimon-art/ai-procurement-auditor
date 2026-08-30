from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.companies.models import Company
from apps.users.models import UserProfile


User = get_user_model()


class ActiveUserAuthenticationForm(AuthenticationForm):
    """Reject login for inactive UserProfile.status."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        try:
            profile = user.profile
        except ObjectDoesNotExist:
            return

        if profile.status == UserProfile.Status.INACTIVE:
            raise ValidationError(
                "Учётная запись отключена. "
                "Обратитесь к администратору.",
                code="inactive",
            )


class RegistrationForm(forms.Form):
    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
    )
    full_name = forms.CharField(
        label="Имя",
        max_length=255,
    )
    email = forms.EmailField(
        label="E-mail",
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        strip=False,
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        strip=False,
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "Пользователь с таким именем уже существует."
            )

        return username

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                "Пароли не совпадают.",
            )

        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data

    def save(self):
        """
        Create User + own Company + UserProfile.

        Role is always operator. Role/company from POST are ignored.
        """
        username = self.cleaned_data["username"]
        full_name = self.cleaned_data["full_name"].strip()
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        company = Company.objects.create(
            name=f"Компания {username}",
        )

        UserProfile.objects.create(
            user=user,
            company=company,
            full_name=full_name,
            role=UserProfile.Role.OPERATOR,
            status=UserProfile.Status.ACTIVE,
        )

        return user
