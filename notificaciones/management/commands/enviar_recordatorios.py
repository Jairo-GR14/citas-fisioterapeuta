
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from citas.models import Cita
from notificaciones.models import Notificacion


class Command(BaseCommand):

    help = (
        "Genera recordatorios internos de "
        "las citas del día siguiente."
    )

    def handle(self, *args, **options):

        manana = (
            timezone.localdate()
            + timedelta(days=1)
        )

        citas = Cita.objects.filter(
            fecha=manana,
            estado__in=(
                Cita.Estado.PROGRAMADA,
                Cita.Estado.CONFIRMADA,
            ),
        ).select_related(
            "paciente__usuario",
            "fisioterapeuta__usuario",
            "servicio",
        )

        total = 0

        for cita in citas:

            titulo = (
                f"Recordatorio de la cita #{cita.pk}"
            )

            mensaje = (
                f"Tienes una cita de "
                f"{cita.servicio.nombre} mañana "
                f"{cita.fecha:%d/%m/%Y} "
                f"a las {cita.hora:%H:%M}."
            )

            destinatarios = {
                cita.paciente.usuario_id,
                cita.fisioterapeuta.usuario_id,
            }

            for perfil_id in destinatarios:

                _, creada = (
                    Notificacion.objects.get_or_create(
                        usuario_id=perfil_id,
                        tipo=Notificacion.Tipo.RECORDATORIO,
                        titulo=titulo,
                        mensaje=mensaje,
                    )
                )

                total += int(creada)

        self.stdout.write(
            self.style.SUCCESS(
                f"Recordatorios nuevos: {total}"
            )
        )
