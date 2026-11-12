
from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError

from .models import HorarioDisponible


class HorarioDisponibleForm(forms.ModelForm):

    class Meta:
        model = HorarioDisponible

        fields = [
            "dia_semana",
            "hora_inicio",
            "hora_fin",
            "activo",
        ]

        widgets = {
            "dia_semana": forms.Select(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                }
            ),

            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                },
            ),

            "hora_fin": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                },
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "h-5 w-5",
                }
            ),
        }

    def __init__(self, *args, fisioterapeuta, **kwargs):
        super().__init__(*args, **kwargs)

        self.fisioterapeuta = fisioterapeuta

        self.fields["hora_inicio"].input_formats = [
            "%H:%M",
            "%H:%M:%S",
        ]

        self.fields["hora_fin"].input_formats = [
            "%H:%M",
            "%H:%M:%S",
        ]

    def clean(self):
        datos = super().clean()

        dia = datos.get("dia_semana")
        inicio = datos.get("hora_inicio")
        fin = datos.get("hora_fin")
        activo = datos.get("activo", False)

        if dia is None or inicio is None or fin is None:
            return datos

        if fin <= inicio:
            raise ValidationError(
                "La hora de fin debe ser posterior a la de inicio."
            )

        minutos = (
            datetime.combine(date.today(), fin)
            - datetime.combine(date.today(), inicio)
        ).total_seconds() / 60

        if minutos < 60 or minutos % 60 != 0:
            raise ValidationError(
                "La jornada debe durar al menos 60 minutos "
                "y estar dividida en bloques completos de una hora."
            )

        if activo:

            if not (
                self.fisioterapeuta.activo
                and self.fisioterapeuta.usuario.activo
                and self.fisioterapeuta.usuario.usuario.is_active
            ):
                raise ValidationError(
                    "No puedes activar horarios de un fisioterapeuta inactivo."
                )

            otros = HorarioDisponible.objects.filter(
                fisioterapeuta=self.fisioterapeuta,
                dia_semana=dia,
                activo=True,
                hora_inicio__lt=fin,
                hora_fin__gt=inicio,
            )

            if self.instance.pk:
                otros = otros.exclude(
                    pk=self.instance.pk
                )

            if otros.exists():
                raise ValidationError(
                    "Esta jornada se traslapa con otro horario activo."
                )

        return datos
