
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


CLASE = (
    "w-full rounded-xl border border-slate-300 "
    "bg-white px-4 py-3 text-sm"
)


class DatosPacienteForm(forms.Form):

    nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    apellidos = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"class": CLASE}),
    )

    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": CLASE,
            },
        ),
    )

    direccion = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    contacto_emergencia = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    telefono_emergencia = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    antecedentes_medicos = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": CLASE,
                "rows": 4,
            }
        ),
    )

    def __init__(
        self,
        *args,
        usuario_actual=None,
        incluir_antecedentes=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.usuario_actual = usuario_actual

        if not incluir_antecedentes:
            self.fields.pop("antecedentes_medicos")

    def clean_email(self):
        correo = self.cleaned_data["email"].strip().lower()

        existentes = User.objects.filter(
            email__iexact=correo
        )

        if self.usuario_actual is not None:
            existentes = existentes.exclude(
                pk=self.usuario_actual.pk
            )

        if existentes.exists():
            raise ValidationError(
                "Este correo ya está registrado."
            )

        return correo

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data["fecha_nacimiento"]

        if fecha and fecha > timezone.localdate():
            raise ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )

        return fecha


class RegistrarPacienteForm(DatosPacienteForm):

    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"class": CLASE}),
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": CLASE}),
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": CLASE}),
    )

    def clean_username(self):
        nombre_usuario = self.cleaned_data["username"].strip()

        if User.objects.filter(
            username__iexact=nombre_usuario
        ).exists():
            raise ValidationError(
                "Este nombre de usuario ya existe."
            )

        return nombre_usuario

    def clean(self):
        datos = super().clean()

        password1 = datos.get("password1")
        password2 = datos.get("password2")

        if password1 and password2:

            if password1 != password2:
                self.add_error(
                    "password2",
                    "Las contraseñas no coinciden.",
                )

            else:
                usuario = User(
                    username=datos.get("username", ""),
                    first_name=datos.get("nombre", ""),
                    last_name=datos.get("apellidos", ""),
                    email=datos.get("email", ""),
                )

                try:
                    validate_password(
                        password1,
                        user=usuario,
                    )

                except ValidationError as error:
                    self.add_error("password1", error)

        return datos


class EditarPacienteForm(DatosPacienteForm):
    pass
