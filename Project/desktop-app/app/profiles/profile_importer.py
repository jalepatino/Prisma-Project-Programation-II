# Importacion y validacion de perfiles de vision generados por la plataforma web
# La validacion nunca falla en silencio: siempre lanza ValueError con un mensaje claro

import json
from pathlib import Path
from typing import Union

from app.profiles.profile_model import (
    DEFICIENCY_TYPES,
    PROFILE_SOURCES,
    ColorVisionProfile,
)

# Campos obligatorios exigidos por el esquema compartido de la Seccion 6.1
REQUIRED_FIELDS = ("schema_version", "deficiency_type", "severity", "source", "generated_at")


# Lee un archivo JSON, valida su esquema y devuelve el perfil resultante
def import_profile_from_json(path: Union[str, Path]) -> ColorVisionProfile:
    with open(path, "r", encoding="ascii") as profile_file:
        data = json.load(profile_file)
    validate_profile_schema(data)
    return ColorVisionProfile(
        schema_version=data["schema_version"],
        deficiency_type=data["deficiency_type"],
        severity=float(data["severity"]),
        source=data["source"],
        generated_at=data["generated_at"],
    )


# Verifica que el diccionario tenga todos los campos y tipos esperados por el esquema
def validate_profile_schema(data: dict) -> bool:
    _validate_required_fields(data)
    _validate_deficiency_type(data["deficiency_type"])
    _validate_severity_range(data["severity"])
    _validate_source(data["source"])
    return True


# Confirma que ningun campo obligatorio falte en el diccionario recibido
def _validate_required_fields(data: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError("Faltan campos obligatorios en el perfil: " + ", ".join(missing))


# Confirma que el tipo de deficiencia sea uno de los valores soportados
def _validate_deficiency_type(deficiency_type: object) -> None:
    if deficiency_type not in DEFICIENCY_TYPES:
        raise ValueError("Tipo de deficiencia invalido: " + str(deficiency_type))


# Confirma que la severidad sea numerica y este en el rango 0.0 a 1.0
def _validate_severity_range(severity: object) -> None:
    if not isinstance(severity, (int, float)) or isinstance(severity, bool):
        raise ValueError("La severidad debe ser numerica")
    if severity < 0.0 or severity > 1.0:
        raise ValueError("La severidad debe estar entre 0.0 y 1.0")


# Confirma que el origen declarado sea uno de los valores soportados
def _validate_source(source: object) -> None:
    if source not in PROFILE_SOURCES:
        raise ValueError("Origen de perfil invalido: " + str(source))
