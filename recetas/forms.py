from django import forms

from .models import Receta


class RecetaForm(forms.ModelForm):

    class Meta:
        model = Receta

        fields = [
            "indicaciones",
            "ejercicios",
            "repeticiones",
            "frecuencia",
            "duracion",
            "recomendaciones",
            "restricciones",
        ]

        labels = {
            "indicaciones": "Indicaciones generales",
            "ejercicios": "Ejercicios indicados",
            "repeticiones": "Repeticiones",
            "frecuencia": "Frecuencia",
            "duracion": "Duración",
            "recomendaciones": "Recomendaciones",
            "restricciones": "Restricciones",
        }

        widgets = {

            # INDICACIONES
            "indicaciones": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 4,
                    "placeholder": (
                        "Escribe las indicaciones para el paciente"
                    ),
                }
            ),

            # EJERCICIOS
            "ejercicios": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 4,
                    "placeholder": (
                        "Describe los ejercicios que debe realizar"
                    ),
                }
            ),

            # REPETICIONES
            "repeticiones": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "placeholder": (
                        "Ej. 3 series de 10 repeticiones"
                    ),
                }
            ),

            # FRECUENCIA
            "frecuencia": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "placeholder": (
                        "Ej. 2 veces al día"
                    ),
                }
            ),

            # DURACIÓN
            "duracion": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "placeholder": (
                        "Ej. Durante 4 semanas"
                    ),
                }
            ),

            # RECOMENDACIONES
            "recomendaciones": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 3,
                    "placeholder": (
                        "Recomendaciones adicionales"
                    ),
                }
            ),

            # RESTRICCIONES
            "restricciones": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 3,
                    "placeholder": (
                        "Actividades o movimientos que debe evitar"
                    ),
                }
            ),
        }