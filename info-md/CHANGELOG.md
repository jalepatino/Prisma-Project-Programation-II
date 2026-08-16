# CHANGELOG — ChromaticVision Desktop

---

## Fase 7 — GUIDE.md y documentacion final — 2026-08-16

### Archivos creados
- `GUIDE.md` (raiz del monorepo, `Project/GUIDE.md`) — mapa de directorios
  completo (Proposito/Funciones/Conexiones por cada uno de los ~35 archivos
  `.py` significativos de las Fases 0-6), orden de lectura sugerido,
  glosario en espanol accesible, diagrama ASCII del modelo de hilos, y una
  seccion final que resume las divergencias reales respecto al spec
  original con referencia a la entrada del CHANGELOG que las documenta en
  detalle

### Decisiones de esta fase
- Antes de escribir una sola linea de `GUIDE.md`, se releyo el CHANGELOG
  completo (Fases 1-6) y se releyeron los cinco archivos con mas historial
  de cambios (`main.py`, `main_window.py`, `filters_view.py`,
  `settings_view.py`, `picker_view.py`) para confirmar su estado final
  exacto, en vez de documentar de memoria. `GUIDE.md` describe el codigo
  **tal como quedo construido**, con sus divergencias de API y decisiones
  de rendimiento reales, no la version idealizada del spec original —
  siguiendo instruccion explicita para esta fase
- Correccion de ubicacion: `GUIDE.md` se escribio primero en la raiz del
  repositorio Git (`ProyectoDaltonismo/GUIDE.md`), pero esa raiz tambien
  contiene `info-md/` y un `README.md` de plantilla ajenos al monorepo
  descrito en la Seccion 7 del spec. La raiz real equivalente a
  `chromaticvision-suite/` es `Project/` (contiene `desktop-app/` y
  `shared-color-science/` como hermanos directos, igual que el spec). Se
  movio a `Project/GUIDE.md` antes de confirmar la fase como completa

### Dependencias agregadas
- ninguna (fase de documentacion, sin cambios de codigo)

### Limitaciones conocidas
- Ninguna bloqueante; `GUIDE.md` es un documento vivo segun la Seccion 9 del
  spec y debera actualizarse si se agregan fases futuras

---

## Fase 6 — Empaquetado PyInstaller y pulido final — 2026-08-16

### Archivos creados
- `build.spec` — configuracion de PyInstaller en modo onefile (`ChromaticVision.exe`)
- `assets/icons/generate_icon.py` — genera `app.ico` (multi-resolucion) y `app.png` con Pillow; circulo azul y "C" blanca centrada
- `app/utils/resource_path.py` — resuelve rutas a datos empaquetados, funcionando desde codigo fuente y desde el ejecutable congelado
- `README.md` — guia de usuario en espanol: requisitos, instalacion, ejecucion desde fuente, build, vistas y atajos

### Archivos modificados
- `app/core/color_matrix_engine.py`, `app/picker/color_picker_service.py` — usan `resolve_shared_resource()` en vez de `Path(__file__).resolve().parents[N]`
- `app/core/overlay_renderer.py` — el pipeline completo (matriz + temperatura + brillo/contraste) ahora corre sobre una copia reducida del frame (`RENDER_SCALE_FACTOR = 0.5`) y el resultado se reescala a la resolucion original antes de entregarse
- `main.py` — `initialize_page()` y `run_application()` ahora son corrutinas que esperan (`await`) `page.window.center()`
- `app/ui/views/filters_view.py`, `app/ui/views/settings_view.py` — nuevos `set_filter_state()` y `set_preferences()` para restaurar el estado tras reconstruir la vista
- `app/ui/main_window.py` — `toggle_theme()` captura el estado de Filtros y Ajustes antes de reconstruir el shell y lo restaura despues

### Dependencias agregadas
- `pyinstaller==6.22.1` (ya estaba listado como necesario para esta fase); `requirements.txt` regenerado con `pip freeze`, que ahora tambien captura las dependencias transitivas de PyInstaller (`altgraph`, `pefile`, `pywin32-ctypes`, `pyinstaller-hooks-contrib`, `packaging`, `setuptools`)

### Bugs reales atrapados al compilar y EJECUTAR el .exe (no solo compilarlo)
Compilar sin errores no prueba que el ejecutable funcione: lo confirme lanzando el
`.exe` real y tomando una captura de pantalla de la ventana renderizada, no solo
verificando que el proceso no terminara.

1. **Rutas basadas en `Path(__file__).resolve().parents[N]` no funcionan congeladas.**
   PyInstaller mantiene la mayoria de los modulos Python puros dentro del archivo
   PYZ comprimido en vez de extraerlos como archivos sueltos; `__file__` para esos
   modulos no se comporta como una ruta de sistema de archivos normal. El primer
   intento de build fallo al arrancar (`color_matrix_engine.py` no podia ubicar
   `shared-color-science/color_matrix_reference.json`, detectado antes de ejecutar
   por inspeccion de codigo). Se corrigio con `resource_path.py`, que usa
   `sys._MEIPASS` como raiz cuando el proceso esta congelado.
2. **`flet` no tiene hook propio de PyInstaller.** El primer intento de EJECUTAR el
   `.exe` (build exitoso, pero la app fallaba al abrir) lanzo
   `FileNotFoundError: ...flet\controls\material\icons.json` porque PyInstaller no
   sabia que ese archivo de datos interno del paquete debia empaquetarse. Se
   corrigio agregando `collect_data_files("flet")` a `build.spec`.
3. **`page.window.center()` nunca se esperaba (`await`).** Es una corrutina desde
   que se investigo su API en la Fase 2 (igual que `close()`, `destroy()`,
   `to_front()`), pero `main.py` la llamaba de forma sincrona desde la Fase 0 y
   ningun test lo detecto porque los dobles de prueba (`FakeWindow.center`) siempre
   fueron metodos sincronos. Solo aparecio como `RuntimeWarning: coroutine
   'Window.center' was never awaited` al ejecutar el `.exe` real. Corregido
   convirtiendo `initialize_page()` y `run_application()` en corrutinas.

### Rendimiento del overlay: medido, no asumido
Se perfilo cada etapa del pipeline por separado antes de decidir que optimizar
(`capture_frame`, conversion BGR/RGB, `apply_color_matrix`, `apply_temperature_shift`,
`_apply_brightness_contrast`), en vez de asumir donde estaba el costo:

| Etapa (1920x1080) | Costo medido |
|---|---|
| `capture_frame` (mss) | ~35-58 ms |
| `apply_color_matrix` | ~70 ms |
| `apply_temperature_shift` | ~63 ms |
| `_apply_brightness_contrast` | ~102 ms (la mas cara, no la matriz CVD) |

Con el pipeline completo activo (matriz + temperatura + brillo/contraste), el FPS
real medido era de **2.0 FPS** a resolucion completa — mas bajo que el ~10 FPS de
la Fase 1, porque esa medicion original no incluia la capa de filtros de la Fase 4.

**Nota importante sobre la premisa de esta fase:** compilar con PyInstaller no
mejora el rendimiento del bucle en caliente. PyInstaller empaqueta el interprete
CPython estandar junto con el bytecode de la app; no compila Python a codigo
maquina nativo. numpy y OpenCV ya son extensiones C compiladas de antemano, asi
que su velocidad es identica corriendo desde `python main.py` o desde el `.exe`.
Verificado: el FPS medido en ambos casos es equivalente dentro del margen de
error de la medicion.

**Fix aplicado (segun lo indicado, sin reescribir el motor de matrices):** el
pipeline completo ahora corre sobre un frame reducido a `RENDER_SCALE_FACTOR = 0.5`
(960x540 en un monitor 1920x1080), y el resultado se reescala de vuelta a la
resolucion original antes de entregarse al `frame_sink`. Brillo/contraste
sigue implementado como `np.clip` + multiplicador escalar (nunca como matriz
diagonal), simplemente ahora corre sobre menos pixeles.

**Resultado medido tras el fix: 8.0 FPS** (mejora de 4x sobre los 2.0 FPS
originales). Sigue por debajo del objetivo de 30 FPS. La causa raiz reportada
con honestidad: la captura de pantalla en si (`mss`, ~35-58 ms/frame a resolucion
completa) es ya el costo individual mas grande y es en gran parte irreducible,
porque mss no admite reescalar durante la captura — solo recortar el area
capturada, lo cual cambiaria la funcionalidad (ya no seria una superposicion de
pantalla completa). Llegar a 30 FPS de forma sostenida requeriria un enfoque
distinto (por ejemplo, un shader en GPU o una libreria de captura con
downsampling nativo), fuera del alcance de "no reescribir el motor de matrices"
que fijo esta fase. Documentado como limitacion conocida, no oculto.

### Otras decisiones arquitectonicas
- `toggle_theme()` (advertencia abierta desde la revision de la Fase 0) ya no
  descarta el estado de `FiltersView` ni de `SettingsView`: se captura con
  `get_filter_state()`/`get_preferences()` antes de `_build_shell()` y se
  restaura con los nuevos `set_filter_state()`/`set_preferences()` despues.
  Verificado con una prueba que confirma que el estado sobrevive al cambio de
  tema y que el resumen del panel refleja los filtros restaurados
- El icono de bandeja y el `.ico` del ejecutable comparten el mismo color de
  acento (`#0071E3`) que la paleta clara del sistema de diseno, por consistencia
  visual entre ambos

### Limitaciones conocidas
- El overlay sostiene ~8 FPS reales a 1920x1080 con el pipeline completo activo,
  por debajo del objetivo de 30 FPS de la Seccion 4.4 del spec. Ver la seccion de
  rendimiento arriba para el analisis completo y la causa raiz
- El primer lanzamiento del `.exe` en una maquina sin el cliente Flet Desktop en
  cache (`%USERPROFILE%\.flet\client\`) requeriria conexion a internet para
  descargarlo; en esta maquina ya estaba en cache de una instalacion previa de
  `flet`, por lo que no se pudo verificar ese camino especifico

---

## Fase 5 — Integracion de perfiles y configuracion persistente — 2026-08-16

### Archivos modificados
- `app/ui/views/settings_view.py` — importar/exportar perfil via `FilePicker`, persistencia de preferencias en cada cambio, restauracion en `activate()`, toasts no bloqueantes con icono + color
- `app/ui/main_window.py` — nuevo `on_profile_changed()`: refresca el panel, publica la matriz activa en `overlay_renderer` y sincroniza la bandeja; se invoca al arrancar si hay un perfil guardado
- `main.py` — aplica `launch_on_startup` (registro de Windows `HKCU\...\Run`) y `start_minimized` (oculta la ventana) al arrancar, leidos de la configuracion persistida

### Dependencias agregadas
- ninguna nueva (`winreg` es modulo estandar de Windows); `requirements.txt` regenerado con `pip freeze`

### Decisiones arquitectonicas
- El perfil activo del escritorio se persiste bajo un identificador fijo (`ACTIVE_PROFILE_ID = "active"`) en vez de un UUID por importacion, ya que el spec modela un unico perfil activo a la vez (Seccion 6.1); cada importacion sobrescribe el mismo archivo en vez de acumular perfiles huerfanos en disco
- `SettingsView` no recibe una referencia directa a `MainWindow`; en su lugar expone `set_profile_changed_callback()`, y `MainWindow._create_views()` la vincula a `self.on_profile_changed` tras crear las vistas — mismo patron de inyeccion por metodo que `set_tray_icon()` desde la Fase 2, sin tocar la firma comun de `BaseView.__init__`
- La exportacion usa `dataclasses.asdict(profile)` directamente: como `ColorVisionProfile` ya es un espejo exacto del esquema de la Seccion 6.1 (decision de la Fase 1), no hace falta un mapeo manual de campos
- `_handle_preference_change` hace lectura-fusion-escritura (`load_config()` + `update()` + `save_config()`) en vez de guardar solo `get_preferences()` directamente: guardar unicamente esas 3 claves habria sobrescrito `config.json` completo, perdiendo `active_profile_id`, `latitude`/`longitude` y `correction_active` en cada cambio de un switch. Verificado con una prueba que confirma que esas claves sobreviven

### Bugs de API reales atrapados por pruebas propias (no por el smoke test del prompt)
- `ft.Dropdown` no acepta `on_change` en Flet 0.86.5 — el evento correcto es `on_select`. Sin la prueba de instanciacion completa de `SettingsView`, esto habria fallado recien en tiempo de ejecucion real

### Limitaciones conocidas
- Activar "Iniciar con el sistema" desde Ajustes escribe la preferencia en `config.json` de inmediato, pero el registro de Windows solo se sincroniza la proxima vez que arranca la aplicacion (`apply_startup_preference` corre en `main.py`, no en el manejador del switch) — coherente con el alcance de la Fase 5 (`main.py`: "Load config on startup and apply"), documentado por transparencia
- Los dialogos de `FilePicker` (importar/exportar) requieren una ventana Flet real; no son verificables de extremo a extremo en un entorno headless. Se probo toda la logica circundante (validacion, persistencia, callback, toasts) sustituyendo `pick_files`/`save_file` por dobles de prueba

---

## Fase 4 — Filtro de luz azul y programador de ocaso — 2026-08-16

### Archivos creados
- `app/core/filter_scheduler.py` — calculo de amanecer/atardecer (algoritmo solar NOAA) y bucle de programacion en hilo dedicado
- `app/utils/logger.py` — configuracion centralizada de logging (previsto en la Seccion 4.3 del spec, usado por primera vez en esta fase)

### Archivos modificados
- `app/core/overlay_renderer.py` — nueva cola de estado de filtros, `update_filter_state()`, `is_render_loop_running()`; la capa de temperatura/brillo/contraste se aplica DESPUES de la matriz CVD
- `app/ui/views/filters_view.py` — los tres sliders publican su estado en `overlay_renderer`; el interruptor de programacion arranca/detiene `filter_scheduler`; nueva etiqueta de estado ("Activo..."/"En espera...")
- `app/ui/main_window.py` — se elimino el mezclado de temperatura en la matriz de correccion (ahora redundante con la nueva capa de filtros de la Fase 4); `_handle_correction_toggle` publica el estado de filtros por separado
- `app/config/app_config.py` — se agregaron las claves `latitude`/`longitude` al esquema de configuracion, consumidas por `filter_scheduler.get_local_coordinates()`

### Dependencias agregadas
- ninguna nueva (numpy y opencv-python ya instalados); `requirements.txt` regenerado con `pip freeze` para fijar el entorno completo

### Decisiones arquitectonicas
- La hora "local" del amanecer/atardecer se aproxima con el desfase UTC actual del sistema operativo (`datetime.now().astimezone()`), no con una base de datos de husos horarios por coordenada, ya que esta fase no agrega dependencias nuevas
- `filter_scheduler` usa `threading.Event.wait(60)` en vez de `time.sleep(60)`, para que `stop_schedule_loop()` responda de inmediato en vez de esperar hasta el proximo minuto
- Al activar el filtro por programacion, si el hilo de superposicion no esta corriendo (porque la correccion CVD manual esta apagada), se arranca igualmente con matriz identidad — el filtro de luz azul es independiente de la correccion CVD, segun la Seccion 4.2.3 del spec
- Al desactivar por programacion NO se detiene el hilo de superposicion (podria estar sosteniendo una correccion CVD activa por separado); en su lugar se publica un estado de filtro neutro (sin efecto visible)
- Correccion de un doble conteo: la Fase 1 mezclaba la ganancia de temperatura directamente en la matriz de correccion CVD como parche temporal; ahora que existe la capa de filtros apilable real de la Fase 4, ese mezclado se elimino de `main_window.py` para evitar aplicar la temperatura dos veces

### Limitaciones conocidas
- En latitudes cercanas al circulo polar durante el sol de medianoche (dia de 24 horas), `get_sunrise_sunset()` no puede representar "nunca se pone el sol" como un par `(hora, hora)` dentro de un mismo dia calendario; el amanecer y el ocaso calculados colapsan al mismo valor. Verificado como limitacion inherente del tipo de retorno exigido por el spec, no como error de la formula solar (validado contra Madrid: amanecer/atardecer del solsticio de verano coinciden con valores publicados reales dentro de 1 minuto de precision)
- El programador no se detiene automaticamente al cerrar la aplicacion desde la bandeja (`tray_menu_actions.handle_exit` no fue modificado en esta fase); al ser un hilo daemon, se termina igualmente con el proceso, sin bloquear el cierre

---

## Fase 3 — Selector de color y lupa en vivo — 2026-08-15

### Archivos creados
- `app/picker/__init__.py` — paquete del modulo picker
- `app/picker/color_name_resolver.py` — resolucion de nombre de color por vecino mas cercano en espacio RGB
- `app/picker/color_picker_service.py` — bucle de captura de cursor a 60 FPS en hilo dedicado
- `app/picker/data/color_names.json` — 161 entradas HEX->nombre unicas (CSS/X11 extendido + curado)

### Archivos modificados
- `app/ui/views/picker_view.py` — reescrito para usar el bucle en vivo via `run_task`

### Dependencias agregadas
- ninguna nueva (mss ya instalado desde Fase 1)

### Decisiones arquitectonicas
- El callback del picker nunca toca la UI directamente: agenda `_apply_picker_sample` via `page.run_task()` para respetar el loop de eventos de Flet (mismo patron que la bandeja en Fase 2)
- Se agrego `get_last_cursor_position()` para implementar correctamente el "congelar y copiar" — al hacer clic en el boton el cursor ya se movio, por lo que se usa la ultima posicion observada por el bucle, no la posicion actual
- Posicion del cursor via `ctypes.windll.user32.GetCursorPos` (stdlib puro, sin dependencia nueva), consistente con el enfoque Windows-only del proyecto
- `page.clipboard.set()` en vez de `page.set_clipboard()` — API correcta en Flet 0.86.5
- `ft.Image.src` en vez de `src_base64` — ya corregido desde Fase 1, mantenido

### Limitaciones conocidas
- La lupa muestra la region ampliada sin correccion de color aplicada — la integracion con el motor de correccion queda para la Fase 5 cuando el perfil activo este completamente cableado

---

## Fase 2 — Bandeja del sistema — 2026-08-15

### Archivos creados
- `app/tray/__init__.py` — paquete del modulo tray
- `app/tray/tray_service.py` — ciclo de vida del icono de bandeja con pystray
- `app/tray/tray_menu_actions.py` — manejadores de cada item del menu

### Archivos modificados
- `main.py` — arranque del icono de bandeja en hilo daemon + cierre a bandeja en vez de salir
- `app/ui/main_window.py` — `set_tray_icon()` + sincronizacion del checkmark en `_handle_correction_toggle`

### Dependencias agregadas
- `pystray==0.19.5` — icono y menu de bandeja del sistema en Windows
- `pillow==12.3.0` — generacion programatica del icono de bandeja

### Decisiones arquitectonicas
- `page.window.on_close` no existe en Flet 0.86.x; se usa `page.window.on_event` con `event.type == ft.WindowEventType.CLOSE` y `page.window.prevent_close = True`
- Los clics del menu de pystray llegan en hilo sincrono ajeno al loop de Flet; se usa `page.run_task()` como unico puente thread-safe confirmado
- `handle_exit` llama `icon.stop()` directamente para evitar import circular entre `tray_service` y `tray_menu_actions`
- La ultima matriz de correccion se recuerda en `_current_matrix` dentro de `tray_menu_actions` para reutilizarla al reactivar la correccion desde la bandeja
- El submenu de cambio rapido aplica severidad 1.0 (dicromacia total); el ajuste fino queda en la ventana principal

### Limitaciones conocidas
- Ninguna bloqueante para fases siguientes

---

## Fase 1 — Motor de nucleo — 2026-08-15

### Archivos creados
- `shared-color-science/color_matrix_reference.json` — coeficientes Machado 2009, variantes simulate y correct para los 4 tipos de deficiencia
- `app/core/__init__.py`
- `app/core/color_matrix_engine.py` — construccion, interpolacion y aplicacion de matrices de correccion CVD
- `app/core/screen_capture_service.py` — captura de pantalla completa y region via mss
- `app/core/overlay_renderer.py` — bucle de render en hilo dedicado con queue thread-safe
- `app/core/color_temperature.py` — curva Kelvin (algoritmo Tanner Helland) y shift de temperatura
- `app/profiles/__init__.py`
- `app/profiles/profile_model.py` — dataclass ColorVisionProfile (espejo del esquema JSON Seccion 6.1)
- `app/profiles/profile_service.py` — CRUD de perfiles persistidos como JSON
- `app/profiles/profile_importer.py` — importacion y validacion de esquema con ValueError explicito
- `app/config/app_config.py` — carga y escritura atomica de configuracion local

### Archivos modificados
- `app/ui/main_window.py` — wiring minimo: resumen del panel + arranque/parada del overlay
- `app/ui/views/picker_view.py` — captura estatica en activate() (reemplazada en Fase 3)
- `requirements.txt` — creado con numpy, opencv-python, mss, flet

### Dependencias agregadas
- `numpy` — operaciones matriciales vectorizadas
- `opencv-python` — procesamiento de frames BGR
- `mss` — captura de pantalla de alta velocidad

### Decisiones arquitectonicas
- `apply_color_matrix()` es agnostico de orden de canal; `overlay_renderer` hace la conversion BGR<->RGB
- Matrices de correccion derivadas matematicamente via daltonizacion lineal (Fidaner), no solo literatura
- deuteranomaly/deuteranopia comparten matriz base; la severidad los distingue (interpolacion 0.0-1.0)
- Temperatura de color se combina como matriz diagonal antes de arrancar el hilo de overlay
- Brillo/contraste NO implementados aun — no son operaciones 3x3 puras (pendiente Fase 4/6)
- `ColorVisionProfile` sin campo `id` — el `profile_id` lo gestiona `profile_service` como nombre de archivo

### Limitaciones conocidas
- El overlay sostiene ~10 FPS a 1920x1080 en Python puro, por debajo del objetivo de 30 FPS de la Seccion 4.4. Se abordara en Fase 6 con captura a resolucion reducida tras el build de PyInstaller

---
