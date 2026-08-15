# Motor de matrices de simulacion y correccion de daltonismo
# Unica fuente de coeficientes: shared-color-science/color_matrix_reference.json
# Los frames y las matrices deben compartir el mismo orden de canal (RGB); la
# conversion desde el BGR nativo de OpenCV es responsabilidad del llamador

import json
from pathlib import Path
from typing import Optional

import numpy as np

from app.profiles.profile_model import ColorVisionProfile

# Modos de matriz soportados por build_matrix_for_profile
MATRIX_MODES = ("simulate", "correct")

# Ruta al archivo de coeficientes compartido con la plataforma web
COLOR_MATRIX_REFERENCE_PATH = (
    Path(__file__).resolve().parents[3] / "shared-color-science" / "color_matrix_reference.json"
)

# Matriz neutra usada como punto de partida de la interpolacion de severidad
IDENTITY_MATRIX = np.eye(3, dtype=np.float64)

# Cache en memoria del archivo de referencia, cargado una sola vez por proceso
_matrix_reference_cache: Optional[dict] = None


# Aplica una matriz de color 3x3 sobre cada pixel del frame, sin efectos secundarios
def apply_color_matrix(frame: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    pixels = frame.reshape(-1, frame.shape[-1]).astype(np.float64)
    transformed = pixels @ np.asarray(matrix, dtype=np.float64).T
    clipped = np.clip(transformed, 0, 255)
    return clipped.reshape(frame.shape).astype(frame.dtype)


# Interpola linealmente entre la matriz identidad y la matriz de deficiencia completa
def interpolate_severity(
    identity: np.ndarray, full_matrix: np.ndarray, severity: float
) -> np.ndarray:
    clamped_severity = min(max(severity, 0.0), 1.0)
    return identity + (np.asarray(full_matrix) - identity) * clamped_severity


# Construye la matriz final para un perfil y modo dados, ya interpolada por severidad
def build_matrix_for_profile(profile: ColorVisionProfile, mode: str) -> np.ndarray:
    if mode not in MATRIX_MODES:
        raise ValueError("Modo de matriz invalido: " + str(mode))
    if profile.deficiency_type == "normal":
        return IDENTITY_MATRIX.copy()
    full_matrix = np.array(_get_deficiency_entry(profile.deficiency_type)[mode], dtype=np.float64)
    return interpolate_severity(IDENTITY_MATRIX, full_matrix, profile.severity)


# Simula sobre un frame como percibe la escena capturada un perfil con deficiencia
def simulate_deficiency(frame: np.ndarray, profile: ColorVisionProfile) -> np.ndarray:
    matrix = build_matrix_for_profile(profile, "simulate")
    return apply_color_matrix(frame, matrix)


# Carga y cachea en memoria el archivo de referencia compartido con la plataforma web
def _load_matrix_reference() -> dict:
    global _matrix_reference_cache
    if _matrix_reference_cache is None:
        with open(COLOR_MATRIX_REFERENCE_PATH, "r", encoding="ascii") as reference_file:
            _matrix_reference_cache = json.load(reference_file)
    return _matrix_reference_cache


# Devuelve el bloque simulate/correct del tipo de deficiencia solicitado
def _get_deficiency_entry(deficiency_type: str) -> dict:
    matrices = _load_matrix_reference()["deficiency_matrices"]
    if deficiency_type not in matrices:
        raise ValueError("Tipo de deficiencia no soportado: " + deficiency_type)
    return matrices[deficiency_type]
