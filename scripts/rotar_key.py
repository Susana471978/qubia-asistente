#!/usr/bin/env python3
"""Rota la clave publica de un tenant. La anterior sigue viva 7 dias."""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import generar_public_key  # noqa: E402

VENTANA_DIAS = 7


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    args = p.parse_args()

    client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
    db = client[settings.mongo_db]

    tenant = await db.tenants.find_one({"slug": args.slug})
    if not tenant:
        sys.exit(f"ERROR: tenant '{args.slug}' no encontrado.")

    anterior = tenant["auth"]["public_key"]
    nueva = generar_public_key(args.slug)
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(days=VENTANA_DIAS)

    await db.tenants.update_one(
        {"_id": tenant["_id"]},
        {
            "$set": {
                "auth.public_key": nueva,
                "auth.key_rotated_at": ahora,
                "auth.key_previous": anterior,
                "auth.key_previous_expires_at": expira,
                "updated_at": ahora,
            }
        },
    )
    client.close()

    print(f"\nClave rotada para {args.slug}")
    print(f"  nueva    : {nueva}")
    print(f"  anterior : {anterior}")
    print(f"  la anterior deja de funcionar el {expira:%d/%m/%Y}")
    print("  Actualiza data-qubia-key en la web del cliente antes de esa fecha.\n")


if __name__ == "__main__":
    asyncio.run(main())
