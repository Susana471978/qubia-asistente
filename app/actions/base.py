"""Contrato base de una accion de Qubia.

Una ActionDef describe una accion disponible: su tipo (identificador estable,
en MAYUSCULAS), su etiqueta por defecto para el usuario (español) y el vertical
al que pertenece. No contiene logica de ejecucion en Sprint 1.
"""
from dataclasses import dataclass
from typing import Literal

Vertical = Literal["general", "real_estate", "hospitality", "guest"]


@dataclass(frozen=True)
class ActionDef:
    """Definicion declarativa de una accion.

    type    : identificador estable, p.ej. "SEARCH_PROPERTIES".
    label   : etiqueta por defecto visible para el usuario (es).
    vertical: vertical propietario de la accion.

    El label es el POR DEFECTO. Un tenant puede sobreescribir las etiquetas
    visibles via su campo quick_actions (configuracion en Mongo), sin tocar
    codigo ni el widget.
    """
    type: str
    label: str
    vertical: Vertical

    def as_dict(self) -> dict:
        """Serializacion para el contrato /v1/config y /v1/chat."""
        return {"type": self.type, "label": self.label}
