from django import forms

from .models import Progreso


class ProgresoForm(forms.ModelForm):

    class Meta:
        model = Progreso

        fields = [
            "movilidad",
            "nivel_dolor",
            "ejercicios_realizados",
            "avances",
            "observaciones",
            "recomendaciones",
        ]

        labels = {
            "movilidad": "Movilidad del paciente",
            "nivel_dolor": "Nivel de dolor",
            "ejercicios_realizados": "Ejercicios realizados",
            "avances": "Avances observados",
            "observaciones": "Observaciones",
            "recomendaciones": "Recomendaciones",
        }

        widgets = {

            # MOVILIDAD
            "movilidad": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 3,
                    "placeholder": (
                        "Describe la movilidad actual del paciente"
                    ),
                }
            ),

            # NIVEL DE DOLOR
            "nivel_dolor": forms.NumberInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "placeholder": "Nivel de dolor de 0 a 10",
                }
            ),

            # EJERCICIOS REALIZADOS
            "ejercicios_realizados": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 4,
                    "placeholder": (
                        "Describe los ejercicios realizados"
                    ),
                }
            ),

            # AVANCES
            "avances": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 4,
                    "placeholder": (
                        "Registra los avances del paciente"
                    ),
                }
            ),

            # OBSERVACIONES
            "observaciones": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3"
                    ),
                    "rows": 3,
                    "placeholder": (
                        "Observaciones adicionales"
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
                        "Recomendaciones para el paciente"
                    ),
                }
            ),
        }

    # ==========================================
    # VALIDACIÓN DEL NIVEL DE DOLOR
    # ==========================================

    def clean_nivel_dolor(self):

        nivel_dolor = self.cleaned_data.get(
            "nivel_dolor"
        )

        if nivel_dolor is not None:

            if not 0 <= nivel_dolor <= 10:

                raise forms.ValidationError(
                    "El nivel de dolor debe estar "
                    "entre 0 y 10."
                )

        return nivel_dolor