from fastapi import HTTPException, status


class QubiaError(HTTPException):
    pass


def tenant_no_encontrado() -> QubiaError:
    return QubiaError(status.HTTP_401_UNAUTHORIZED, "Clave de tenant invalida")


def tenant_inactivo() -> QubiaError:
    return QubiaError(status.HTTP_403_FORBIDDEN, "Tenant inactivo")


def origen_no_permitido() -> QubiaError:
    return QubiaError(status.HTTP_403_FORBIDDEN, "Origen no autorizado")


def cuota_superada() -> QubiaError:
    return QubiaError(status.HTTP_429_TOO_MANY_REQUESTS, "Cuota diaria superada")


def no_autorizado() -> QubiaError:
    return QubiaError(status.HTTP_401_UNAUTHORIZED, "No autorizado")
