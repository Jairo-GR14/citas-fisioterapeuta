
from decimal import Decimal

from django import forms

from citas.models import Cita

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

    # Utilizar la misma precisión que el campo
    # costo_final del modelo Cita.
    _campo_costo = Cita._meta.get_field("costo_final")

    costo_final = forms.DecimalField(
        label="Costo final de la atención (MXN)",
        required=True,
        max_digits=_campo_costo.max_digits,
        decimal_places=_campo_costo.decimal_places,
        min_value=Decimal("0.00"),
        help_text=(
            "Escribe el costo final de la atención. "
            "Si fue gratuita, registra 0.00."
        ),
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "w-full rounded-xl border "
                    "border-slate-300 px-4 py-3"
                ),
                "placeholder": "Ej. 400.00",
                "min": "0",
                "step": "0.01",
                "inputmode": "decimal",
            }
        ),
    )
