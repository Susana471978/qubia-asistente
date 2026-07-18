import asyncio
import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import settings

log = logging.getLogger("qubia.notificaciones")

ORO = "#2DD4BF"
NEGRO = "#0E0C09"


def _html_lead(nombre_tenant: str, datos: dict) -> str:
    filas = "".join(
        f'<tr>'
        f'<td style="padding:8px 12px;color:#8A8578;font-size:13px;'
        f'border-bottom:1px solid #1c1a17;">{k.capitalize()}</td>'
        f'<td style="padding:8px 12px;color:#ffffff;font-size:14px;'
        f'border-bottom:1px solid #1c1a17;">{v or "-"}</td>'
        f"</tr>"
        for k, v in datos.items()
        if k not in ("extra",)
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f5f5f4;
font-family:'Plus Jakarta Sans',Helvetica,Arial,sans-serif;">
  <table style="max-width:560px;margin:0 auto;background:{NEGRO};
  border-radius:3px;overflow:hidden;" cellpadding="0" cellspacing="0" width="100%">
    <tr><td style="padding:20px 24px;border-bottom:2px solid {ORO};">
      <div style="color:{ORO};font-size:12px;letter-spacing:2px;">QUBIA</div>
      <div style="color:#fff;font-size:18px;margin-top:4px;">Nuevo contacto</div>
      <div style="color:#8A8578;font-size:13px;margin-top:2px;">{nombre_tenant}</div>
    </td></tr>
    <tr><td style="padding:8px 12px;">
      <table width="100%" cellpadding="0" cellspacing="0">{filas}</table>
    </td></tr>
    <tr><td style="padding:16px 24px;color:#8A8578;font-size:11px;">
      Enviado automaticamente por el asistente de Qubia.
    </td></tr>
  </table>
</body></html>"""


def _enviar_email_sync(destino: str, asunto: str, html: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = settings.smtp_from
    msg["To"] = destino
    msg.set_content("Nuevo contacto desde el asistente. Ver version HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as s:
        s.login(settings.smtp_user, settings.smtp_password)
        s.send_message(msg)


async def enviar_email(destino: str, asunto: str, html: str) -> bool:
    """No-op silencioso si SMTP no esta configurado (mismo patron que ObjSin)."""
    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password):
        log.info("SMTP no configurado, email a %s omitido", destino)
        return False
    try:
        await asyncio.to_thread(_enviar_email_sync, destino, asunto, html)
        return True
    except Exception:
        log.exception("fallo envio email a %s", destino)
        return False


async def enviar_webhook(url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
        return True
    except Exception:
        log.exception("fallo webhook %s", url)
        return False


async def notificar_lead(tenant: dict, datos: dict) -> bool:
    destinos = tenant.get("leads", {}).get("destinos", [])
    activos = [d for d in destinos if d.get("activo")]
    if not activos:
        log.warning("tenant %s sin destinos de lead", tenant.get("slug"))
        return False

    nombre = tenant.get("nombre", "")
    html = _html_lead(nombre, datos)
    asunto = f"Nuevo contacto web - {nombre}"

    resultados = []
    for d in activos:
        if d["tipo"] == "email":
            resultados.append(await enviar_email(d["valor"], asunto, html))
        elif d["tipo"] == "webhook":
            resultados.append(
                await enviar_webhook(
                    d["valor"], {"tenant": tenant.get("slug"), "lead": datos}
                )
            )
    return any(resultados)
