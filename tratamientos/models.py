from django.db import models


class Tratamiento(models.Model):
    consulta = models.ForeignKey(
        "consultas.Consulta",
        on_delete=models.CASCADE,
        related_name="tratamientos",
    )

    nombre = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField(
        blank=True,
    )

    objetivo = models.TextField(
        blank=True,
    )

    fecha_inicio = models.DateField(
        null=True,
        blank=True,
    )

    fecha_fin = models.DateField(
        null=True,
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
        return self.nombre