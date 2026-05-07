# turnos/services.py
from django.db.models import Q
from .models import Turno


def existe_solapamiento(profesional, fecha, hora_inicio, hora_fin, excluir_turno_id=None) -> bool:
    qs = Turno.objects.filter(
        profesional=profesional,
        fecha=fecha,
        estado=Turno.ESTADO_CONFIRMADO,
    )

    if excluir_turno_id:
        qs = qs.exclude(id=excluir_turno_id)

    # Solapamiento:
    # nuevo_inicio < existente_fin AND nuevo_fin > existente_inicio
    qs = qs.filter(
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    )

    return qs.exists()