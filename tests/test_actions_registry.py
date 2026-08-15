"""Tests del motor de acciones (Sprint 1, paso 4)."""
from app.actions import registry
from app.actions.base import ActionDef


def test_real_estate_tiene_sus_seis_acciones():
    tipos = registry.tipos_de_vertical("real_estate")
    esperadas = {
        "SEARCH_PROPERTIES", "SHOW_PROPERTY", "COMPARE_PROPERTIES",
        "REQUEST_VISIT", "REQUEST_INFO", "CONTACT_AGENT",
    }
    assert tipos == esperadas


def test_general_no_expone_acciones():
    assert registry.acciones_de_vertical("general") == []


def test_vertical_desconocido_devuelve_vacio_sin_lanzar():
    assert registry.acciones_de_vertical("inexistente") == []


def test_aislamiento_entre_verticales():
    """Un tenant Real Estate NO debe recibir acciones de Hospitality."""
    re_tipos = registry.tipos_de_vertical("real_estate")
    hosp_tipos = registry.tipos_de_vertical("hospitality")
    guest_tipos = registry.tipos_de_vertical("guest")
    assert re_tipos.isdisjoint(hosp_tipos)
    assert re_tipos.isdisjoint(guest_tipos)
    assert hosp_tipos.isdisjoint(guest_tipos)
    assert not registry.es_accion_valida("real_estate", "SHOW_MENU")
    assert registry.es_accion_valida("real_estate", "SEARCH_PROPERTIES")


def test_labels_por_defecto_en_espanol():
    accs = registry.acciones_de_vertical("real_estate")
    labels = {a.type: a.label for a in accs}
    assert labels["SEARCH_PROPERTIES"] == "Buscar propiedad"
    assert labels["REQUEST_VISIT"] == "Solicitar visita"


def test_as_dict_serializa_type_y_label():
    a = ActionDef("X", "Equis", "real_estate")
    assert a.as_dict() == {"type": "X", "label": "Equis"}


def test_catalogo_completo_incluye_los_cuatro_verticales():
    cat = registry.catalogo_completo()
    assert set(cat.keys()) == {"general", "real_estate", "hospitality", "guest"}
    assert len(cat["real_estate"]) == 6
    assert len(cat["hospitality"]) == 5
    assert len(cat["guest"]) == 5
