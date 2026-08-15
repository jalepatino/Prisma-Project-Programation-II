# Persistencia de la configuracion local de la aplicacion en disco
# Fuente unica de la ruta del directorio de configuracion consumida por otros modulos

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from app.config.constants import APP_NAME

# Valores por defecto devueltos cuando aun no existe un archivo de configuracion
DEFAULT_CONFIG: Dict[str, Any] = {
    "start_minimized": True,
    "launch_on_startup": False,
    "startup_target": "Ventana principal",
    "active_profile_id": None,
    "correction_active": False,
    "latitude": None,
    "longitude": None,
}


# Lee la configuracion persistida; devuelve los valores por defecto si no existe el archivo
def load_config() -> Dict[str, Any]:
    path = get_config_file_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    with open(path, "r", encoding="ascii") as config_file:
        data = json.load(config_file)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


# Escribe la configuracion en disco de forma atomica
def save_config(data: Dict[str, Any]) -> None:
    write_json_atomic(get_config_file_path(), data)


# Ruta del archivo de configuracion principal dentro del directorio de la aplicacion
def get_config_file_path() -> Path:
    return get_config_directory() / "config.json"


# Directorio donde se guardan los perfiles de vision locales
def get_profiles_directory() -> Path:
    return get_config_directory() / "profiles"


# Resuelve el directorio raiz de configuracion segun el sistema operativo
def get_config_directory() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / ".config" / APP_NAME


# Escribe un diccionario como JSON de forma atomica: archivo temporal y renombrado
def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _write_temp_file(path.parent, data)
    os.replace(temp_path, path)


# Crea el archivo temporal en el mismo directorio destino para que el renombrado sea atomico
def _write_temp_file(directory: Path, data: Dict[str, Any]) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="ascii", dir=directory, delete=False, suffix=".tmp"
    ) as temp_file:
        json.dump(data, temp_file, indent=2)
        return Path(temp_file.name)
