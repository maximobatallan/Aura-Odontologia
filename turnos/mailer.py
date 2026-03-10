# turnos/mailer.py
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def enviar_mail_profesional_nuevo_turno(request, turno):
    if not turno.profesional.email:
        print(f"[TURNOS] El profesional {turno.profesional_id} no tiene email cargado.")
        return False

    url_confirmar = request.build_absolute_uri(
        reverse("turnos:confirmar", args=[turno.token])
    )
    url_rechazar = request.build_absolute_uri(
        reverse("turnos:rechazar", args=[turno.token])
    )

    subject = f"Nueva solicitud de turno - {turno.paciente.nombre} {turno.paciente.apellido}"

    message = (
        f"Se generó una nueva solicitud de turno.\n\n"
        f"Paciente: {turno.paciente.nombre} {turno.paciente.apellido}\n"
        f"Email: {turno.paciente.email}\n"
        f"Teléfono: {turno.paciente.telefono}\n"
        f"Documento: {turno.paciente.documento}\n"
        f"Profesional: {turno.profesional.nombre}\n"
        f"Fecha: {turno.fecha}\n"
        f"Hora: {turno.hora_inicio} - {turno.hora_fin}\n"
        f"Motivo: {turno.motivo}\n"
        f"Observaciones: {turno.observaciones}\n\n"
        f"Confirmar turno:\n{url_confirmar}\n\n"
        f"Rechazar turno:\n{url_rechazar}\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
        recipient_list=[turno.profesional.email],
        fail_silently=False,
    )
    print(f"[TURNOS] Mail enviado a {turno.profesional.email}")
    return True