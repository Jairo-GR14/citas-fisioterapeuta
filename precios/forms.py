
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
            "activo",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "placeholder": "Nombre del servicio",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "rows": 4,
                    "placeholder": "Describe el servicio",
                }
            ),

            "precio_base": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "h-5 w-5 rounded border-slate-300",
                }
            ),
        }

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
