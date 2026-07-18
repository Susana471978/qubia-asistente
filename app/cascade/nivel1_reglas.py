import re
import unicodedata


def normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _contiene_keyword(mensaje_norm: str, keyword: str) -> bool:
    kw = normalizar(keyword)
    if not kw:
        return False
    patron = r"(?<!\w)" + re.escape(kw).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(patron, mensaje_norm) is not None


def evaluar(mensaje: str, reglas: list[dict]) -> str | None:
    if not reglas:
        return None
    mensaje_norm = normalizar(mensaje)
    if not mensaje_norm:
        return None
    candidatas = [
        r for r in reglas
        if any(_contiene_keyword(mensaje_norm, kw) for kw in r.get("keywords", []))
    ]
    if not candidatas:
        return None
    return max(candidatas, key=lambda r: r.get("prioridad", 0)).get("respuesta") or None
