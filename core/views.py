# myapp/views.py
from __future__ import annotations

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from .models import Formulario


WHATSAPP_NUMBER = "5491xxxxxxxxx"
DIRECCION_LOCAL = "Charcas 2014"

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


def placas_antihumedad(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="placas_antihumedad",
        page_title="Placas Antihumedad | Od. Alessandrello",
        page_description="Solución antihumedad con garantía. Venta y colocación. Cotización sin cargo.",
        producto="placas_antihumedad",
        origen=origen,
        whatsapp_text="Hola, estoy interesado/a en Placas Antihumedad. ¿Me pasan precios, modelos y tiempos de entrega?",
    )
    return render(request, "myapp/servicios/placas_antihumedad.html", ctx)

def prevencion_controles(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="prevencion",
        page_title="Prevención y Controles | Od. Alessandrello",
        page_description="Odontología preventiva infantil: controles, limpieza, flúor y selladores para evitar caries y cuidar la sonrisa desde temprano.",
        producto="prevencion",
        origen=origen,
        whatsapp_text="Hola, quiero sacar un turno para Prevención y Controles. ¿Me pasan disponibilidad?",
    )
    return render(request, "myapp/servicios/prevencion.html", ctx)


def primera_consulta_bebe(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="bebe",
        page_title="Primera Consulta del Bebé | Od. Alessandrello",
        page_description="Primera consulta odontopediátrica: evaluación del desarrollo dental y guía para mamá y papá sobre hábitos saludables desde el inicio.",
        producto="bebe",
        origen=origen,
        whatsapp_text="Hola, quiero sacar un turno para la Primera Consulta del Bebé. ¿Me pasan disponibilidad?",
    )
    return render(request, "myapp/servicios/bebe.html", ctx)


def tratamientos_restauradores(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="restauradores",
        page_title="Tratamientos Restauradores | Od. Alessandrello",
        page_description="Tratamientos para caries y restauraciones infantiles con técnicas modernas y mínimamente invasivas para mayor comodidad.",
        producto="restauradores",
        origen=origen,
        whatsapp_text="Hola, quiero consultar por Tratamientos Restauradores (caries/obturaciones). ¿Me pasan un turno?",
    )
    return render(request, "myapp/servicios/restauradores.html", ctx)


def odontologia_sin_miedo(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="sin_miedo",
        page_title="Odontología sin Miedo | Od. Alessandrello",
        page_description="Adaptación, contención emocional y manejo del miedo para que niños y familias vivan una experiencia dental positiva y tranquila.",
        producto="sin_miedo",
        origen=origen,
        whatsapp_text="Hola, mi hijo/a tiene miedo al dentista. ¿Podemos coordinar un turno para adaptación?",
    )
    return render(request, "myapp/servicios/sin_miedo.html", ctx)


def educacion_habitos(request):
    origen = detectar_origen(request)
    ctx = _base_context(
        is_home=False,
        active_producto="educacion",
        page_title="Educación y Hábitos | Od. Alessandrello",
        page_description="Educación en salud bucal: cepillado, alimentación y hábitos para prevenir caries y cuidar la sonrisa en casa.",
        producto="educacion",
        origen=origen,
        whatsapp_text="Hola, quiero una consulta para educación y hábitos (cepillado/alimentación). ¿Me pasan disponibilidad?",
    )
    return render(request, "myapp/servicios/educacion.html", ctx)
