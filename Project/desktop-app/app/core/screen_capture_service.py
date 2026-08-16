# Servicio de captura de pantalla basado en mss, con salida en formato BGR de OpenCV
# capture_frame alimenta la superposicion completa; capture_region alimenta la lupa

import base64
from typing import Tuple

import cv2
import mss
import numpy as np

# Indice del monitor primario en la lista que expone mss (0 es el area virtual combinada)
PRIMARY_MONITOR_INDEX = 1


# Captura el monitor primario completo y lo devuelve como array BGR
def capture_frame() -> np.ndarray:
    with mss.MSS() as screen:
        primary_monitor = screen.monitors[PRIMARY_MONITOR_INDEX]
        raw_frame = screen.grab(primary_monitor)
        return _convert_to_bgr(raw_frame)


# Captura una region acotada de la pantalla, usada por la lupa del selector de color
def capture_region(x: int, y: int, w: int, h: int) -> np.ndarray:
    region = {"left": x, "top": y, "width": w, "height": h}
    with mss.MSS() as screen:
        raw_frame = screen.grab(region)
        return _convert_to_bgr(raw_frame)


# Ancho y alto del monitor primario, usados para dimensionar la superposicion de pantalla completa
def get_primary_monitor_size() -> Tuple[int, int]:
    with mss.MSS() as screen:
        primary_monitor = screen.monitors[PRIMARY_MONITOR_INDEX]
        return (primary_monitor["width"], primary_monitor["height"])


# Codifica un frame BGR como PNG en base64, listo para ft.Image(src=...)
def encode_frame_as_png_base64(frame: np.ndarray) -> str:
    success, encoded = cv2.imencode(".png", frame)
    if not success:
        raise ValueError("No se pudo codificar el frame como PNG")
    return base64.b64encode(encoded).decode("ascii")


# Codifica un frame BGR como JPEG en base64; medido ~3.5x mas rapido que PNG y menos de la
# mitad del tamano a resolucion completa (usado por la superposicion, no por la lupa)
def encode_frame_as_jpeg_base64(frame: np.ndarray, quality: int = 85) -> str:
    success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not success:
        raise ValueError("No se pudo codificar el frame como JPEG")
    return base64.b64encode(encoded).decode("ascii")


# Convierte el buffer BGRA entregado por mss a un array BGR compatible con OpenCV
def _convert_to_bgr(raw_frame: mss.screenshot.ScreenShot) -> np.ndarray:
    bgra_array = np.array(raw_frame, dtype=np.uint8)
    return cv2.cvtColor(bgra_array, cv2.COLOR_BGRA2BGR)
