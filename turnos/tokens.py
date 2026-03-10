# turnos/tokens.py
from django.core import signing
from django.conf import settings

TOKEN_SALT = "turnos-confirmacion-v1"
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 días


def generar_token_turno(turno_id: int) -> str:
    return signing.dumps({"turno_id": turno_id}, salt=TOKEN_SALT)


def validar_token_turno(token: str) -> dict:
    return signing.loads(
        token,
        salt=TOKEN_SALT,
        max_age=TOKEN_MAX_AGE_SECONDS
    )