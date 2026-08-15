"""Tests de resolucion de quick_actions por vertical (Sprint 1, paso 5)."""
from app.routers.chat import _resolver_quick_actions


def test_real_estate_usa_registry_si_no_hay_config():
    qa = _resolver_quick_actions({"vertical": "real_estate"})
    tipos = {x["type"] for x in qa}
    assert "SEARCH_PROPERTIES" in tipos
    assert len(qa) == 6
    assert all("label" in x and "type" in x for x in qa)


def test_tenant_config_tiene_prioridad():
    qa = _resolver_quick_actions(
        {"vertical": "real_estate", "quick_actions": ["Encuentra tu hogar"]}
    )
    assert qa == [{"type": "CUSTOM", "label": "Encuentra tu hogar"}]


def test_general_no_expone_acciones():
    assert _resolver_quick_actions({"vertical": "general"}) == []


def test_real_estate_no_recibe_acciones_de_hospitality():
    qa = _resolver_quick_actions({"vertical": "real_estate"})
    tipos = {x["type"] for x in qa}
    assert "SHOW_MENU" not in tipos
    assert "REQUEST_TABLE" not in tipos
