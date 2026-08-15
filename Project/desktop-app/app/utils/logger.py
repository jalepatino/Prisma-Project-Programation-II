# Configuracion centralizada de logging para toda la aplicacion desktop
# Los mensajes se emiten con marca de tiempo, nivel y nombre del modulo de origen

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False


# Devuelve un logger configurado con el formato estandar del proyecto
def get_logger(name: str) -> logging.Logger:
    _ensure_configured()
    return logging.getLogger(name)


# Aplica la configuracion base de logging una sola vez por proceso
def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    _configured = True
