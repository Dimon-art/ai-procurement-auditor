from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.companies.models import Company
from apps.users.models import UserProfile


class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
        error_messages={
            "required": "Укажите имя пользователя.",
        },
    )
    email = forms.EmailField(
        label="E-mail",
        error_messages={
            "required": "Укажите e-mail.",
            "invalid": "Введите корректный e-mail.",
        },
    )
    company_name = forms.CharField(
        label="Название компании",
        max_length=255,
        error_messages={
            "required": "Укажите название компании.",
        },
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        error_messages={
            "required": "Укажите пароль.",
        },
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        error_messages={
            "required": "Подтвердите пароль.",
        },
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if not username:
            raise ValidationError(
                "Укажите имя пользователя.",
            )

        if User.objects.filter(
            username=username,
        ).exists():
            raise ValidationError(
                "Пользователь с таким именем уже существует.",
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(
            email=email,
        ).exists():
            raise ValidationError(
                "Пользователь с таким e-mail уже существует.",
            )

        return email

    def clean_company_name(self):
        company_name = self.cleaned_data["company_name"].strip()

        if not company_name:
            raise ValidationError(
                "Укажите название компании.",
            )

        return company_name

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(
                "Пароли не совпадают.",
            )

        if password1:
            try:
                password_validation.validate_password(
                    password1,
                )
            except ValidationError:
                raise ValidationError(
                    "Пароль слишком простой или не соответствует "
                    "требованиям безопасности.",
                ) from None

        return cleaned_data

    @transaction.atomic
    def save(self):
        company_name = self.cleaned_data["company_name"]

        company = (
            Company.objects
            .filter(name__iexact=company_name)
            .first()
        )

        if company is None:
            company = Company.objects.create(
                name=company_name,
            )

        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            is_staff=False,
            is_superuser=False,
        )

        UserProfile.objects.create(
            user=user,
            company=company,
            full_name=self.cleaned_data["username"],
            role=UserProfile.Role.OPERATOR,
            status=UserProfile.Status.ACTIVE,
        )

        return user
