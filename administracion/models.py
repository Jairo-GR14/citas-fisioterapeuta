from django.db import models


class RegistroActividad(models.Model):
    usuario = models.ForeignKey(
        "usuarios.PerfilUsuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actividades",
    )

    accion = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField(
        blank=True,
    )

    modulo = models.CharField(
        max_length=100,
        blank=True,
    )

    fecha = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.accion} - {self.fecha}"