
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from fisioterapeutas.models import (
    Fisioterapeuta,
    HorarioDisponible,
)
from pacientes.models import Paciente
from precios.models import Servicio

from .models import Cita, MotivoConsulta


class CitaForm(forms.ModelForm):
    """
    Valida la jornada y utiliza la duración
    reservada para cada cita.
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

    def _duracion_para_reserva(self, servicio):
        """
        Una cita nueva utiliza la duración actual
        del servicio.

        Al editar sin cambiar de servicio,
        conserva la duración reservada.

        Si cambia el servicio, utiliza la
        duración del nuevo servicio.
        """

        if self.instance.pk:
            anterior = (
                Cita.objects.filter(
                    pk=self.instance.pk
                )
                .values(
                    "servicio_id",
                    "duracion_minutos",
                )
                .first()
            )

            if (
                anterior
                and anterior["servicio_id"] == servicio.pk
            ):
                return anterior["duracion_minutos"]

        return servicio.duracion_minutos

    def clean(self):
        cleaned_data = super().clean()

        fisioterapeuta = cleaned_data.get(
            "fisioterapeuta"
        )
        servicio = cleaned_data.get("servicio")
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora")

        if not all(
            (fisioterapeuta, servicio, fecha, hora)
        ):
            return cleaned_data

        # Comprobar que el fisioterapeuta esté activo.
        if (
            not fisioterapeuta.activo
            or not fisioterapeuta.usuario.activo
        ):
            raise ValidationError(
                "El fisioterapeuta seleccionado "
                "no está activo."
            )

        # Obtener la duración correspondiente.
        duracion_minutos = (
            self._duracion_para_reserva(servicio)
        )

        if not 15 <= duracion_minutos <= 480:
            raise ValidationError(
                "La duración del servicio debe "
                "estar entre 15 y 480 minutos."
            )

        zona = timezone.get_current_timezone()

        inicio = timezone.make_aware(
            datetime.combine(fecha, hora),
            zona,
        )

        # Rechazar fechas y horas pasadas.
        if inicio <= timezone.now():
            raise ValidationError(
                "No puedes agendar una cita en una "
                "fecha u hora pasada."
            )

        # Calcular el final real de la cita.
        fin = inicio + timedelta(
            minutes=duracion_minutos
        )

        # Consultar las jornadas del fisioterapeuta.
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

            # La cita completa debe caber
            # dentro de una jornada.
            if (
                inicio_jornada <= inicio
                and fin <= fin_jornada
            ):

                diferencia = (
                    inicio - inicio_jornada
                )

                # Mantener temporalmente los inicios
                # por hora, como en el sistema original.
                if (
                    diferencia.total_seconds()
                    % 3600 == 0
                ):
                    horario_valido = True
                    break

        if not horario_valido:
            raise ValidationError(
                "La cita debe iniciar en un bloque "
                "horario de la jornada y terminar "
                "antes de que finalice la disponibilidad "
                "del fisioterapeuta."
            )

        # Buscar citas que puedan ocupar el intervalo.
        citas_ocupadas = (
            Cita.objects.filter(
                fisioterapeuta=fisioterapeuta,
                fecha=fecha,
            )
            .exclude(
                estado=Cita.Estado.CANCELADA
            )
        )

        # No comparar una cita consigo misma
        # durante su edición.
        if self.instance.pk:
            citas_ocupadas = (
                citas_ocupadas.exclude(
                    pk=self.instance.pk
                )
            )

        for cita in citas_ocupadas:

            inicio_ocupado = timezone.make_aware(
                datetime.combine(
                    cita.fecha,
                    cita.hora,
                ),
                zona,
            )

            # Cada cita existente utiliza
            # su propia duración reservada.
            fin_ocupado = (
                inicio_ocupado
                + timedelta(
                    minutes=cita.duracion_minutos
                )
            )

            # Dos intervalos se traslapan si
            # ambos comienzan antes de que
            # termine el otro.
            if (
                inicio < fin_ocupado
                and inicio_ocupado < fin
            ):
                raise ValidationError(
                    "Este fisioterapeuta ya tiene "
                    "una cita que se traslapa con "
                    "el horario solicitado."
                )

        return cleaned_data

    def save(self, commit=True):
        """
        Guardar la duración correspondiente
        junto con los datos de la cita.

        Compatible con las vistas que utilizan
        formulario.save(commit=False).
        """

        cita = super().save(commit=False)

        servicio = self.cleaned_data.get(
            "servicio"
        )

        if servicio is not None:
            cita.duracion_minutos = (
                self._duracion_para_reserva(
                    servicio
                )
            )

        if commit:
            cita.save()
            self.save_m2m()

        return cita


class EditarCitaForm(CitaForm):
    """
    Permite modificar una cita
    sin cambiar el paciente.
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
