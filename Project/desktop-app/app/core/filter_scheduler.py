# Calculo local de amanecer/atardecer (algoritmo solar de NOAA) y programador de filtros
# Ciclo de vida: start_schedule_loop -> stop_schedule_loop; nunca hace peticiones de red
# La hora local se aproxima con el desfase UTC actual del sistema (sin base de datos de husos)

import math
import threading
from datetime import date as date_type
from datetime import datetime, time
from typing import Callable, Optional, Tuple

from app.config.app_config import load_config
from app.utils.logger import get_logger

# Angulo cenital solar oficial para orto/ocaso: incluye refraccion atmosferica y radio solar
SOLAR_ZENITH_SUNRISE_SUNSET = 90.833

# Coordenadas de respaldo cuando el usuario no configuro una ubicacion
FALLBACK_COORDINATES = (0.0, 0.0)

# Intervalo entre revisiones del programador, en segundos
SCHEDULE_CHECK_INTERVAL_SECONDS = 60

_logger = get_logger(__name__)
_schedule_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


# Calcula el amanecer y el atardecer locales para una latitud, longitud y fecha dadas
def get_sunrise_sunset(lat: float, lon: float, date: date_type) -> Tuple[time, time]:
    julian_century = _julian_century(date)
    geom_mean_long_sun = _geom_mean_long_sun(julian_century)
    geom_mean_anom_sun = _geom_mean_anom_sun(julian_century)
    eccent_earth_orbit = _eccent_earth_orbit(julian_century)
    sun_eq_of_center = _sun_eq_of_center(julian_century, geom_mean_anom_sun)
    sun_true_long = geom_mean_long_sun + sun_eq_of_center
    sun_app_long = _sun_apparent_long(julian_century, sun_true_long)
    obliq_corr = _obliquity_correction(julian_century)
    sun_declin = _sun_declination(obliq_corr, sun_app_long)
    eq_of_time = _equation_of_time(
        julian_century, obliq_corr, geom_mean_long_sun, geom_mean_anom_sun, eccent_earth_orbit
    )
    hour_angle = _hour_angle_sunrise(lat, sun_declin)
    solar_noon_minutes_utc = 720.0 - 4.0 * lon - eq_of_time
    sunrise_minutes_utc = solar_noon_minutes_utc - hour_angle * 4.0
    sunset_minutes_utc = solar_noon_minutes_utc + hour_angle * 4.0
    utc_offset_minutes = _local_utc_offset_minutes()
    sunrise_time = _minutes_to_local_time(sunrise_minutes_utc, utc_offset_minutes)
    sunset_time = _minutes_to_local_time(sunset_minutes_utc, utc_offset_minutes)
    return (sunrise_time, sunset_time)


# Obtiene las coordenadas configuradas por el usuario; usa un respaldo neutro si no hay ninguna
def get_local_coordinates() -> Tuple[float, float]:
    config = load_config()
    latitude = config.get("latitude")
    longitude = config.get("longitude")
    if latitude is None or longitude is None:
        _logger.warning(
            "No hay coordenadas configuradas; usando el respaldo %s", FALLBACK_COORDINATES
        )
        return FALLBACK_COORDINATES
    return (float(latitude), float(longitude))


# Arranca el hilo dedicado que revisa periodicamente si corresponde activar los filtros
def start_schedule_loop(
    on_activate: Callable[[], None], on_deactivate: Callable[[], None]
) -> None:
    global _schedule_thread
    if _schedule_thread is not None and _schedule_thread.is_alive():
        return
    _stop_event.clear()
    _schedule_thread = threading.Thread(
        target=_run_schedule_loop, args=(on_activate, on_deactivate), daemon=True
    )
    _schedule_thread.start()


# Senala el cierre limpio del hilo del programador y espera su finalizacion
def stop_schedule_loop() -> None:
    global _schedule_thread
    _stop_event.set()
    if _schedule_thread is not None:
        _schedule_thread.join(timeout=2.0)
    _schedule_thread = None


# Bucle interno: compara la hora local contra la ventana nocturna y notifica los cambios de estado
def _run_schedule_loop(
    on_activate: Callable[[], None], on_deactivate: Callable[[], None]
) -> None:
    latitude, longitude = get_local_coordinates()
    is_currently_active = False
    while not _stop_event.is_set():
        today = datetime.now().date()
        sunrise, sunset = get_sunrise_sunset(latitude, longitude, today)
        should_be_active = _is_within_night_window(datetime.now().time(), sunrise, sunset)
        if should_be_active and not is_currently_active:
            is_currently_active = True
            on_activate()
        elif not should_be_active and is_currently_active:
            is_currently_active = False
            on_deactivate()
        _stop_event.wait(SCHEDULE_CHECK_INTERVAL_SECONDS)


# Determina si la hora actual cae despues del ocaso o antes del orto
def _is_within_night_window(now: time, sunrise: time, sunset: time) -> bool:
    return now >= sunset or now < sunrise


# Numero de dia juliano a mediodia UTC para la fecha dada (formula civil estandar)
def _julian_day(date: date_type) -> float:
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    return float(
        date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    )


# Siglo juliano transcurrido desde el 1 de enero de 2000 al mediodia UTC
def _julian_century(date: date_type) -> float:
    return (_julian_day(date) - 2451545.0) / 36525.0


# Longitud media geometrica del Sol, en grados
def _geom_mean_long_sun(t: float) -> float:
    return (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0


# Anomalia media geometrica del Sol, en grados
def _geom_mean_anom_sun(t: float) -> float:
    return 357.52911 + t * (35999.05029 - 0.0001537 * t)


# Excentricidad de la orbita terrestre
def _eccent_earth_orbit(t: float) -> float:
    return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)


# Ecuacion del centro solar, en grados
def _sun_eq_of_center(t: float, geom_mean_anom_sun: float) -> float:
    m_rad = math.radians(geom_mean_anom_sun)
    return (
        math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * m_rad) * (0.019993 - 0.000101 * t)
        + math.sin(3 * m_rad) * 0.000289
    )


# Longitud aparente del Sol, corregida por nutacion y aberracion
def _sun_apparent_long(t: float, sun_true_long: float) -> float:
    return sun_true_long - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * t))


# Oblicuidad media de la ecliptica, en grados
def _mean_obliquity_ecliptic(t: float) -> float:
    seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
    return 23.0 + (26.0 + seconds / 60.0) / 60.0


# Oblicuidad de la ecliptica corregida por nutacion
def _obliquity_correction(t: float) -> float:
    return _mean_obliquity_ecliptic(t) + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * t))


# Declinacion solar, en grados
def _sun_declination(obliq_corr: float, sun_app_long: float) -> float:
    sin_declin = math.sin(math.radians(obliq_corr)) * math.sin(math.radians(sun_app_long))
    return math.degrees(math.asin(sin_declin))


# Ecuacion del tiempo, en minutos: diferencia entre el tiempo solar real y el tiempo solar medio
def _equation_of_time(
    t: float,
    obliq_corr: float,
    geom_mean_long_sun: float,
    geom_mean_anom_sun: float,
    eccent_earth_orbit: float,
) -> float:
    var_y = math.tan(math.radians(obliq_corr) / 2.0) ** 2
    l0_rad = math.radians(geom_mean_long_sun)
    m_rad = math.radians(geom_mean_anom_sun)
    result = (
        var_y * math.sin(2 * l0_rad)
        - 2 * eccent_earth_orbit * math.sin(m_rad)
        + 4 * eccent_earth_orbit * var_y * math.sin(m_rad) * math.cos(2 * l0_rad)
        - 0.5 * var_y * var_y * math.sin(4 * l0_rad)
        - 1.25 * eccent_earth_orbit * eccent_earth_orbit * math.sin(2 * m_rad)
    )
    return 4.0 * math.degrees(result)


# Angulo horario del orto/ocaso, en grados, para la latitud y declinacion dadas
def _hour_angle_sunrise(lat: float, sun_declin: float) -> float:
    lat_rad = math.radians(lat)
    declin_rad = math.radians(sun_declin)
    cos_hour_angle = math.cos(math.radians(SOLAR_ZENITH_SUNRISE_SUNSET)) / (
        math.cos(lat_rad) * math.cos(declin_rad)
    ) - math.tan(lat_rad) * math.tan(declin_rad)
    # Se recorta al rango valido de acos; en latitudes polares el sol no cruza el horizonte
    clamped = min(max(cos_hour_angle, -1.0), 1.0)
    return math.degrees(math.acos(clamped))


# Desfase UTC actual del sistema local, en minutos (aproximacion sin base de datos de husos)
def _local_utc_offset_minutes() -> float:
    local_offset = datetime.now().astimezone().utcoffset()
    return local_offset.total_seconds() / 60.0 if local_offset is not None else 0.0


# Convierte minutos UTC desde medianoche a una hora local, envolviendo dentro de un dia
def _minutes_to_local_time(minutes_utc: float, utc_offset_minutes: float) -> time:
    total_minutes = (minutes_utc + utc_offset_minutes) % 1440.0
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return time(hour=hours, minute=minutes)
