
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Servicio


class ServicioForm(forms.ModelForm):

    class Meta:
        model = Servicio

        fields = [
            "nombre",
            "descripcion",
            "precio_base",
            "duracion_minutos",
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "placeholder": "Nombre del servicio",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 4,
                    "placeholder": "Describe el servicio",
                }
            ),

            "precio_base": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),

            "duracion_minutos": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "type": "number",
                    "min": "15",
                    "max": "480",
                    "step": "1",
                    "placeholder": "Ej. 45, 60, 90",
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": (
                        "h-5 w-5 rounded "
                        "border-slate-300"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mantener compatibilidad con formularios y
        # pruebas anteriores que todavía no envían
        # la duración del servicio.
        self.fields["duracion_minutos"].required = False

        self.fields["duracion_minutos"].help_text = (
            "Entre 15 y 480 minutos. "
            "Si queda vacío, se usan 60 minutos "
            "para servicios nuevos."
        )

    def clean_duracion_minutos(self):

        duracion = self.cleaned_data.get(
            "duracion_minutos"
        )

        # Si se edita un servicio sin enviar una nueva
        # duración, conservar la duración existente.
        if duracion is None:

            if self.instance.pk:
                return self.instance.duracion_minutos

            return 60

        return duracion

    def clean_nombre(self):

        nombre = self.cleaned_data["nombre"].strip()

        if not nombre:
            raise ValidationError(
                "Debes escribir el nombre del servicio."
            )

        existe = Servicio.objects.filter(
            nombre__iexact=nombre
        )

        if self.instance.pk:
            existe = existe.exclude(
                pk=self.instance.pk
            )

        if existe.exists():
            raise ValidationError(
                "Ya existe un servicio con ese nombre."
            )

        return nombre

    def clean_precio_base(self):

        precio = self.cleaned_data["precio_base"]

        if precio is None or precio < Decimal("0.01"):
            raise ValidationError(
                "El precio debe ser mayor que cero."
            )

        return precio
