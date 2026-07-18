"""Nivel 2 - RAG sobre documentos del tenant. Placeholder deliberado.

Cuando se active:
  1. Ingesta: tenant.conocimiento.documentos -> chunks -> embeddings
  2. Almacen: coleccion `chunks` con tenant_id + vector
  3. Busqueda: Atlas Vector Search filtrando SIEMPRE por tenant_id
  4. Si score < umbral -> None y cae a nivel 3
"""


async def consultar(db, tenant: dict, mensaje: str) -> str | None:
    return None
