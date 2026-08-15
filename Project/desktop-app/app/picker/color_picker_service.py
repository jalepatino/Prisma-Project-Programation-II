# Bucle de muestreo del selector de color: captura la region bajo el cursor a alta frecuencia
# Ciclo de vida: start_picker_loop -> stop_picker_loop; sample_pixel es una captura puntual

import ctypes
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import numpy as np

from app.core.screen_capture_service import capture_region
from app.picker.color_name_resolver import load_color_dataset, resolve_color_name

# Callback invocado en cada muestra: (hex_value, rgb_value, color_name, frame_region)
PickerCallback = Callable[[str, str, str, np.ndarray], None]

# Ruta del dataset de nombres empaquetado junto al modulo
COLOR_DATASET_PATH = Path(__file__).resolve().parent / "data" / "color_names.json"

# Posicion de reserva cuando el cursor no puede consultarse (limite del sistema operativo)
FALLBACK_CURSOR_POSITION = (0, 0)

_picker_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_color_dataset: Optional[Dict[str, str]] = None
_last_cursor_position: Tuple[int, int] = FALLBACK_CURSOR_POSITION


# Arranca el hilo dedicado que muestrea la region bajo el cursor y notifica al callback
def start_picker_loop(callback: PickerCallback, region_size: int = 120, fps: int = 60) -> None:
    global _picker_thread
    if _picker_thread is not None and _picker_thread.is_alive():
        return
    _stop_event.clear()
    _picker_thread = threading.Thread(
        target=_run_picker_loop, args=(callback, region_size, fps), daemon=True
    )
    _picker_thread.start()


# Senala el cierre limpio del hilo del picker y espera su finalizacion
def stop_picker_loop() -> None:
    global _picker_thread
    _stop_event.set()
    if _picker_thread is not None:
        _picker_thread.join(timeout=2.0)
    _picker_thread = None


# Captura puntual de un pixel en pantalla; usada por la accion "congelar y copiar"
def sample_pixel(x: int, y: int) -> Tuple[str, str]:
    frame = capture_region(x, y, 1, 1)
    return _pixel_to_hex_rgb(frame[0, 0])


# Ultima posicion de cursor observada por el bucle en vivo; usada para congelar la muestra actual
def get_last_cursor_position() -> Tuple[int, int]:
    return _last_cursor_position


# Bucle interno del hilo dedicado: captura, resuelve el nombre y notifica al callback
def _run_picker_loop(callback: PickerCallback, region_size: int, fps: int) -> None:
    global _last_cursor_position
    dataset = _get_color_dataset()
    frame_budget_seconds = 1.0 / fps
    half_region = region_size // 2
    while not _stop_event.is_set():
        loop_started_at = time.perf_counter()
        cursor_x, cursor_y = _get_cursor_position()
        _last_cursor_position = (cursor_x, cursor_y)
        frame_region = capture_region(
            cursor_x - half_region, cursor_y - half_region, region_size, region_size
        )
        hex_value, rgb_value = _pixel_to_hex_rgb(frame_region[half_region, half_region])
        color_name = resolve_color_name(hex_value, dataset)
        callback(hex_value, rgb_value, color_name, frame_region)
        _sleep_for_remaining_budget(loop_started_at, frame_budget_seconds)


# Carga el dataset de nombres una sola vez al arrancar y lo cachea para el resto de la sesion
def _get_color_dataset() -> Dict[str, str]:
    global _color_dataset
    if _color_dataset is None:
        _color_dataset = load_color_dataset(str(COLOR_DATASET_PATH))
    return _color_dataset


# Obtiene la posicion actual del cursor en coordenadas de pantalla via la API nativa de Windows
def _get_cursor_position() -> Tuple[int, int]:
    point = wintypes.POINT()
    if not ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        return FALLBACK_CURSOR_POSITION
    return (point.x, point.y)


# Convierte el pixel BGR capturado en sus representaciones de texto HEX y RGB
def _pixel_to_hex_rgb(pixel: np.ndarray) -> Tuple[str, str]:
    blue, green, red = int(pixel[0]), int(pixel[1]), int(pixel[2])
    hex_value = "#{:02X}{:02X}{:02X}".format(red, green, blue)
    rgb_value = "rgb({}, {}, {})".format(red, green, blue)
    return (hex_value, rgb_value)


# Duerme el tiempo restante del presupuesto de frame para respetar el FPS objetivo
def _sleep_for_remaining_budget(loop_started_at: float, frame_budget_seconds: float) -> None:
    elapsed = time.perf_counter() - loop_started_at
    remaining = frame_budget_seconds - elapsed
    if remaining > 0:
        time.sleep(remaining)
