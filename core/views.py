# myapp/views.py
from __future__ import annotations

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from .models import Formulario


WHATSAPP_NUMBER = "5491xxxxxxxxx"
DIRECCION_LOCAL = "Besares 2477, 3°D"

SERVICIOS = [
    {"key": "prevencion", "nombre": "Prevención y controles", "url_name": "servicio_prevencion"},
    {"key": "bebe", "nombre": "Primera consulta del bebé", "url_name": "servicio_bebe"},
    {"key": "restauradores", "nombre": "Tratamientos restauradores", "url_name": "servicio_restauradores"},
    {"key": "sin_miedo", "nombre": "Odontología sin miedo", "url_name": "servicio_sin_miedo"},
    {"key": "educacion", "nombre": "Educación y hábitos", "url_name": "servicio_educacion"},
]



def _base_context(**extra):
    ctx = {
        "servicios_menu": SERVICIOS,
        "telefono_whatsapp": WHATSAPP_NUMBER,
        "direccion_local": DIRECCION_LOCAL,
        "site_name": "Od. Alessandrello",
    }
    ctx.update(extra)
    return ctx


def detectar_origen(request) -> str:
    if request.GET.get("gclid"):
        return "google_ads"
    if request.GET.get("fbclid"):
        return "facebook_ads"

    utm_source = (request.GET.get("utm_source") or "").lower().strip()
    if utm_source in {"google", "googleads", "adwords"}:
        return "google_ads"
    if utm_source in {"facebook", "instagram", "meta"}:
        return "facebook_ads"
    if utm_source in {"whatsapp"}:
        return "whatsapp"
    if utm_source in {"organico", "organic", "seo"}:
        return "organico"

    return "directo"


def _sanitize_choice(value: str, allowed: set[str], default: str) -> str:
    v = (value or "").strip()
    return v if v in allowed else default


def send_user_data_email(user_data: str) -> None:
    subject = "Nuevo formulario web"
    body = f"Se registró un nuevo formulario con los siguientes datos:\n\n{user_data}"

    from_email = "notificaciondepaginaweb@gmail.com"

    # Puede ser uno solo o incluso el mismo from_email
    to = ["notificaciondepaginaweb@gmail.com"]

    bcc = [
        "maximobatallan@gmail.com",
        "od.alessandrello@gmail.com",
    ]

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        bcc=bcc,
    )

    email.send(fail_silently=False)


def home(request):
    formulario_enviado = bool(request.GET.get("ok"))
    origen = detectar_origen(request)

    ctx = _base_context(
        is_home=True,
        formulario_enviado=formulario_enviado,
        page_title="Od. Alessandrello | Odontología integral para todas las edades",

        page_description=(
            "Odontología integral para todas las edades. Especialistas en odontopediatría, implantología y rehabilitación oral. "
            "Atención profesional, cercana y personalizada con turnos por WhatsApp."
        ),

        whatsapp_text="Hola, quiero sacar un turno. ¿Me pasan disponibilidad?",
    

        producto="general",  # podés mantenerlo por compatibilidad interna
        origen=origen,

    )

    return render(request, "myapp/pages/home.html", ctx)



@require_POST
def save_formulario(request):
    nombre = (request.POST.get("name") or "").strip()
    telefono = (request.POST.get("telefono") or "").strip()
    email = (request.POST.get("email") or "").strip()
    texto = (request.POST.get("message") or "").strip()

    # choices válidos desde el modelo (no hardcodear)
    servicios_validos = {k for (k, _) in Formulario.SERVICIOS_CHOICES}
    origenes_validos = {k for (k, _) in Formulario.ORIGEN_CHOICES}

    producto = _sanitize_choice(request.POST.get("producto"), servicios_validos, "general")
    origen = _sanitize_choice(request.POST.get("origen"), origenes_validos, "directo")

    # Tracking extra
    gclid = (request.POST.get("gclid") or "").strip()
    fbclid = (request.POST.get("fbclid") or "").strip()

    utm_source = (request.POST.get("utm_source") or "").strip()
    utm_medium = (request.POST.get("utm_medium") or "").strip()
    utm_campaign = (request.POST.get("utm_campaign") or "").strip()
    utm_term = (request.POST.get("utm_term") or "").strip()
    utm_content = (request.POST.get("utm_content") or "").strip()

    # A dónde volver (misma página). Guardamos también landing para análisis.
    next_url = (request.POST.get("next") or "").strip()  # suele ser request.get_full_path
    landing_path = next_url or request.path

    lead = Formulario.objects.create(
        nombre=nombre,
        telefono=telefono,
        mail=email,
        texto=texto,
        producto=producto,
        origen=origen,
        gclid=gclid,
        fbclid=fbclid,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        landing_path=landing_path,
    )

    user_data = (
        f"nombre: {nombre}\n"
        f"telefono: {telefono}\n"
        f"email: {email}\n"
        f"producto: {producto}\n"
        f"texto: {texto}"
    )
    send_user_data_email(user_data)

    if next_url:
        sep = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{sep}ok=1")

    return redirect(f"{reverse('myapp:home')}?ok=1")


def politicas_privacidad(request):
    ctx = _base_context(
        is_home=False,
        page_title="Políticas de Privacidad | Od. Alessandrello",
        page_description="Políticas de privacidad de Od. Alessandrello.",
    )
    return render(request, "myapp/politicas_privacidad.html", ctx)

def odontopediatria(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="odontopediatria",
        page_title="Odontopediatría | Od. Alessandrello",
        page_description="Especialistas en odontopediatría. Atención odontológica para bebés, niños y adolescentes con enfoque preventivo y cuidado integral.",
        producto="odontopediatria",
        origen=origen,
        whatsapp_text="Hola, quiero sacar un turno para odontopediatría. ¿Me pasan disponibilidad?",
    )
    return render(request, "myapp/servicios/odontopediatria.html", ctx)


def odontologia_general(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="odontologia_general",
        page_title="Odontología General | Od. Alessandrello",
        page_description="Odontología general para todas las edades. Diagnóstico, limpieza, tratamientos restauradores y cuidado integral de la salud bucal.",
        producto="odontologia_general",
        origen=origen,
        whatsapp_text="Hola, quiero consultar por odontología general. ¿Me pasan disponibilidad?",
    )
    return render(request, "myapp/servicios/odontologia_general.html", ctx)


def implantologia(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="implantologia",
        page_title="Implantología Dental | Od. Alessandrello",
        page_description="Implantes dentales para recuperar función y estética. Tratamientos modernos con planificación digital y materiales de alta calidad.",
        producto="implantologia",
        origen=origen,
        whatsapp_text="Hola, quiero consultar por implantes dentales. ¿Me pasan información?",
    )
    return render(request, "myapp/servicios/implantologia.html", ctx)