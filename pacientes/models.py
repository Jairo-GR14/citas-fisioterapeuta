from django.db import models


class Paciente(models.Model):
    usuario = models.OneToOneField(
        "usuarios.PerfilUsuario",
        on_delete=models.CASCADE,
        related_name="paciente",
    )

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
    )

    direccion = models.CharField(
        max_length=255,
        blank=True,
    )

    contacto_emergencia = models.CharField(
        max_length=150,
        blank=True,
    )

    telefono_emergencia = models.CharField(
        max_length=20,
        blank=True,
    )

    antecedentes_medicos = models.TextField(
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        nombre = self.usuario.usuario.get_full_name().strip()

        if nombre:
            return nombre

        return self.usuario.usuario.username