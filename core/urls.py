from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    # Home / Landing
    path("", views.home, name="home"),

    # Formulario
    path("save-formulario/", views.save_formulario, name="save_formulario"),

    # Landings de servicios odontopediátricos
    path('servicios/odontologia-general/', views.odontologia_general, name='servicio_odontologia_general'),
    path('servicios/implantologia/', views.implantologia, name='servicio_implantologia'),
    path('servicios/odontopediatria/', views.odontopediatria, name='servicio_odontopediatria'),


    # Legales
    path("politicas-privacidad/", views.politicas_privacidad, name="politicas_privacidad"),
]
