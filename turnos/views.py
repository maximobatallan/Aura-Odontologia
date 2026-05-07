# turnos/views.py
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from .google_oauth import build_google_flow, credentials_to_dict, credentials_from_session
from .forms import SolicitudTurnoForm
from .models import Paciente, Turno, Profesional
from .tokens import generar_token_turno, validar_token_turno
from .services import existe_solapamiento
from .google_calendar import (
    crear_evento_google,
    GoogleCalendarError,
    consultar_bloques_ocupados,
    generar_slots_disponibles,
)
from .mailer import enviar_mail_profesional_nuevo_turno


def solicitar_turno(request):
    if request.method == "POST":
        form = SolicitudTurnoForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            paciente, _ = Paciente.objects.get_or_create(
                email=cd["email"],
                defaults={
                    "nombre": cd["nombre"],
                    "apellido": cd["apellido"],
                    "telefono": cd.get("telefono", ""),
                    "documento": cd.get("documento", ""),
                }
            )

            paciente.nombre = cd["nombre"]
            paciente.apellido = cd["apellido"]
            paciente.telefono = cd.get("telefono", "")
            paciente.documento = cd.get("documento", "")
            paciente.save()

            turno = Turno.objects.create(
                paciente=paciente,
                profesional=cd["profesional"],
                fecha=cd["fecha"],
                hora_inicio=cd["hora_inicio"],
                hora_fin=cd["hora_fin"],
                motivo=cd.get("motivo", ""),
                observaciones=cd.get("observaciones", ""),
                estado=Turno.ESTADO_PENDIENTE,
            )

            token = generar_token_turno(turno.id)
            turno.token = token
            turno.save(update_fields=["token"])

            try:
                enviar_mail_profesional_nuevo_turno(request, turno)
            except Exception as e:
                print("[TURNOS] ERROR enviando mail al profesional:", e)
                raise

            return redirect("turnos:pendiente")
    else:
        form = SolicitudTurnoForm()

    return render(request, "turnos/solicitar_turno.html", {"form": form})


def turno_pendiente(request):
    return render(request, "turnos/turno_pendiente.html")


def horarios_disponibles(request):
    profesional_id = request.GET.get("profesional_id")
    fecha_str = request.GET.get("fecha")

    if not profesional_id or not fecha_str:
        return JsonResponse(
            {"ok": False, "error": "Faltan profesional_id o fecha."},
            status=400
        )

    try:
        profesional = Profesional.objects.get(id=profesional_id, activo=True)
    except Profesional.DoesNotExist:
        return JsonResponse(
            {"ok": False, "error": "Profesional no encontrado."},
            status=404
        )

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"ok": False, "error": "Fecha inválida. Formato esperado YYYY-MM-DD."},
            status=400
        )

    # Modo inicial sin Google activo todavía
    if not getattr(settings, "TURNOS_USAR_GOOGLE_CALENDAR", False):
        horarios_demo = [
            "09:00", "09:30", "10:00", "10:30",
            "11:00", "11:30", "12:00",
            "15:00", "15:30", "16:00", "16:30", "17:00"
        ]
        return JsonResponse({
            "ok": True,
            "profesional": profesional.nombre,
            "fecha": fecha_str,
            "horarios": horarios_demo,
            "modo": "demo"
        })

    if not profesional.google_calendar_id:
        return JsonResponse(
            {"ok": False, "error": "El profesional no tiene calendar_id configurado."},
            status=400
        )

    # TODO: reemplazar por credenciales OAuth reales
    credentials = None

    try:
        bloques = consultar_bloques_ocupados(
            credentials=credentials,
            calendar_id=profesional.google_calendar_id,
            fecha=fecha,
        )

        horarios = generar_slots_disponibles(
            fecha=fecha,
            bloques_ocupados=bloques,
            duracion_minutos=profesional.duracion_turno_minutos,
            hora_inicio_jornada=9,
            hora_fin_jornada=18,
            intervalo_minutos=30,
        )

        return JsonResponse({
            "ok": True,
            "profesional": profesional.nombre,
            "fecha": fecha_str,
            "horarios": horarios,
        })

    except GoogleCalendarError as e:
        return JsonResponse(
            {"ok": False, "error": str(e)},
            status=500
        )


@transaction.atomic
def confirmar_turno(request, token):
    try:
        payload = validar_token_turno(token)
        turno = Turno.objects.select_for_update().select_related(
            "paciente", "profesional"
        ).get(id=payload["turno_id"])
    except Exception:
        return render(request, "turnos/turno_error.html", {
            "mensaje": "El link de confirmación es inválido o venció."
        })

    if turno.estado == Turno.ESTADO_CONFIRMADO:
        return render(request, "turnos/turno_ya_procesado.html", {
            "mensaje": "Este turno ya fue confirmado."
        })

    if turno.estado == Turno.ESTADO_RECHAZADO:
        return render(request, "turnos/turno_ya_procesado.html", {
            "mensaje": "Este turno ya fue rechazado."
        })

    if existe_solapamiento(
        profesional=turno.profesional,
        fecha=turno.fecha,
        hora_inicio=turno.hora_inicio,
        hora_fin=turno.hora_fin,
        excluir_turno_id=turno.id,
    ):
        return render(request, "turnos/turno_error.html", {
            "mensaje": "No se puede confirmar porque el horario ya está ocupado."
        })

    turno.estado = Turno.ESTADO_CONFIRMADO
    turno.confirmado_en = timezone.now()

    credentials = None

    if getattr(settings, "TURNOS_USAR_GOOGLE_CALENDAR", False):
        try:
            event_id = crear_evento_google(
                turno=turno,
                credentials=credentials,
                calendar_id=getattr(
                    settings,
                    "TURNOS_GOOGLE_CALENDAR_ID",
                    turno.profesional.google_calendar_id or "primary"
                ),
            )
            turno.google_event_id = event_id
        except GoogleCalendarError as e:
            return render(request, "turnos/turno_error.html", {
                "mensaje": f"El turno se pudo validar internamente pero falló Google Calendar: {e}"
            })

    turno.save()

    return render(request, "turnos/turno_confirmado.html", {"turno": turno})


@transaction.atomic
def rechazar_turno(request, token):
    try:
        payload = validar_token_turno(token)
        turno = Turno.objects.select_for_update().select_related(
            "paciente", "profesional"
        ).get(id=payload["turno_id"])
    except Exception:
        return render(request, "turnos/turno_error.html", {
            "mensaje": "El link de rechazo es inválido o venció."
        })

    if turno.estado == Turno.ESTADO_CONFIRMADO:
        return render(request, "turnos/turno_ya_procesado.html", {
            "mensaje": "Este turno ya fue confirmado y no puede rechazarse desde este link."
        })

    if turno.estado == Turno.ESTADO_RECHAZADO:
        return render(request, "turnos/turno_ya_procesado.html", {
            "mensaje": "Este turno ya fue rechazado."
        })

    turno.estado = Turno.ESTADO_RECHAZADO
    turno.rechazado_en = timezone.now()
    turno.save(update_fields=["estado", "rechazado_en"])

    return render(request, "turnos/turno_rechazado.html", {"turno": turno})

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect

def google_connect(request):
    flow = build_google_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    request.session["google_oauth_state"] = state
    request.session["google_code_verifier"] = flow.code_verifier

    return redirect(authorization_url)


def google_callback(request):
    state = request.session.get("google_oauth_state")
    code_verifier = request.session.get("google_code_verifier")

    if not state:
        return HttpResponseBadRequest("Falta google_oauth_state en sesión.")

    if not code_verifier:
        return HttpResponseBadRequest("Falta google_code_verifier en sesión.")

    flow = build_google_flow(state=state)
    flow.code_verifier = code_verifier

    flow.fetch_token(
        code=request.GET.get("code")
    )

    credentials = flow.credentials
    request.session["google_credentials"] = credentials_to_dict(credentials)

    request.session.pop("google_oauth_state", None)
    request.session.pop("google_code_verifier", None)

    return redirect("turnos:google_status")


def google_status(request):
    creds = request.session.get("google_credentials")
    conectado = bool(creds and creds.get("token"))

    return JsonResponse({
        "ok": True,
        "google_conectado": conectado,
        "scopes": creds.get("scopes") if creds else [],
    })