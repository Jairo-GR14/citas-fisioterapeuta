from django.contrib import admin

from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = (
        "cita",
        "fecha_inicio",
        "fecha_finalizacion",
        "fecha_creacion",
    )

    search_fields = (
        "cita__paciente__usuario__usuario__username",
        "cita__paciente__usuario__usuario__first_name",
        "cita__paciente__usuario__usuario__last_name",
    )

    ordering = (
        "-fecha_creacion",
    )