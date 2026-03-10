# turnos/google_calendar.py

from datetime import datetime, timedelta, time
from googleapiclient.discovery import build
from django.utils import timezone


class GoogleCalendarError(Exception):
    pass


def get_calendar_service(credentials):
    """
    credentials: credenciales OAuth válidas del usuario/consultorio.
    """
    try:
        service = build("calendar", "v3", credentials=credentials)
        return service
    except Exception as e:
        raise GoogleCalendarError(f"No se pudo construir el cliente de Google Calendar: {e}")


# ==========================================================
# CONSULTA DE DISPONIBILIDAD (FREEBUSY)
# ==========================================================

def consultar_bloques_ocupados(credentials, calendar_id, fecha, tz_name="America/Argentina/Buenos_Aires"):
    """
    Devuelve una lista de bloques ocupados en una fecha.

    Retorna:
    [
        (datetime_inicio, datetime_fin),
        (datetime_inicio, datetime_fin),
    ]
    """

    service = get_calendar_service(credentials)

    tz = timezone.get_current_timezone()

    inicio_dia = timezone.make_aware(datetime.combine(fecha, time(0, 0)), tz)
    fin_dia = timezone.make_aware(datetime.combine(fecha, time(23, 59, 59)), tz)

    body = {
        "timeMin": inicio_dia.isoformat(),
        "timeMax": fin_dia.isoformat(),
        "timeZone": tz_name,
        "items": [{"id": calendar_id}],
    }

    try:
        result = service.freebusy().query(body=body).execute()
    except Exception as e:
        raise GoogleCalendarError(f"Error consultando disponibilidad en Google Calendar: {e}")

    calendars = result.get("calendars", {})
    calendar_data = calendars.get(calendar_id, {})
    busy = calendar_data.get("busy", [])

    bloques = []

    for item in busy:

        start_dt = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))

        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt, tz)
        else:
            start_dt = start_dt.astimezone(tz)

        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt, tz)
        else:
            end_dt = end_dt.astimezone(tz)

        bloques.append((start_dt, end_dt))

    return bloques


# ==========================================================
# GENERAR HORARIOS DISPONIBLES
# ==========================================================

def generar_slots_disponibles(
    *,
    fecha,
    bloques_ocupados,
    duracion_minutos=30,
    hora_inicio_jornada=9,
    hora_fin_jornada=18,
    intervalo_minutos=30,
):
    """
    Genera slots disponibles dentro de una jornada laboral.

    Retorna lista de strings:

    [
        "09:00",
        "09:30",
        "10:00",
    ]
    """

    tz = timezone.get_current_timezone()

    inicio_jornada = timezone.make_aware(
        datetime.combine(fecha, time(hora_inicio_jornada, 0)),
        tz,
    )

    fin_jornada = timezone.make_aware(
        datetime.combine(fecha, time(hora_fin_jornada, 0)),
        tz,
    )

    slots = []

    cursor = inicio_jornada
    duracion = timedelta(minutes=duracion_minutos)
    paso = timedelta(minutes=intervalo_minutos)

    while cursor + duracion <= fin_jornada:

        candidato_inicio = cursor
        candidato_fin = cursor + duracion

        solapa = False

        for ocupado_inicio, ocupado_fin in bloques_ocupados:

            if candidato_inicio < ocupado_fin and candidato_fin > ocupado_inicio:
                solapa = True
                break

        if not solapa:
            slots.append(candidato_inicio.strftime("%H:%M"))

        cursor += paso

    return slots


# ==========================================================
# CREACIÓN DE EVENTO EN GOOGLE CALENDAR
# ==========================================================

def build_event_payload(turno):
    """
    Construye el payload para crear el evento en Google Calendar.
    """

    return {
        "summary": f"Turno odontológico - {turno.paciente.nombre} {turno.paciente.apellido}",
        "description": (
            f"Paciente: {turno.paciente.nombre} {turno.paciente.apellido}\n"
            f"Email: {turno.paciente.email}\n"
            f"Teléfono: {turno.paciente.telefono}\n"
            f"Documento: {turno.paciente.documento}\n"
            f"Motivo: {turno.motivo}\n"
            f"Observaciones: {turno.observaciones}\n"
            f"Turno ID interno: {turno.id}"
        ),
        "start": {
            "dateTime": turno.fecha_inicio_datetime.isoformat(),
            "timeZone": "America/Argentina/Buenos_Aires",
        },
        "end": {
            "dateTime": turno.fecha_fin_datetime.isoformat(),
            "timeZone": "America/Argentina/Buenos_Aires",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 1440},
                {"method": "popup", "minutes": 1440},
            ],
        },
        "extendedProperties": {
            "private": {
                "turno_id": str(turno.id),
                "profesional_id": str(turno.profesional_id),
                "paciente_id": str(turno.paciente_id),
            }
        },
    }


def crear_evento_google(turno, credentials, calendar_id="primary"):
    """
    Crea el evento en Google Calendar y devuelve el event_id.
    """

    service = get_calendar_service(credentials)

    event_body = build_event_payload(turno)

    try:
        result = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=event_body,
                sendUpdates="all",
            )
            .execute()
        )

        return result["id"]

    except Exception as e:
        raise GoogleCalendarError(f"Error al crear evento en Google Calendar: {e}")