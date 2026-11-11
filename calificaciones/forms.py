from django import forms

from .models import Calificacion


class CalificacionForm(forms.ModelForm):

    puntuacion = forms.TypedChoiceField(
        label="Califica tu experiencia",
        choices=[
            (5, "★★★★★ - Excelente"),
            (4, "★★★★☆ - Muy buena"),
            (3, "★★★☆☆ - Buena"),
            (2, "★★☆☆☆ - Regular"),
            (1, "★☆☆☆☆ - Mala"),
        ],
        coerce=int,
        widget=forms.RadioSelect(
            attrs={
                "class": "accent-emerald-600",
            }
        ),
        error_messages={
            "required": "Selecciona una calificación.",
            "invalid_choice": "Selecciona una puntuación válida.",
        },
    )

    class Meta:
        model = Calificacion

        fields = [
            "puntuacion",
            "comentario",
        ]

        labels = {
            "comentario": "Comentario sobre la atención",
        }

        widgets = {
            "comentario": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-xl border "
                        "border-slate-300 px-4 py-3 "
                        "focus:border-blue-500 "
                        "focus:outline-none"
                    ),
                    "rows": 5,
                    "placeholder": (
                        "Cuéntanos cómo fue tu experiencia "
                        "durante la atención."
                    ),
                }
            ),
        }

    def clean_puntuacion(self):

        puntuacion = self.cleaned_data.get("puntuacion")

        if puntuacion not in [1, 2, 3, 4, 5]:
            raise forms.ValidationError(
                "La calificación debe estar entre 1 y 5 estrellas."
            )

        return puntuacion