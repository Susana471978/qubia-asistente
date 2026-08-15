"""Motor de acciones de Qubia Core.

Las acciones representan lo que el usuario puede disparar desde la UI del
widget, separadas de la generacion de texto. Cada vertical declara su propio
catalogo en su modulo; el registry las agrupa y resuelve por vertical.

En Sprint 1 las acciones se DECLARAN (type + label por defecto). La ejecucion
real (buscar propiedades, crear visitas, etc.) se conecta en Sprints 2-3.
"""
from app.actions.registry import acciones_de_vertical, catalogo_completo

__all__ = ["acciones_de_vertical", "catalogo_completo"]
