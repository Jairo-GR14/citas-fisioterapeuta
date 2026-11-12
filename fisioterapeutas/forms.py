
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from .models import Fisioterapeuta


ESTILO = (
    "w-full rounded-xl border border-slate-300 "
    "bg-white px-4 py-3 text-sm"
)


class DatosFisioterapeutaForm(forms.Form):

    nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    apellidos = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={"class": ESTILO}
        ),
    )

    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    especialidad = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    cedula_profesional = forms.CharField(
        label="Cédula profesional",
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": ESTILO,
                "rows": 4,
            }
        ),
    )

    def __init__(
        self,
        *args,
        usuario_actual=None,
        fisioterapeuta_actual=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.usuario_actual = usuario_actual
        self.fisioterapeuta_actual = fisioterapeuta_actual

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        usuarios = User.objects.filter(
            email__iexact=email
        )

        if self.usuario_actual:
            usuarios = usuarios.exclude(
                pk=self.usuario_actual.pk
            )

        if usuarios.exists():
            raise ValidationError(
                "Este correo ya está registrado."
            )

        return email

    def clean_cedula_profesional(self):
        cedula = self.cleaned_data[
            "cedula_profesional"
        ].strip()

        if cedula:
            otros = Fisioterapeuta.objects.filter(
                cedula_profesional__iexact=cedula
            )

            if self.fisioterapeuta_actual:
                otros = otros.exclude(
                    pk=self.fisioterapeuta_actual.pk
                )

            if otros.exists():
                raise ValidationError(
                    "Esta cédula ya está registrada."
                )

        return cedula


class RegistrarFisioterapeutaForm(
    DatosFisioterapeutaForm
):

    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(
            attrs={"class": ESTILO}
        ),
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"class": ESTILO}
        ),
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={"class": ESTILO}
        ),
    )

    def clean_username(self):
        username = self.cleaned_data[
            "username"
        ].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():
            raise ValidationError(
                "Este nombre de usuario ya existe."
            )

        return username

    def clean(self):
        datos = super().clean()

        clave1 = datos.get("password1")
        clave2 = datos.get("password2")

        if clave1 and clave2:

            if clave1 != clave2:
                self.add_error(
                    "password2",
                    "Las contraseñas no coinciden.",
                )

            else:
                temporal = User(
                    username=datos.get("username", ""),
                    first_name=datos.get("nombre", ""),
                    last_name=datos.get("apellidos", ""),
                    email=datos.get("email", ""),
                )

                try:
                    validate_password(
                        clave1,
                        user=temporal,
                    )

                except ValidationError as error:
                    self.add_error(
                        "password1",
                        error,
                    )

        return datos


class EditarFisioterapeutaForm(
    DatosFisioterapeutaForm
):
    pass
