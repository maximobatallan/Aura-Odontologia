# orejas/models.py
from django.db import models

class Formulario(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50)
    mail = models.EmailField()
    texto = models.TextField()

    SERVICIOS_CHOICES = [
        ("prevencion", "Prevención y Controles"),
        ("bebe", "Primera Consulta del Bebé"),
        ("restauradores", "Tratamientos Restauradores"),
        ("sin_miedo", "Odontología sin Miedo"),
        ("educacion", "Educación y Hábitos"),
        ("general", "Consulta General"),
    ]


    producto = models.CharField(max_length=50, choices=SERVICIOS_CHOICES, default="general")

    ORIGEN_CHOICES = [
        ("google_ads", "Google Ads"),
        ("facebook_ads", "Facebook / Instagram Ads"),
        ("organico", "Búsqueda Orgánica"),
        ("whatsapp", "WhatsApp"),
        ("directo", "Tráfico Directo"),
    ]
    origen = models.CharField(max_length=50, choices=ORIGEN_CHOICES, default="directo")

    # UTMs
    utm_source = models.CharField(max_length=100, blank=True, default="")
    utm_medium = models.CharField(max_length=100, blank=True, default="")
    utm_campaign = models.CharField(max_length=100, blank=True, default="")
    utm_content = models.CharField(max_length=100, blank=True, default="")
    utm_term = models.CharField(max_length=100, blank=True, default="")

    # Click IDs / landing
    gclid = models.CharField(max_length=255, blank=True, default="")
    fbclid = models.CharField(max_length=255, blank=True, default="")
    landing_path = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.producto} - {self.origen}"
