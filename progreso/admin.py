from django.contrib import admin

from .models import Progreso


@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = (
        "consulta",
        "nivel_dolor",
        "fecha_registro",
    )

    search_fields = (
        "consulta__cita__paciente__usuario__usuario__username",
        "consulta__cita__paciente__usuario__usuario__first_name",
        "consulta__cita__paciente__usuario__usuario__last_name",
    )

    ordering = (
        "-fecha_registro",
    )