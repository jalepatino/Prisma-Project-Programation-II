# Resuelve el nombre legible mas cercano a un color HEX usando el dataset local
# La busqueda es puramente local por vecino mas cercano; nunca hace una peticion de red

import json
from typing import Dict, Tuple


# Carga el dataset de nombres de color desde el archivo JSON indicado
def load_color_dataset(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="ascii") as dataset_file:
        return json.load(dataset_file)


# Encuentra el nombre del color mas cercano en el dataset por distancia euclidiana en RGB
def resolve_color_name(hex_value: str, dataset: Dict[str, str]) -> str:
    target_rgb = _hex_to_rgb(hex_value)
    closest_name = ""
    closest_distance = None
    for candidate_hex, candidate_name in dataset.items():
        distance = _squared_euclidean_distance(target_rgb, _hex_to_rgb(candidate_hex))
        if closest_distance is None or distance < closest_distance:
            closest_distance = distance
            closest_name = candidate_name
    return closest_name


# Convierte un color hexadecimal "#RRGGBB" en una tupla RGB de enteros
def _hex_to_rgb(hex_value: str) -> Tuple[int, int, int]:
    stripped = hex_value.lstrip("#")
    red = int(stripped[0:2], 16)
    green = int(stripped[2:4], 16)
    blue = int(stripped[4:6], 16)
    return (red, green, blue)


# Distancia euclidiana al cuadrado entre dos puntos RGB; se evita la raiz porque solo se compara
def _squared_euclidean_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
