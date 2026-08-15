# Modelo de perfil de vision cromatica compartido entre Desktop y la plataforma Web
# Refleja exactamente el esquema JSON de la Seccion 6.1 de la especificacion

from dataclasses import dataclass

# Tipos de deficiencia soportados por el motor de matrices
DEFICIENCY_TYPES = (
    "deuteranomaly",
    "deuteranopia",
    "tritanomaly",
    "tritanopia",
    "normal",
)

# Origenes posibles de generacion de un perfil
PROFILE_SOURCES = ("manual", "web_ishihara_test", "imported")

# Version de esquema soportada por esta version de la aplicacion
CURRENT_SCHEMA_VERSION = "1.0"


# Perfil inmutable exportable e importable entre el Desktop y la plataforma Web
@dataclass(frozen=True)
class ColorVisionProfile:
    schema_version: str
    deficiency_type: str
    severity: float
    source: str
    generated_at: str
