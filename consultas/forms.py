from django import forms

from .models import Consulta


class ConsultaForm(forms.ModelForm):

    class Meta:
        model = Consulta

        fields = [
            "valoracion_inicial",
            "diagnostico",
            "informacion_atencion",
            "observaciones",
        ]

        widgets = {
            "valoracion_inicial": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                    "rows": 4,
                    "placeholder": "Describe la valoración inicial",
                }
            ),

            "diagnostico": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                    "rows": 4,
                    "placeholder": "Escribe el diagnóstico",
                }
            ),

            "informacion_atencion": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                    "rows": 4,
                    "placeholder": "Describe la atención realizada",
                }
            ),

            "observaciones": forms.Textarea(
                attrs={
                    "class": "w-full rounded-xl border border-slate-300 p-3",
                    "rows": 3,
                    "placeholder": "Observaciones adicionales",
                }
            ),
        }