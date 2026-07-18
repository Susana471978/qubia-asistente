# Qubia Asistente

Asistente IA multi-tenant. Una instancia, muchos clientes.

## Arranque local

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env      # rellenar GROQ_API_KEY
    python scripts/seed_dev.py
    uvicorn app.main:app --reload

## Resolucion de tenant

Cada cliente tiene una `public_key` (`qb_pub_<slug>_<hex>`) que viaja en la
cabecera `X-Qubia-Key`. Es identificacion, no autenticacion: la seguridad real
la dan `allowed_origins` por tenant + rate limiting por tenant+IP.

## Regla de oro

Toda consulta a `conversaciones`, `leads` y `usage_daily` lleva `tenant_id`.
El test `tests/test_tenant_isolation.py` lo verifica escaneando el codigo.

## Endpoints

Publicos (X-Qubia-Key):
  POST /v1/chat
  GET  /v1/config
  POST /v1/lead

Admin (JWT):
  POST   /admin/auth/login
  GET    /admin/tenants
  POST   /admin/tenants
  PATCH  /admin/tenants/{id}
  POST   /admin/tenants/{id}/rotar-key
  DELETE /admin/tenants/{id}
  GET    /admin/metrics/uso
  GET    /admin/metrics/leads
