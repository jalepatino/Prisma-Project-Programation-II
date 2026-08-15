# Persistencia de perfiles de vision como archivos JSON bajo el directorio de configuracion
# Orden CRUD: create_profile -> get_profile -> update_profile -> delete_profile

import dataclasses
import json
from pathlib import Path
from typing import Optional

from app.config.app_config import get_profiles_directory, write_json_atomic
from app.profiles.profile_model import ColorVisionProfile


# Crea un nuevo archivo de perfil; sobrescribe silenciosamente si el identificador ya existe
def create_profile(profile_id: str, profile: ColorVisionProfile) -> None:
    _write_profile_file(_resolve_profile_path(profile_id), profile)


# Lee un perfil por su identificador; devuelve None si el archivo no existe
def get_profile(profile_id: str) -> Optional[ColorVisionProfile]:
    path = _resolve_profile_path(profile_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="ascii") as profile_file:
        data = json.load(profile_file)
    return ColorVisionProfile(**data)


# Reemplaza los datos de un perfil existente por los valores actualizados
def update_profile(profile_id: str, updated: ColorVisionProfile) -> None:
    path = _resolve_profile_path(profile_id)
    if not path.exists():
        raise ValueError("No existe el perfil solicitado: " + profile_id)
    _write_profile_file(path, updated)


# Elimina el archivo de perfil si existe; no falla si ya fue borrado antes
def delete_profile(profile_id: str) -> None:
    path = _resolve_profile_path(profile_id)
    if path.exists():
        path.unlink()


# Resuelve la ruta absoluta del archivo JSON asociado a un identificador de perfil
def _resolve_profile_path(profile_id: str) -> Path:
    return get_profiles_directory() / (profile_id + ".json")


# Serializa el perfil como diccionario y lo escribe en disco de forma atomica
def _write_profile_file(path: Path, profile: ColorVisionProfile) -> None:
    write_json_atomic(path, dataclasses.asdict(profile))
