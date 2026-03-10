# turnos/models.py
from datetime import datetime, timedelta, time
from django.db import models
from django.utils import timezone


class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    documento = models.CharField(max_length=30, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido}".strip()


# turnos/models.py
class Profesional(models.Model):
    nombre = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    especialidad = models.CharField(max_length=120, blank=True)
    duracion_turno_minutos = models.PositiveIntegerField(default=30)
    google_calendar_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Turno(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_CONFIRMADO = "confirmado"
    ESTADO_RECHAZADO = "rechazado"
    ESTADO_CANCELADO = "cancelado"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_CONFIRMADO, "Confirmado"),
        (ESTADO_RECHAZADO, "Rechazado"),
        (ESTADO_CANCELADO, "Cancelado"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="turnos"
    )
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.PROTECT,
        related_name="turnos"
    )

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    motivo = models.CharField(max_length=255, blank=True)
    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )

    token = models.CharField(max_length=255, blank=True)
    google_event_id = models.CharField(max_length=255, blank=True)

    mail_confirmacion_enviado = models.BooleanField(default=False)
    mail_recordatorio_enviado = models.BooleanField(default=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    rechazado_en = models.DateTimeField(null=True, blank=True)
    cancelado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-hora_inicio"]

    def __str__(self):
        return f"{self.paciente} - {self.fecha} {self.hora_inicio}"

    @property
    def fecha_inicio_datetime(self):
        dt = datetime.combine(self.fecha, self.hora_inicio)
        return timezone.make_aware(dt, timezone.get_current_timezone())

    @property
    def fecha_fin_datetime(self):
        dt = datetime.combine(self.fecha, self.hora_fin)
        return timezone.make_aware(dt, timezone.get_current_timezone())

    @property
    def ya_procesado(self):
        return self.estado in {
            self.ESTADO_CONFIRMADO,
            self.ESTADO_RECHAZADO,
            self.ESTADO_CANCELADO,
        }