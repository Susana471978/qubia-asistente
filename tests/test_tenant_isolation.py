"""Aislamiento entre tenants. Si algo de aqui falla, no se despliega."""
import inspect
import re
from pathlib import Path

import pytest

from app.core import security
from app.core.cache import TTLCache

RAIZ = Path(__file__).resolve().parents[1]

COLECCIONES_SCOPED = ["conversaciones", "leads", "usage_daily"]


def test_todo_acceso_a_colecciones_scoped_filtra_por_tenant():
    """Ninguna consulta a colecciones de datos de cliente puede omitir tenant_id."""
    fallos = []
    for archivo in (RAIZ / "app").rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for coleccion in COLECCIONES_SCOPED:
            patron = rf"db\.{coleccion}\.(find_one|find|update_one|update_many|delete_one|delete_many|insert_one|aggregate)\("
            for m in re.finditer(patron, texto):
                # Ventana a ambos lados: el filtro puede ir en el propio query
                # (despues) o en un doc construido antes de la llamada.
                inicio = max(0, m.start() - 600)
                fragmento = texto[inicio : m.start() + 400]
                if "tenant_id" not in fragmento:
                    linea = texto[: m.start()].count("\n") + 1
                    fallos.append(f"{archivo.relative_to(RAIZ)}:{linea} -> {m.group(0)}")
    assert not fallos, "Consultas sin tenant_id:\n" + "\n".join(fallos)


def test_origen_no_permitido_si_no_esta_en_lista(monkeypatch):
    monkeypatch.setattr(security.settings, "app_env", "production")
    permitidos = ["https://clientea.es"]
    assert security.origen_permitido("https://clientea.es", permitidos)
    assert not security.origen_permitido("https://clienteb.es", permitidos)
    assert not security.origen_permitido("https://evil.com", permitidos)
    assert not security.origen_permitido(None, permitidos)
    assert not security.origen_permitido("https://clientea.es", [])


def test_origen_ignora_barra_final_y_mayusculas(monkeypatch):
    monkeypatch.setattr(security.settings, "app_env", "production")
    assert security.origen_permitido("https://ClienteA.es/", ["https://clientea.es"])


def test_origen_distingue_subdominio(monkeypatch):
    monkeypatch.setattr(security.settings, "app_env", "production")
    assert not security.origen_permitido("https://www.clientea.es", ["https://clientea.es"])


def test_claves_publicas_son_unicas_y_con_prefijo():
    claves = {security.generar_public_key("demo") for _ in range(500)}
    assert len(claves) == 500
    assert all(k.startswith("qb_pub_demo_") for k in claves)


def test_cache_no_mezcla_claves():
    cache = TTLCache(ttl=60)
    cache.set("qb_pub_a_1", {"slug": "a"})
    cache.set("qb_pub_b_2", {"slug": "b"})
    assert cache.get("qb_pub_a_1")["slug"] == "a"
    assert cache.get("qb_pub_b_2")["slug"] == "b"
    cache.invalidate("qb_pub_a_1")
    assert cache.get("qb_pub_a_1") is None
    assert cache.get("qb_pub_b_2")["slug"] == "b"


def test_cache_expira():
    cache = TTLCache(ttl=0)
    cache.set("k", {"v": 1})
    assert cache.get("k") is None


@pytest.mark.parametrize("clave_mala", ["", "no-es-una-clave", "sk_live_algo", "qb_priv_x"])
def test_claves_con_formato_invalido_se_rechazan(clave_mala):
    from app.core.errors import QubiaError

    async def run():
        with pytest.raises(QubiaError):
            await security.resolver_tenant(None, clave_mala)

    import asyncio

    asyncio.run(run())


def test_get_tenant_exige_status_active():
    """El codigo de deps debe comprobar explicitamente status == active."""
    from app import deps

    fuente = inspect.getsource(deps.get_tenant)
    assert '"active"' in fuente
    assert "origen_permitido" in fuente
