
from decimal import Decimal

from django import forms

from .models import Consulta


# =========================================================
# FORMULARIO DE VALORACIÓN CLÍNICA
# =========================================================

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


# =========================================================
# FORMULARIO PARA FINALIZAR CONSULTA
# =========================================================

class FinalizarConsultaForm(forms.Form):

    costo_final = forms.DecimalField(
        label="Costo final de la atención (MXN)",
        required=True,
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.00"),
        error_messages={
            "required": "Debes registrar el costo final.",
            "invalid": "Ingresa un importe válido.",
            "min_value": "El costo final no puede ser negativo.",
        },
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "w-full rounded-xl border border-slate-300 "
                    "bg-white px-4 py-3 text-lg font-semibold "
                    "text-slate-900 focus:border-emerald-500 "
                    "focus:outline-none"
                ),
                "step": "0.01",
                "min": "0",
                "inputmode": "decimal",
                "placeholder": "Ej. 400.00",
            }
        ),
    )
