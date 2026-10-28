from django.contrib import admin

from .models import Calificacion


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        "cita",
        "puntuacion",
        "fecha_creacion",
    )

    list_filter = (
        "puntuacion",
    )

    search_fields = (
        "comentario",
        "cita__paciente__usuario__usuario__username",
        "cita__paciente__usuario__usuario__first_name",
        "cita__paciente__usuario__usuario__last_name",
    )

    ordering = (
        "-fecha_creacion",
    )