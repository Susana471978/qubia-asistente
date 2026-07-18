#!/usr/bin/env python3
"""Crea un usuario administrador interno de Objetiva."""
import argparse
import asyncio
import getpass
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    args = p.parse_args()

    password = getpass.getpass("Password: ")
    if len(password) < 10:
        sys.exit("ERROR: minimo 10 caracteres.")
    if password != getpass.getpass("Repetir: "):
        sys.exit("ERROR: no coinciden.")

    client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
    db = client[settings.mongo_db]

    email = args.email.lower()
    if await db.admin_users.find_one({"email": email}):
        sys.exit(f"ERROR: {email} ya existe.")

    await db.admin_users.insert_one(
        {
            "email": email,
            "password_hash": hash_password(password),
            "rol": "admin",
            "activo": True,
            "created_at": datetime.now(timezone.utc),
        }
    )
    client.close()
    print(f"Admin creado: {email}")


if __name__ == "__main__":
    asyncio.run(main())
