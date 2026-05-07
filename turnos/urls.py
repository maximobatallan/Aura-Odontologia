# turnos/urls.py
from django.urls import path
from . import views

app_name = "turnos"

urlpatterns = [
    path("", views.solicitar_turno, name="solicitar"),
    path("gracias/", views.turno_pendiente, name="pendiente"),
    path("confirmar/<str:token>/", views.confirmar_turno, name="confirmar"),
    path("rechazar/<str:token>/", views.rechazar_turno, name="rechazar"),
    path("api/horarios-disponibles/", views.horarios_disponibles, name="horarios_disponibles"),
    path("google/connect/", views.google_connect, name="google_connect"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("google/status/", views.google_status, name="google_status"),

]