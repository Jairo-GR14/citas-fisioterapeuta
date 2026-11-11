
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Cita


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita

        fields = [
            "paciente",
            "fisioterapeuta",
            "servicio",
            "motivo",
            "fecha",
            "hora",
            "observaciones",
        ]

        widgets = {
            "fecha": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "hora": forms.TimeInput(
                attrs={"type": "time"},
                format="%H:%M",
            ),
            "observaciones": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        fisioterapeuta = cleaned_data.get("fisioterapeuta")
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        if not all([fisioterapeuta, fecha, hora]):
            return cleaned_data

        if fecha < timezone.localdate():
            raise ValidationError(
                "No puedes agendar una cita en una fecha pasada."
            )

        if (
            fecha == timezone.localdate()
            and hora <= timezone.localtime().time().replace(tzinfo=None)
        ):
            raise ValidationError(
                "No puedes agendar una cita en una hora pasada."
            )

        citas_ocupadas = Cita.objects.filter(
            fisioterapeuta=fisioterapeuta,
            fecha=fecha,
            hora=hora,
        ).exclude(
            estado=Cita.Estado.CANCELADA
        )

        if self.instance.pk:
            citas_ocupadas = citas_ocupadas.exclude(
                pk=self.instance.pk
            )

        if citas_ocupadas.exists():
            raise ValidationError(
                "Este fisioterapeuta ya tiene una cita "
                "programada en ese horario."
            )

        return cleaned_data


class EditarCitaForm(CitaForm):
    class Meta(CitaForm.Meta):
        fields = [
            "fisioterapeuta",
            "servicio",
            "fecha",
            "hora",
            "motivo",
            "observaciones",
        ]
