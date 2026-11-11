
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from fisioterapeutas.models import HorarioDisponible

from .models import Cita


# FORMULARIO DE CITA

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
                attrs={"rows": 3},
            ),
        }


    # VALIDAR HORARIOS

    def clean(self):
        cleaned_data = super().clean()

        fisioterapeuta = cleaned_data.get("fisioterapeuta")
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        if not all([fisioterapeuta, fecha, hora]):
            return cleaned_data

        if not fisioterapeuta.activo:
            raise ValidationError(
                "El fisioterapeuta seleccionado no está activo."
            )

        if not fisioterapeuta.usuario.activo:
            raise ValidationError(
                "El perfil del fisioterapeuta no está activo."
            )

        # FECHA Y HORA
        inicio = timezone.make_aware(
            datetime.combine(fecha, hora),
            timezone.get_current_timezone(),
        )

        ahora = timezone.localtime()

        if inicio <= ahora:
            raise ValidationError(
                "No puedes agendar una cita en una fecha "
                "u hora pasada."
            )

        # DURACIÓN DE LA CITA
        duracion = timedelta(minutes=60)
        fin = inicio + duracion

        # HORARIO DEL FISIOTERAPEUTA
        jornadas = HorarioDisponible.objects.filter(
            fisioterapeuta=fisioterapeuta,
            dia_semana=fecha.isoweekday(),
            activo=True,
        )

        horario_valido = False

        for jornada in jornadas:
            inicio_jornada = timezone.make_aware(
                datetime.combine(
                    fecha,
                    jornada.hora_inicio,
                ),
                timezone.get_current_timezone(),
            )

            fin_jornada = timezone.make_aware(
                datetime.combine(
                    fecha,
                    jornada.hora_fin,
                ),
                timezone.get_current_timezone(),
            )

            if not (
                inicio_jornada <= inicio
                and fin <= fin_jornada
            ):
                continue

            # BLOQUES DE 60 MINUTOS
            diferencia = inicio - inicio_jornada

            if diferencia.total_seconds() % 3600 == 0:
                horario_valido = True
                break

        if not horario_valido:
            raise ValidationError(
                "El horario seleccionado no pertenece "
                "a la jornada disponible del fisioterapeuta."
            )

        # CITAS OCUPADAS
        citas_ocupadas = Cita.objects.filter(
            fisioterapeuta=fisioterapeuta,
            fecha=fecha,
        ).exclude(
            estado=Cita.Estado.CANCELADA
        )

        # EXCLUIR LA CITA ACTUAL AL EDITAR
        if self.instance.pk:
            citas_ocupadas = citas_ocupadas.exclude(
                pk=self.instance.pk
            )

        for cita in citas_ocupadas:
            inicio_ocupado = timezone.make_aware(
                datetime.combine(
                    cita.fecha,
                    cita.hora,
                ),
                timezone.get_current_timezone(),
            )

            fin_ocupado = inicio_ocupado + duracion

            if (
                inicio < fin_ocupado
                and inicio_ocupado < fin
            ):
                raise ValidationError(
                    "Este fisioterapeuta ya tiene una cita "
                    "en ese horario. Selecciona otro."
                )

        return cleaned_data


# EDITAR CITA

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
