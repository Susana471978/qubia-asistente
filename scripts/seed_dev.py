#!/usr/bin/env python3
"""Tenant de demostracion para desarrollo local."""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.config import settings  # noqa: E402

KEY_DEMO = "qb_pub_demo_000000000000"


async def main() -> None:
    if not settings.is_dev:
        sys.exit("ERROR: seed solo en APP_ENV=development")

    client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
    db = client[settings.mongo_db]
    ahora = datetime.now(timezone.utc)

    await db.tenants.delete_one({"slug": "demo"})
    await db.tenants.insert_one(
        {
            "slug": "demo",
            "nombre": "Clinica Demo Qubia",
            "status": "active",
            "created_at": ahora,
            "updated_at": ahora,
            "auth": {
                "public_key": KEY_DEMO,
                "key_rotated_at": ahora,
                "key_previous": None,
                "key_previous_expires_at": None,
                "allowed_origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
            },
            "identidad": {
                "nombre_asistente": "Marta",
                "tono": "cercano y profesional",
                "idioma_principal": "es",
                "idiomas_soportados": ["es", "en"],
                "saludo_inicial": "Hola, soy Marta. ¿En que puedo ayudarte?",
                "mensaje_fuera_alcance": "Eso lo ve mejor el equipo. ¿Quieres que te llamen?",
                "prompt_extra": "",
            },
            "conocimiento": {
                "descripcion_negocio": "Clinica dental en La Laguna, Tenerife. "
                "Mas de 20 anos atendiendo a familias de la comarca.",
                "horarios": "Lunes a viernes de 9:00 a 20:00. Sabados de 9:00 a 14:00.",
                "direccion": "Calle Ejemplo 12, San Cristobal de La Laguna",
                "telefono": "922 000 000",
                "email": "info@demo.es",
                "servicios": [
                    {"nombre": "Revision general", "descripcion": "Diagnostico completo", "precio_desde": 40},
                    {"nombre": "Limpieza dental", "descripcion": "Higiene profesional", "precio_desde": 55},
                    {"nombre": "Ortodoncia invisible", "descripcion": "Alineadores transparentes", "precio_desde": None},
                ],
                "faqs": [
                    {"pregunta": "¿Hay aparcamiento?", "respuesta": "Si, parking gratuito para pacientes."},
                    {"pregunta": "¿Trabajais con seguros?", "respuesta": "Si, con las principales aseguradoras."},
                ],
                "documentos": [],
            },
            "reglas_nivel1": [
                {
                    "id": "horario",
                    "keywords": ["horario", "horarios", "abren", "cierran", "abierto"],
                    "respuesta": "Abrimos de lunes a viernes de 9:00 a 20:00 y los sabados de 9:00 a 14:00.",
                    "prioridad": 10,
                },
                {
                    "id": "direccion",
                    "keywords": ["donde estais", "direccion", "como llegar", "ubicacion"],
                    "respuesta": "Estamos en Calle Ejemplo 12, La Laguna. Con parking gratuito para pacientes.",
                    "prioridad": 10,
                },
            ],
            "leads": {
                "activo": True,
                "campos": ["nombre", "telefono", "email", "motivo"],
                "campos_obligatorios": ["nombre", "telefono"],
                "destinos": [{"tipo": "email", "valor": "info@demo.es", "activo": True}],
                "trigger": "intencion",
            },
            "limites": {"mensajes_dia": 1000, "mensajes_minuto": 20, "max_turnos_memoria": 6},
            "modelo": {"proveedor": "groq", "nombre": None, "temperatura": 0.4, "max_tokens": 500},
            "web": {"dominio": "localhost", "cloudflare_project": "qubia-demo", "plantilla_version": "1.0.0"},
            "facturacion": {"alta": ahora, "cuota_mensual": 0, "estado_pago": "al_corriente"},
        }
    )
    client.close()
    print(f"Tenant demo creado. public_key: {KEY_DEMO}")


if __name__ == "__main__":
    asyncio.run(main())
