from django import forms

from .models import Tratamiento


class TratamientoForm(forms.ModelForm):

    class Meta:
        model = Tratamiento

        fields = [
            "nombre",
            "descripcion",
            "objetivo",
            "fecha_inicio",
            "fecha_fin",
            "activo",
        ]

        labels = {
            "nombre": "Nombre del tratamiento",
            "descripcion": "Descripción del tratamiento",
            "objetivo": "Objetivo del tratamiento",
            "fecha_inicio": "Fecha de inicio",
            "fecha_fin": "Fecha de finalización",
            "activo": "Tratamiento activo",
        }

        widgets = {

            "nombre": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "placeholder": "Ej. Rehabilitación de rodilla",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "rows": 4,
                    "placeholder": "Describe el tratamiento",
                }
            ),

            "objetivo": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                    "rows": 3,
                    "placeholder": "Objetivos que se desean alcanzar",
                }
            ),

            "fecha_inicio": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                }
            ),

            "fecha_fin": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-slate-300 text-blue-600",
                }
            ),
        }

    def clean(self):
        datos = super().clean()

        fecha_inicio = datos.get("fecha_inicio")
        fecha_fin = datos.get("fecha_fin")

        if fecha_inicio and fecha_fin:

            if fecha_fin < fecha_inicio:
                self.add_error(
                    "fecha_fin",
                    "La fecha de finalización no puede "
                    "ser anterior a la fecha de inicio.",
                )

        return datos