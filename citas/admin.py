from django.contrib import admin

from .models import Cita, MotivoConsulta


@admin.register(MotivoConsulta)
class MotivoConsultaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "activo",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "nombre",
    )


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "fisioterapeuta",
        "servicio",
        "fecha",
        "hora",
        "estado",
        "costo_estimado",
        "costo_final",
    )

    list_filter = (
        "estado",
        "fecha",
        "servicio",
    )

    search_fields = (
        "paciente__usuario__usuario__username",
        "paciente__usuario__usuario__first_name",
        "paciente__usuario__usuario__last_name",
        "fisioterapeuta__usuario__usuario__first_name",
        "fisioterapeuta__usuario__usuario__last_name",
    )

    ordering = (
        "-fecha",
        "-hora",
    )