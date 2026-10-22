from django.db import models


class Fisioterapeuta(models.Model):
    usuario = models.OneToOneField(
        "usuarios.PerfilUsuario",
        on_delete=models.CASCADE,
        related_name="fisioterapeuta",
    )

    especialidad = models.CharField(
        max_length=150,
        blank=True,
    )

    cedula_profesional = models.CharField(
        max_length=50,
        blank=True,
    )

    descripcion = models.TextField(
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

## Horarios ##
class HorarioDisponible(models.Model):

    class DiaSemana(models.IntegerChoices):
        LUNES = 1, "Lunes"
        MARTES = 2, "Martes"
        MIERCOLES = 3, "Miércoles"
        JUEVES = 4, "Jueves"
        VIERNES = 5, "Viernes"
        SABADO = 6, "Sábado"
        DOMINGO = 7, "Domingo"

    fisioterapeuta = models.ForeignKey(
        Fisioterapeuta,
        on_delete=models.CASCADE,
        related_name="horarios",
    )

    dia_semana = models.PositiveSmallIntegerField(
        choices=DiaSemana.choices,
    )

    hora_inicio = models.TimeField()

    hora_fin = models.TimeField()

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self):
        return (
            f"{self.fisioterapeuta} - "
            f"{self.get_dia_semana_display()} "
            f"{self.hora_inicio} a {self.hora_fin}"
        )