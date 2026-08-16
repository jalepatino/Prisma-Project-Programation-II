# Resuelve rutas a datos empaquetados, funcionando desde codigo fuente y desde el
# ejecutable de PyInstaller, que extrae los datos declarados en datas= bajo sys._MEIPASS
# __file__ no es un camino de sistema de archivos normal para modulos congelados,
# por eso no se puede seguir usando Path(__file__).resolve().parents[N] una vez empaquetado

import sys
from pathlib import Path


# Indica si el proceso corre como ejecutable congelado de PyInstaller
def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")


# Resuelve una ruta relativa a la raiz del monorepo, en codigo fuente o empaquetada
def resolve_shared_resource(relative_path: str) -> Path:
    if is_frozen():
        return Path(sys._MEIPASS) / relative_path
    # Desde codigo fuente, la raiz del monorepo esta tres niveles sobre este archivo
    return Path(__file__).resolve().parents[3] / relative_path
