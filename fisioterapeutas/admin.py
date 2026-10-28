from django.contrib import admin

from .models import Fisioterapeuta, HorarioDisponible


@admin.register(Fisioterapeuta)
class FisioterapeutaAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "especialidad",
        "cedula_profesional",
        "activo",
        "fecha_registro",
    )

    list_filter = (
        "activo",
        "especialidad",
    )

    search_fields = (
        "usuario__usuario__username",
        "usuario__usuario__first_name",
        "usuario__usuario__last_name",
        "cedula_profesional",
    )


@admin.register(HorarioDisponible)
class HorarioDisponibleAdmin(admin.ModelAdmin):
    list_display = (
        "fisioterapeuta",
        "dia_semana",
        "hora_inicio",
        "hora_fin",
        "activo",
    )

    list_filter = (
        "dia_semana",
        "activo",
    )