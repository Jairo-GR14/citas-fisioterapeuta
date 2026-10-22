from django.db import models


class Servicio(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    precio_base = models.DecimalField(
        max_digits=8,
        decimal_places=2,
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

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio_base}"