
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from fisioterapeutas.models import Fisioterapeuta, HorarioDisponible
from pacientes.models import Paciente
from precios.models import Servicio

from .models import Cita, MotivoConsulta


class CitaForm(forms.ModelForm):
    """
    Formulario para reservar citas de 60 minutos.
    Valida horarios del fisioterapeuta y citas ocupadas.
    """

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "paciente" in self.fields:
            self.fields["paciente"].queryset = (
                Paciente.objects.filter(
                    activo=True,
                    usuario__activo=True,
                ).select_related("usuario__usuario")
            )

        self.fields["fisioterapeuta"].queryset = (
            Fisioterapeuta.objects.filter(
                activo=True,
                usuario__activo=True,
            ).select_related("usuario__usuario")
        )

        self.fields["servicio"].queryset = (
            Servicio.objects.filter(activo=True)
        )

        self.fields["motivo"].queryset = (
            MotivoConsulta.objects.filter(activo=True)
        )

    def clean(self):
        cleaned_data = super().clean()

        fisioterapeuta = cleaned_data.get("fisioterapeuta")
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        if not all((fisioterapeuta, fecha, hora)):
            return cleaned_data

        # Verificar que el fisioterapeuta esté activo.
        if (
            not fisioterapeuta.activo
            or not fisioterapeuta.usuario.activo
        ):
            raise ValidationError(
                "El fisioterapeuta seleccionado no está activo."
            )

        # Comprobar que la fecha no sea pasada.
        zona = timezone.get_current_timezone()

        inicio = timezone.make_aware(
            datetime.combine(fecha, hora),
            zona,
        )

        if inicio <= timezone.now():
            raise ValidationError(
                "No puedes agendar una cita en una fecha "
                "u hora pasada."
            )

        # Las citas duran 60 minutos.
        duracion = timedelta(minutes=60)
        fin = inicio + duracion

        # Buscar los horarios disponibles del fisioterapeuta.
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
                zona,
            )

            fin_jornada = timezone.make_aware(
                datetime.combine(
                    fecha,
                    jornada.hora_fin,
                ),
                zona,
            )

            if (
                inicio_jornada <= inicio
                and fin <= fin_jornada
            ):
                diferencia = inicio - inicio_jornada

                if diferencia.total_seconds() % 3600 == 0:
                    horario_valido = True
                    break

        if not horario_valido:
            raise ValidationError(
                "Selecciona un bloque de 60 minutos dentro "
                "de la jornada disponible del fisioterapeuta."
            )

        # Evitar citas que se traslapen.
        citas_ocupadas = Cita.objects.filter(
            fisioterapeuta=fisioterapeuta,
            fecha=fecha,
        ).exclude(
            estado=Cita.Estado.CANCELADA
        )

        # Al editar, excluir la propia cita.
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
                zona,
            )

            fin_ocupado = inicio_ocupado + duracion

            if (
                inicio < fin_ocupado
                and inicio_ocupado < fin
            ):
                raise ValidationError(
                    "Este fisioterapeuta ya tiene una cita "
                    "en ese horario."
                )

        return cleaned_data


class EditarCitaForm(CitaForm):
    """
    Permite modificar una cita sin cambiar el paciente.
    """

    class Meta(CitaForm.Meta):
        fields = [
            "fisioterapeuta",
            "servicio",
            "fecha",
            "hora",
            "motivo",
            "observaciones",
        ]
