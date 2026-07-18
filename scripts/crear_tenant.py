#!/usr/bin/env python3
"""Alta de un tenant nuevo.

Uso:
    python scripts/crear_tenant.py --slug clinica-laguna \
        --nombre "Clinica Dental La Laguna" \
        --origins https://clinicalaguna.es,https://www.clinicalaguna.es \
        --email-leads info@clinicalaguna.es

    python scripts/crear_tenant.py --slug inmo-teide \
        --nombre "Inmobiliaria Teide" \
        --desde-json tenants/inmo-teide.json
"""
import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import generar_public_key  # noqa: E402

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--nombre", required=True)
    p.add_argument("--origins", default="")
    p.add_argument("--email-leads", default="")
    p.add_argument("--asistente", default="Asistente")
    p.add_argument("--status", default="trial", choices=["trial", "active", "suspended"])
    p.add_argument(
        "--desde-json",
        default="",
        help="Ruta a un JSON con el tenant completo (conocimiento, reglas_nivel1, ...)",
    )
    args = p.parse_args()

    extra: dict = {}
    if args.desde_json:
        ruta_json = Path(args.desde_json)
        if not ruta_json.is_file():
            sys.exit(f"ERROR: no existe el fichero {ruta_json}")
        try:
            extra = json.loads(ruta_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"ERROR: JSON invalido en {ruta_json}: {e}")
        if not isinstance(extra, dict):
            sys.exit("ERROR: el JSON debe ser un objeto.")
        for protegido in ("slug", "auth", "created_at", "updated_at"):
            extra.pop(protegido, None)

    if not SLUG_RE.match(args.slug):
        sys.exit("ERROR: slug invalido. Usa minusculas, numeros y guiones.")

    client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
    db = client[settings.mongo_db]

    if await db.tenants.find_one({"slug": args.slug}):
        sys.exit(f"ERROR: el slug '{args.slug}' ya existe.")

    ahora = datetime.now(timezone.utc)
    key = generar_public_key(args.slug)
    origins = [o.strip() for o in args.origins.split(",") if o.strip()]
    destinos = (
        [{"tipo": "email", "valor": args.email_leads, "activo": True}]
        if args.email_leads
        else []
    )

    doc = {
        "slug": args.slug,
        "nombre": args.nombre,
        "status": args.status,
        "created_at": ahora,
        "updated_at": ahora,
        "auth": {
            "public_key": key,
            "key_rotated_at": ahora,
            "key_previous": None,
            "key_previous_expires_at": None,
            "allowed_origins": origins,
        },
        "identidad": {
            "nombre_asistente": args.asistente,
            "tono": "cercano y profesional",
            "idioma_principal": "es",
            "idiomas_soportados": ["es"],
            "saludo_inicial": f"Hola, soy {args.asistente}. ¿En que puedo ayudarte?",
            "mensaje_fuera_alcance": "Eso lo ve mejor el equipo. ¿Quieres que te contacten?",
            "prompt_extra": "",
        },
        "conocimiento": {
            "descripcion_negocio": "",
            "horarios": "",
            "direccion": "",
            "telefono": "",
            "email": "",
            "servicios": [],
            "faqs": [],
            "documentos": [],
        },
        "reglas_nivel1": [],
        "leads": {
            "activo": True,
            "campos": ["nombre", "telefono", "email", "motivo"],
            "campos_obligatorios": ["nombre", "telefono"],
            "destinos": destinos,
            "trigger": "intencion",
        },
        "limites": {"mensajes_dia": 500, "mensajes_minuto": 10, "max_turnos_memoria": 6},
        "modelo": {"proveedor": "groq", "nombre": None, "temperatura": 0.4, "max_tokens": 500},
        "web": {"dominio": "", "cloudflare_project": f"qubia-{args.slug}", "plantilla_version": "1.0.0"},
        "facturacion": {"alta": ahora, "cuota_mensual": 0, "estado_pago": "al_corriente"},
    }

    if extra:
        for clave, valor in extra.items():
            if isinstance(valor, dict) and isinstance(doc.get(clave), dict):
                doc[clave].update(valor)
            else:
                doc[clave] = valor
        doc["auth"]["allowed_origins"] = origins or doc["auth"].get("allowed_origins", [])

    await db.tenants.insert_one(doc)
    client.close()

    print(f"\nTenant creado: {args.nombre}")
    print(f"  slug        : {args.slug}")
    print(f"  status      : {args.status}")
    print(f"  public_key  : {key}")
    print(f"  origins     : {doc['auth']['allowed_origins'] or '(ninguno - añadir antes de produccion)'}")
    con = doc.get("conocimiento", {})
    print(f"  servicios   : {len(con.get('servicios', []))}")
    print(f"  faqs        : {len(con.get('faqs', []))}")
    print(f"  reglas nv1  : {len(doc.get('reglas_nivel1', []))}")
    print(f"\n  <script src=\"https://cdn.qubia.es/widget/v1.js\"")
    print(f"          data-qubia-key=\"{key}\"")
    print(f"          data-api=\"https://api.qubia.es\"></script>\n")


if __name__ == "__main__":
    asyncio.run(main())
