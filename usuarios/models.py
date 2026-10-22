from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):

    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        RECEPCIONISTA = "RECEPCIONISTA", "Recepcionista"
        FISIOTERAPEUTA = "FISIOTERAPEUTA", "Fisioterapeuta"
        PACIENTE = "PACIENTE", "Paciente"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"
