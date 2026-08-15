# Filtro de temperatura de color para fotofobia, independiente de la matriz de daltonismo
# Aproximacion de cuerpo negro de Tanner Helland, sin dependencia de red
# Los frames se esperan en orden BGR, igual que screen_capture_service.capture_frame

import numpy as np

# Rango de temperatura soportado: muy calido a luz de dia neutra
KELVIN_MIN_SUPPORTED = 1000.0
KELVIN_MAX_SUPPORTED = 40000.0


# Convierte un valor Kelvin en multiplicadores de ganancia (r, g, b) entre 0.0 y 1.0
def calculate_kelvin_curve(kelvin: float) -> tuple:
    clamped_kelvin = min(max(kelvin, KELVIN_MIN_SUPPORTED), KELVIN_MAX_SUPPORTED)
    temperature = clamped_kelvin / 100.0
    red = _calculate_red_channel(temperature)
    green = _calculate_green_channel(temperature)
    blue = _calculate_blue_channel(temperature)
    return (red / 255.0, green / 255.0, blue / 255.0)


# Aplica el desplazamiento de temperatura sobre un frame BGR mediante ganancia por canal
def apply_temperature_shift(frame: np.ndarray, kelvin: float) -> np.ndarray:
    red_gain, green_gain, blue_gain = calculate_kelvin_curve(kelvin)
    gains_bgr = np.array([blue_gain, green_gain, red_gain], dtype=np.float64)
    shifted = frame.astype(np.float64) * gains_bgr
    clipped = np.clip(shifted, 0, 255)
    return clipped.astype(frame.dtype)


# Canal rojo de la curva de cuerpo negro; saturado por encima de 6600K aproximados
def _calculate_red_channel(temperature: float) -> float:
    if temperature <= 66:
        return 255.0
    red = 329.698727446 * ((temperature - 60) ** -0.1332047592)
    return _clamp_channel(red)


# Canal verde de la curva de cuerpo negro; formula distinta antes y despues de 6600K
def _calculate_green_channel(temperature: float) -> float:
    if temperature <= 66:
        green = 99.4708025861 * np.log(temperature) - 161.1195681661
    else:
        green = 288.1221695283 * ((temperature - 60) ** -0.0755148492)
    return _clamp_channel(green)


# Canal azul de la curva de cuerpo negro; se anula por debajo de 1900K aproximados
def _calculate_blue_channel(temperature: float) -> float:
    if temperature >= 66:
        return 255.0
    if temperature <= 19:
        return 0.0
    blue = 138.5177312231 * np.log(temperature - 10) - 305.0447927307
    return _clamp_channel(blue)


# Restringe un valor de canal calculado al rango valido 0-255
def _clamp_channel(value: float) -> float:
    return float(min(max(value, 0.0), 255.0))
