"""Envio de correo por SMTP, deliberadamente agnostico de proveedor.

POR QUE SMTP Y NO EL SDK DE UN PROVEEDOR
----------------------------------------
Gmail, Resend, Brevo, Mailgun, Amazon SES y un servidor propio hablan todos
SMTP. Acoplarse al SDK de uno obligaria a reescribir esto el dia que cambie
el proveedor -- y el primer proveedor de un proyecto que arranca casi nunca
es el definitivo. Con SMTP se cambia de proveedor editando el `.env`.

LIMITES CONOCIDOS, escritos aqui y no escondidos
------------------------------------------------
1. **Es sincrono y bloquea la peticion.** Un servidor SMTP lento anade su
   latencia al alta del lead. Por eso hay `SMTP_TIMEOUT` (10s por defecto) y
   por eso cualquier fallo se traga: ver el punto 2. El dia que haya mas
   volumen, esto se mueve a una cola -- no antes, porque una cola es otra
   pieza de infraestructura que mantener.
2. **Falla en silencio, a proposito.** Si el correo no sale, se registra un
   warning y la peticion sigue su curso. El lead YA esta guardado en la base
   de datos cuando se intenta notificar; perder el aviso es molesto, perder
   el lead por un fallo de SMTP seria inaceptable.
3. **Sin reintentos.** Un fallo transitorio pierde ese aviso concreto. Los
   datos nunca se pierden: estan en la tabla y en el dashboard.
4. **No verifica entregabilidad.** Que el servidor acepte el mensaje no
   garantiza que no acabe en spam. Con dominio propio, configurar SPF y
   DKIM es lo que mueve la aguja ahi.

NUNCA se registra el contenido del correo ni las credenciales SMTP.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def correo_configurado() -> bool:
    """True si hay lo minimo para intentar un envio.

    Sin esto configurado el modulo entero es inerte: no falla, no avisa en
    cada peticion, simplemente no manda nada. Es el comportamiento correcto
    en dev y en CI, donde nadie quiere un servidor SMTP de verdad.
    """
    return bool(settings.smtp_host and settings.notify_email)


def _remitente() -> str:
    return settings.smtp_from or settings.smtp_user or "ninjasec@localhost"


def enviar_correo(asunto: str, cuerpo: str, destino: str | None = None) -> bool:
    """Envia un correo de texto plano. Devuelve si salio, nunca lanza.

    El valor de retorno existe para los tests y para quien quiera registrar
    el resultado; los llamadores normales pueden ignorarlo.
    """
    if not correo_configurado():
        logger.debug("Correo no configurado; no se envia '%s'", asunto)
        return False

    destinatario = destino or settings.notify_email

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = _remitente()
    mensaje["To"] = destinatario
    mensaje.set_content(cuerpo)

    try:
        if settings.smtp_use_ssl:
            cliente = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout,
            )
        else:
            cliente = smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout,
            )

        with cliente:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                cliente.starttls()
            if settings.smtp_user:
                cliente.login(settings.smtp_user, settings.smtp_password)
            cliente.send_message(mensaje)

    except Exception as exc:  # noqa: BLE001 -- ver limite 2 del docstring
        # Se registra el tipo de error, nunca el contenido ni las
        # credenciales. El dato ya esta persistido; esto solo es el aviso.
        logger.warning(
            "No se pudo enviar el correo '%s': %s", asunto, type(exc).__name__
        )
        return False

    logger.info("Correo enviado: %s", asunto)
    return True


# ---------------------------------------------------------------------------
# Avisos concretos
# ---------------------------------------------------------------------------
# Van aqui y no en los routers para que el texto viva en un solo sitio y para
# que los routers no sepan nada de SMTP.


def avisar_lead_nuevo(
    *, empresa: str, contacto: str, email: str, telefono: str | None, mensaje: str | None
) -> bool:
    cuerpo = (
        "Ha entrado un lead nuevo por la web.\n\n"
        f"Empresa : {empresa}\n"
        f"Contacto: {contacto}\n"
        f"Email   : {email}\n"
        f"Telefono: {telefono or '-'}\n\n"
        f"Mensaje:\n{mensaje or '(sin mensaje)'}\n\n"
        "Verlo en el dashboard: /dashboard/leads\n"
    )
    return enviar_correo(f"[NinjaSec] Lead nuevo: {empresa}", cuerpo)


def avisar_postulacion_nueva(
    *, nombre: str, email: str, puesto: str | None, resumen: str | None
) -> bool:
    cuerpo = (
        "Ha entrado una postulacion nueva por la web.\n\n"
        f"Nombre: {nombre}\n"
        f"Email : {email}\n"
        f"Puesto: {puesto or '-'}\n\n"
        f"Resumen:\n{resumen or '(sin resumen)'}\n\n"
        "Verla en el dashboard: /dashboard/applications\n"
    )
    return enviar_correo(f"[NinjaSec] Postulacion nueva: {nombre}", cuerpo)
