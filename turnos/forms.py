# turnos/forms.py
from datetime import datetime, timedelta
from django import forms
from .models import Profesional


class SolicitudTurnoForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    apellido = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    telefono = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    documento = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    profesional = forms.ModelChoiceField(
        queryset=Profesional.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    fecha = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    hora_inicio = forms.TimeField(
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=[("", "Seleccionar hora")]
        )
    )

    motivo = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4})
    )

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha < datetime.now().date():
            raise forms.ValidationError("No podés solicitar un turno en una fecha pasada.")
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        profesional = cleaned_data.get("profesional")

        if hora_inicio and profesional:
            dt = datetime.combine(datetime.today(), hora_inicio)
            hora_fin = (dt + timedelta(minutes=profesional.duracion_turno_minutos)).time()
            cleaned_data["hora_fin"] = hora_fin

        return cleaned_data
    
    