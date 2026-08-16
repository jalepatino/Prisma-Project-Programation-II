# GUIDE.md — ChromaticVision Suite (Desktop)

Guia de estudio del codigo, organizada por directorio, tal como exige la
Seccion 9 de `ProjectDaltonism.md`. Cubre el arbol completo de las Fases 0-6.

Este documento describe el codigo **tal como quedo construido**, no la version
ideal del spec original. Donde la implementacion real se aparto del plan (una
API de Flet que no existia como se esperaba, un problema de rendimiento, un
patron de hilos necesario que el spec no anticipaba), se explica aqui y se
referencia la entrada correspondiente de `info-md/CHANGELOG.md`, que es la
fuente de verdad de esas decisiones fase por fase. Si este documento y el
CHANGELOG alguna vez se contradicen, confia en el CHANGELOG: refleja lo que se
verifico funcionando, no lo que se planeo al principio de cada fase.

Todos los identificadores de codigo se mantienen en ingles, exactamente como
aparecen en los archivos (Seccion 12.3 del spec). La prosa esta en espanol,
con acentos donde corresponde: este archivo es documentacion, no codigo
fuente, asi que no esta sujeto a la regla de ASCII estricto de la Seccion 3.4
(esa regla aplica a los `.py`, verificada por el smoke test de cada fase).

---

## Tabla de contenidos

1. [Mapa de directorios](#1-mapa-de-directorios)
2. [Orden de lectura sugerido](#2-orden-de-lectura-sugerido)
3. [Glosario](#3-glosario)
4. [Diagrama de hilos](#4-diagrama-de-hilos)
5. [Decisiones que se apartaron del spec original](#5-decisiones-que-se-apartaron-del-spec-original)

---

## 1. Mapa de directorios

```
chromaticvision-suite/
├── GUIDE.md                          # este archivo
├── info-md/CHANGELOG.md              # historial de decisiones, fase por fase
├── shared-color-science/
│   └── color_matrix_reference.json
└── desktop-app/
    ├── main.py
    ├── build.spec
    ├── requirements.txt
    ├── README.md
    ├── app/
    │   ├── config/
    │   │   ├── constants.py
    │   │   └── app_config.py
    │   ├── core/
    │   │   ├── color_matrix_engine.py
    │   │   ├── screen_capture_service.py
    │   │   ├── overlay_renderer.py
    │   │   ├── color_temperature.py
    │   │   └── filter_scheduler.py
    │   ├── tray/
    │   │   ├── tray_service.py
    │   │   └── tray_menu_actions.py
    │   ├── picker/
    │   │   ├── color_picker_service.py
    │   │   ├── color_name_resolver.py
    │   │   └── data/color_names.json
    │   ├── profiles/
    │   │   ├── profile_model.py
    │   │   ├── profile_service.py
    │   │   └── profile_importer.py
    │   ├── ui/
    │   │   ├── main_window.py
    │   │   ├── theme/
    │   │   │   ├── design_tokens.py
    │   │   │   └── theme_builder.py
    │   │   ├── components/
    │   │   │   ├── navigation_item.py
    │   │   │   ├── navigation_bar.py
    │   │   │   ├── surface_card.py
    │   │   │   └── app_header.py
    │   │   └── views/
    │   │       ├── base_view.py
    │   │       ├── dashboard_view.py
    │   │       ├── picker_view.py
    │   │       ├── filters_view.py
    │   │       └── settings_view.py
    │   └── utils/
    │       ├── control_sync.py
    │       ├── logger.py
    │       └── resource_path.py
    └── assets/icons/generate_icon.py
```

Los `__init__.py` de cada paquete estan vacios (solo marcan el directorio como
paquete importable); no se documentan individualmente.

---

### `shared-color-science/color_matrix_reference.json`

**Proposito.** Fuente unica de los coeficientes de color que consume el motor
de correccion. Contiene, para cada tipo de deficiencia (`deuteranomaly`,
`deuteranopia`, `tritanomaly`, `tritanopia`), dos matrices 3x3: `simulate`
(como percibe la escena una persona con esa deficiencia, coeficientes de
Machado, Oliveira & Fernandes 2009) y `correct` (matriz de daltonizacion,
derivada matematicamente por formula, no tomada de una tabla). Las claves
`deuteranomaly`/`deuteranopia` comparten la misma matriz base entre si (lo
mismo `tritanomaly`/`tritanopia`); lo que distingue anomalia de dicromacia
completa es unicamente el valor de `severity` del perfil (0.0-1.0),
interpolado contra la matriz identidad en tiempo de ejecucion, nunca un
segundo juego de coeficientes.

**Como se construyo `correct`.** `correction_method` en el propio JSON lo
documenta: `correct = identidad + matriz_de_error (identidad - simulate)`,
donde `matriz_de_error` redistribuye hacia los canales que la persona si
percibe la informacion perdida en el eje afectado (enfoque Fidaner-Walraven-
Grzywacz, el mismo que usan herramientas de daltonizacion como daltonize.js).

**Conexiones.** Lo lee unicamente `app/core/color_matrix_engine.py`, via
`app/utils/resource_path.py` (nunca con una ruta relativa a `__file__`, ver
Seccion 5 de esta guia). Ningun otro modulo debe abrir este archivo
directamente.

---

## `desktop-app/` — raiz

### `main.py`

**Proposito.** Punto de entrada del proceso. Prepara la ventana nativa, monta
`MainWindow`, arranca el icono de bandeja en un hilo daemon, aplica las
preferencias de arranque persistidas (registro de Windows, ventana
minimizada) y registra el evento de cierre de ventana para ocultarla en vez
de terminar el proceso.

**Funciones clave.**
- `initialize_page(page)` — corrutina; configura titulo, tema, dimensiones de
  ventana y `prevent_close = True`. Termina con `await page.window.center()`
  (ver Seccion 5: es una corrutina de Flet, no una llamada sincrona).
- `build_application(page)` — instancia `MainWindow`, conecta
  `on_keyboard_event`/`on_resize`, y registra `page.window.on_event` para
  interceptar el cierre (`WindowEventType.CLOSE`) y ocultar la ventana en vez
  de salir.
- `start_tray_service(page, main_window)` — crea el icono de bandeja, lo
  vincula a `main_window.set_tray_icon()` y arranca `tray_service.run_tray_loop`
  en un `threading.Thread` daemon independiente del hilo de Flet.
- `apply_startup_preference(launch_on_startup)` — escribe o borra la entrada
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` via `winreg` (stdlib,
  sin dependencia nueva).
- `run_application(page)` — corrutina objetivo pasada a `ft.run()`; orquesta
  las funciones anteriores y aplica `start_minimized` ocultando la ventana si
  corresponde.

**Conexiones.** Importa `app.ui.main_window.MainWindow`,
`app.tray.tray_service`, `app.tray.tray_menu_actions`,
`app.config.app_config.load_config`, `app.ui.theme.*`. Es el unico archivo
que llama `ft.run(...)`.

### `build.spec`

**Proposito.** Configuracion de PyInstaller para el ejecutable de un solo
archivo (`ChromaticVision.exe`, modo onefile: no hay paso `COLLECT`, todo se
empaqueta directamente en `EXE`). Declara los datos que deben viajar dentro
del ejecutable: `shared-color-science/color_matrix_reference.json`,
`app/picker/data/color_names.json`, y — critico, ver Seccion 5 —
`collect_data_files("flet")`, porque `flet` no trae su propio hook de
PyInstaller y sin esto la app no llega a arrancar.

**Conexiones.** No es codigo de la aplicacion; solo se ejecuta como entrada
de `pyinstaller build.spec`. Referencia `main.py` como script raiz y
`assets/icons/app.ico` como icono del ejecutable.

### `assets/icons/generate_icon.py`

**Proposito.** Genera `app.ico` (multi-resolucion: 16 a 256px) y `app.png` con
Pillow: un circulo del color de acento de la paleta clara (`#0071E3`) con una
"C" blanca centrada. Se ejecuta una sola vez, manualmente, antes de compilar
el `.exe` — nunca al arrancar la aplicacion.

**Conexiones.** Ninguna con el resto de la app en tiempo de ejecucion;
`build.spec` referencia su salida (`app.ico`) por ruta de archivo.

---

## `app/config/`

### `constants.py`

**Proposito.** Constantes fijas de identidad, geometria de ventana, rutas de
navegacion y los textos de UI que deben mantenerse en ASCII. No debe importar
logica de negocio ni componentes de UI — solo valores y el descriptor
`NavigationDestination` / la clase `AppRoute`.

**Funciones/clases clave.**
- `AppRoute` — strings de ruta (`dashboard`, `picker`, `filters`, `settings`).
- `NavigationDestination` — dataclass congelada: ruta, iconos, titulo,
  subtitulo de cada destino de navegacion.
- `NAVIGATION_DESTINATIONS` — tupla ordenada; el orden define tambien los
  atajos Ctrl+1..Ctrl+4.

**Conexiones.** Es una hoja del grafo de imports: la importan casi todos los
modulos de `app/ui/`, `main.py` y `main_window.py`; no importa nada del
propio proyecto.

### `app_config.py`

**Proposito.** Unica fuente de la ruta de configuracion local
(`%APPDATA%/ChromaticVision/config.json`, con respaldo `~/.config/...` en
otros sistemas) y de la escritura atomica (archivo temporal + `os.replace`).
El diccionario por defecto (`DEFAULT_CONFIG`) incluye `active_profile_id`
(Fase 1), `latitude`/`longitude` (Fase 4, para `filter_scheduler`), y
`start_minimized`/`launch_on_startup`/`startup_target` (Fase 5).

**Funciones clave.**
- `load_config()` — fusiona lo persistido sobre `DEFAULT_CONFIG`, nunca
  devuelve un diccionario incompleto.
- `save_config(data)` — sobrescribe el archivo completo; por eso todo
  llamador que solo quiere cambiar una clave debe hacer
  `load_config()` + `.update()` + `save_config()`, nunca guardar un
  subconjunto de claves directamente (ver Seccion 5, bug real de la Fase 5).
- `get_profiles_directory()` — subdirectorio usado por `profile_service.py`.
- `write_json_atomic(path, data)` — reutilizado por `profile_service.py`.

**Conexiones.** La consumen `main.py`, `main_window.py`, `filters_view.py`
(indirectamente via `filter_scheduler`), `settings_view.py` y
`filter_scheduler.py`. No importa nada de `app/ui/` ni `app/core/`.

---

## `app/core/`

### `color_matrix_engine.py`

**Proposito.** Motor puro de matrices de color: construye, interpola por
severidad y aplica matrices de correccion/simulacion CVD. Es
**agnostico del orden de canal** — `apply_color_matrix(frame, matrix)` no
sabe ni le importa si el frame esta en RGB o BGR, solo exige que frame y
matriz compartan el mismo orden. La responsabilidad de convertir desde el BGR
nativo de OpenCV es de quien lo llama (`overlay_renderer.py`).

**Funciones/clases clave.**
- `apply_color_matrix(frame, matrix)` — multiplicacion matricial vectorizada
  por pixel, con recorte 0-255.
- `interpolate_severity(identity, full_matrix, severity)` — interpolacion
  lineal identidad -> matriz completa.
- `build_matrix_for_profile(profile, mode)` — orquesta lo anterior; si
  `profile.deficiency_type == "normal"` devuelve la identidad directamente,
  sin tocar el JSON de referencia.
- `simulate_deficiency(frame, profile)` — atajo de alto nivel que combina
  `build_matrix_for_profile` + `apply_color_matrix` en modo `"simulate"`.
- `IDENTITY_MATRIX` — constante publica reutilizada por `filters_view.py`
  cuando el programador de ocaso arranca el overlay sin un perfil CVD activo.

**Conexiones.** Importa `app.profiles.profile_model.ColorVisionProfile` y
`app.utils.resource_path.resolve_shared_resource` (Fase 6; antes usaba
`Path(__file__).resolve().parents[3]`, que se rompia en el `.exe`
compilado — ver Seccion 5). Lo consumen `overlay_renderer.py`,
`main_window.py`, `tray_menu_actions.py` y `filters_view.py`.

### `screen_capture_service.py`

**Proposito.** Captura de pantalla via `mss` (no `cv2.VideoCapture`, elegido
por velocidad), con salida en BGR compatible con OpenCV. `capture_frame()`
alimenta el overlay de pantalla completa; `capture_region(x, y, w, h)`
alimenta la lupa del selector de color.

**Funciones clave.**
- `capture_frame()` / `capture_region(x, y, w, h)` — abren un `mss.MSS()`
  nuevo por llamada (simple y correcto; no es la instancia de mayor
  rendimiento posible para un bucle muy ajustado, pero evita compartir una
  instancia de mss entre hilos, que no es thread-safe).
- `encode_frame_as_png_base64(frame)` — codifica a PNG y luego base64,
  listo para `ft.Image(src=...)` (Fase 3; ver Seccion 5 sobre el campo `src`).

**Conexiones.** La usan `overlay_renderer.py`, `color_picker_service.py` y
`picker_view.py`. No importa nada de `app/ui/`.

### `overlay_renderer.py`

**Proposito.** Bucle de renderizado de la superposicion de correccion, en un
hilo dedicado (nunca el hilo de UI de Flet). Dos colas (`queue.Queue`,
thread-safe) sincronizan la matriz de correccion activa y el estado de
filtros (temperatura/brillo/contraste) sin bloquear a quien las publica.

**Pipeline por frame** (en este orden): captura BGR a resolucion completa ->
reduce a `RENDER_SCALE_FACTOR = 0.5` (Fase 6, ver Seccion 5) -> convierte a
RGB -> aplica la matriz de correccion CVD -> vuelve a BGR -> aplica
temperatura + brillo/contraste (capa independiente, apilada DESPUES de la
matriz CVD, nunca mezclada con ella) -> reescala de vuelta a la resolucion
original -> entrega al `frame_sink`.

**Funciones clave.**
- `start_render_loop(initial_matrix, frame_sink=None)` /
  `stop_render_loop()` — ciclo de vida del hilo.
- `update_active_matrix(matrix)` / `update_filter_state(state)` — publican en
  cada cola sin bloquear.
- `is_render_loop_running()` — usado por `filters_view.py` para decidir si
  el programador de ocaso necesita arrancar el hilo el mismo.
- `_apply_brightness_contrast(frame, brightness_ceiling, contrast)` — **no es
  una matriz diagonal**: es `np.clip` sobre una escala de brillo y una
  transformacion afine de contraste alrededor del punto medio (127.5),
  porque brillo y contraste no son operaciones lineales 3x3 puras (spec
  Seccion 4.2.4 implicito; confirmado explicitamente en la Fase 1).

**Conexiones.** Importa `color_matrix_engine.apply_color_matrix`,
`color_temperature.apply_temperature_shift`, `screen_capture_service.
capture_frame`. Lo controlan `main_window.py` (al activar/desactivar la
correccion manual), `filters_view.py` (sliders y programador) y
`tray_menu_actions.py` (menu rapido de la bandeja).

### `color_temperature.py`

**Proposito.** Filtro de temperatura de color (fotofobia), independiente de
la matriz de daltonismo. Aproximacion de cuerpo negro de Tanner Helland, sin
red ni tabla externa.

**Funciones clave.**
- `calculate_kelvin_curve(kelvin)` — devuelve ganancias `(r, g, b)` entre
  0.0 y 1.0.
- `apply_temperature_shift(frame, kelvin)` — espera frames en **BGR**, igual
  que `capture_frame`; aplica la ganancia multiplicando cada canal.

**Conexiones.** La usa `overlay_renderer.py` dentro de la capa de filtros. No
depende de ningun otro modulo del proyecto.

### `filter_scheduler.py`

**Proposito.** Calculo local de amanecer/atardecer (algoritmo solar de NOAA,
sin red) y bucle de programacion en hilo dedicado que activa/desactiva los
filtros de fotofobia automaticamente.

**Funciones clave.**
- `get_sunrise_sunset(lat, lon, date)` — implementa el algoritmo NOAA
  completo (dia juliano, longitud/anomalia media del sol, ecuacion del
  tiempo, angulo horario con el angulo cenital 90.833° que incluye
  refraccion atmosferica). La hora "local" se aproxima con el desfase UTC
  **actual del sistema operativo**, no con una base de datos de husos
  horarios por coordenada — limitacion documentada, no oculta (ver
  Seccion 5).
- `get_local_coordinates()` — lee `latitude`/`longitude` de la
  configuracion; si no hay ninguna, devuelve `(0.0, 0.0)` con una advertencia
  registrada via `app.utils.logger`.
- `start_schedule_loop(on_activate, on_deactivate)` /
  `stop_schedule_loop()` — revisa cada `SCHEDULE_CHECK_INTERVAL_SECONDS`
  (60s) si la hora actual cae despues del ocaso o antes del orto; usa
  `threading.Event.wait(60)` en vez de `time.sleep(60)` para que `stop_...`
  responda de inmediato en vez de esperar hasta el proximo minuto.

**Conexiones.** Importa `app.config.app_config.load_config` y
`app.utils.logger.get_logger`. Lo controla exclusivamente
`filters_view.py`, que le pasa dos callbacks que se ejecutan en el hilo del
programador y que por eso nunca tocan la UI directamente (agendan trabajo con
`page.run_task`, ver Seccion 4).

---

## `app/tray/`

### `tray_service.py`

**Proposito.** Ciclo de vida completo del icono de bandeja del sistema con
`pystray`: creacion del icono (circulo generado con Pillow, mismo color de
acento que el resto de la app), construccion del menu completo, y arranque
del bucle bloqueante de eventos.

**Funciones clave.**
- `create_tray_icon(on_open_window, on_exit)` — arma el menu en el orden
  fijo: nombre+version (deshabilitado) -> separador -> alternar correccion
  (con marca) -> submenu de cambio rapido de perfil (5 opciones, severidad
  fija 1.0 porque un menu de bandeja no tiene control deslizante) ->
  separador -> abrir ventana -> salir.
- `run_tray_loop(icon)` / `stop_tray_loop(icon)` — ciclo de vida; quien
  llama a `run_tray_loop` debe hacerlo desde un hilo dedicado (`main.py` lo
  hace via `threading.Thread(daemon=True)`).
- `update_tray_menu(icon, correction_active, active_profile_label)` —
  sincroniza el estado interno con la UI principal y fuerza el repintado.

**Conexiones.** Importa `app.core.overlay_renderer`,
`app.core.color_matrix_engine`, `app.tray.tray_menu_actions` y
`app.ui.theme.design_tokens.LIGHT_PALETTE` (para el color del icono). Lo
consumen `main.py` (arranque) y `main_window.py` (sincronizacion via
`set_tray_icon()` + `update_tray_menu()`).

### `tray_menu_actions.py`

**Proposito.** Un manejador por cada accion del menu de bandeja, separado de
la construccion del menu para poder recibir `renderer`/`engine` como
parametros inyectados (los modulos `overlay_renderer`/`color_matrix_engine`
en si, un patron liviano de inyeccion de dependencias) en vez de importarlos
de forma fija.

**Funciones clave.**
- `handle_toggle_correction(icon, correction_active, renderer)` — arranca o
  detiene el bucle con la ultima matriz recordada en `_current_matrix`
  (modulo-nivel; necesario porque `start_render_loop` exige una matriz y el
  clic de la bandeja no trae ninguna).
- `handle_switch_profile(icon, deficiency_type, severity, engine, renderer)`
  — construye un perfil temporal y publica su matriz.
- `handle_open_window(icon, page)` / `handle_exit(icon, page)` — ambos
  agendan corrutinas con `page.run_task(...)` porque se ejecutan en el hilo
  sincrono de pystray, ajeno al loop de eventos de Flet (ver Seccion 4).
  `handle_exit` llama `icon.stop()` directamente en vez de
  `tray_service.stop_tray_loop()`, para evitar un import circular entre
  ambos archivos.

**Conexiones.** Importa `app.core.overlay_renderer` (fijo, para
`handle_exit`) y recibe `color_matrix_engine`/`overlay_renderer` como
parametros en las otras funciones. Lo llama `tray_service.py` al construir
el menu, y `main.py` al construir los dos callbacks de abrir/salir.

---

## `app/picker/`

### `color_picker_service.py`

**Proposito.** Bucle de muestreo del selector de color en un hilo dedicado, a
hasta 60 FPS: captura la region bajo el cursor, resuelve el nombre del color,
y notifica a un callback. Independiente del hilo de `overlay_renderer.py`.

**Funciones clave.**
- `start_picker_loop(callback, region_size=120, fps=60)` /
  `stop_picker_loop()` — ciclo de vida.
- `sample_pixel(x, y)` — captura puntual de 1x1, usada por "congelar y
  copiar".
- `get_last_cursor_position()` — la ultima posicion observada por el bucle
  en vivo; existe especificamente para que el boton "Copiar HEX" muestree
  donde el usuario estaba mirando, no donde quedo el cursor tras moverse
  para hacer clic en el boton (ver Seccion 5).
- `_get_cursor_position()` — `ctypes.windll.user32.GetCursorPos` (stdlib
  puro de Windows, sin dependencia nueva).

**Conexiones.** Importa `app.core.screen_capture_service.capture_region` y
`app.picker.color_name_resolver`. Lo controla exclusivamente
`picker_view.py`.

### `color_name_resolver.py`

**Proposito.** Resolucion de nombre de color por vecino mas cercano en
espacio RGB (distancia euclidiana al cuadrado, sin raiz, porque solo se
compara orden relativo).

**Funciones clave.**
- `load_color_dataset(path)` — carga el JSON una vez.
- `resolve_color_name(hex_value, dataset)` — recorre linealmente el dataset
  (161 entradas, suficientemente pequeno para no requerir una estructura
  espacial mas compleja) y devuelve el nombre mas cercano.

**Conexiones.** La usa `color_picker_service.py`. No depende de nada mas del
proyecto.

### `data/color_names.json`

**Proposito.** 161 entradas HEX -> nombre unicas: las 148 palabras clave
extendidas de CSS/X11, con los alias de HEX identico colapsados (`gray`
gana sobre `grey`, `cyan` sobre `aqua`, etc. — un JSON no puede tener dos
claves iguales), mas 22 nombres curados adicionales para superar
holgadamente el minimo de 150 pedido.

**Conexiones.** Lo carga `color_name_resolver.load_color_dataset()`, via la
ruta que resuelve `app.utils.resource_path.resolve_shared_resource()`.

---

## `app/profiles/`

### `profile_model.py`

**Proposito.** `ColorVisionProfile`, dataclass congelada que es un espejo
**exacto** del esquema JSON compartido de la Seccion 6.1 del spec (mismos
cinco campos, mismo orden): `schema_version`, `deficiency_type`, `severity`,
`source`, `generated_at`. Deliberadamente no tiene campo `id` — la
interoperabilidad con la plataforma web exige que el JSON exportado
coincida byte a byte con ese esquema.

**Conexiones.** La importan practicamente todos los modulos de `app/core/`,
`app/profiles/`, `app/tray/` y varias vistas. No depende de nada del
proyecto.

### `profile_service.py`

**Proposito.** CRUD de perfiles persistidos como archivos JSON bajo
`app_config.get_profiles_directory()`. El `profile_id` es un nombre de
archivo elegido por quien llama, no un UUID generado — la app de escritorio
modela un unico perfil activo a la vez, guardado bajo el id fijo
`"active"` (constante `ACTIVE_PROFILE_ID` en `settings_view.py`), asi que
cada importacion sobrescribe el mismo archivo en vez de acumular perfiles
huerfanos.

**Funciones clave.** `create_profile`, `get_profile` (devuelve `None` si no
existe), `update_profile` (lanza `ValueError` si el perfil no existe),
`delete_profile` (idempotente).

**Conexiones.** Importa `app.config.app_config` y `app.profiles.
profile_model`. La usan `main_window.py` (carga al arrancar) y
`settings_view.py` (importar/exportar).

### `profile_importer.py`

**Proposito.** Importacion y validacion de perfiles JSON externos (por
ejemplo, generados por la plataforma web). La validacion nunca falla en
silencio: siempre lanza `ValueError` con un mensaje descriptivo.

**Funciones clave.**
- `import_profile_from_json(path)` — lee, valida, construye el dataclass.
- `validate_profile_schema(data)` — verifica los cinco campos obligatorios,
  que `deficiency_type` sea uno de los cinco valores soportados, que
  `severity` sea numerico entre 0.0 y 1.0, y que `source` sea uno de los
  tres valores soportados.

**Conexiones.** Importa `app.profiles.profile_model`. La usa
`settings_view.py` en el flujo de importacion.

---

## `app/ui/main_window.py`

**Proposito.** Shell raiz de la aplicacion: unico punto que conoce el mapa
completo de rutas, coordina cambios de tema, y actua de intermediario entre
las vistas y los servicios de fondo (`overlay_renderer`, `tray_service`,
`profile_service`). Ninguna vista tiene una referencia directa a
`MainWindow`; toda comunicacion vista -> shell pasa por un callback inyectado
explicitamente despues de construir la vista (mismo patron para
`set_tray_icon()` en `main.py` y `set_profile_changed_callback()` en
`SettingsView`).

**Funciones/metodos clave.**
- `navigate_to(route)` — cambia la vista visible; llama `deactivate()` en la
  vista anterior y `activate()` en la nueva (por eso `PickerView` solo
  consume CPU muestreando cuando esta realmente visible).
- `toggle_theme()` — reconstruye todo el shell con la paleta opuesta.
  **Antes de reconstruir**, captura `FiltersView.get_filter_state()` y
  `SettingsView.get_preferences()`; **despues**, los restaura con
  `set_filter_state()`/`set_preferences()` (Fase 6; antes de este arreglo,
  cambiar de tema reseteaba silenciosamente los sliders y switches — bug
  senalado en la revision de la Fase 0, cerrado en la Fase 6).
- `on_profile_changed(profile)` — punto unico de entrada cuando cambia el
  perfil activo (al importar uno nuevo, o al arrancar si hay uno guardado):
  refresca el panel, publica la nueva matriz en `overlay_renderer`, y
  sincroniza la bandeja.
- `_handle_correction_toggle(is_active)` — arranca/detiene
  `overlay_renderer` y publica el estado de filtros vigente por separado
  (la matriz CVD y la capa de temperatura/brillo/contraste viajan por
  colas independientes, nunca mezcladas en una sola matriz — ver Seccion 5).
- `_build_active_correction_matrix()` — solo la matriz CVD del perfil
  activo; ya NO mezcla la ganancia de temperatura (eso se elimino en la
  Fase 4 al existir la capa de filtros real).

**Conexiones.** Importa las cuatro vistas, `NavigationSidebar`, `AppHeader`,
`overlay_renderer`, `color_matrix_engine`, `profile_service`, `tray_service`,
`app_config`. Es importado unicamente por `main.py`.

---

## `app/ui/theme/`

### `design_tokens.py`

**Proposito.** Fuente unica de verdad de espaciado, radios, tipografia,
duraciones, curvas de animacion y color, derivados de
`UI_UX_DESIGN_GUIDELINES.md`. Ningun componente debe usar un valor de
padding/margin/gap fuera de la escala de `Spacing`, ni asignar un
`border_radius` interno a mano en vez de `derive_inner_radius()`.

**Clases/funciones clave.** `Spacing`, `Radius`, `FontWeight`, `FontSize`,
`Duration`, `Curve`, `Interaction` (escalas); `Palette` (dataclass
congelada); `LIGHT_PALETTE`/`DARK_PALETTE`; `get_palette(theme_mode)`;
`derive_inner_radius(outer, padding)` — aplica la formula obligatoria
`inner = outer - padding`, con piso de `Radius.MIN` (2px) si el resultado no
es positivo.

**Conexiones.** La importa practicamente todo `app/ui/`. No depende de nada
del proyecto.

### `theme_builder.py`

**Proposito.** Traduce los tokens de diseno a objetos nativos de Flet
(`ft.Theme`, `ft.TextStyle`). Ningun componente debe construir un `ft.Theme`
por su cuenta.

**Funciones clave.** `build_theme(palette)`, `build_display_style`,
`build_heading_style`, `build_body_style`, `build_caption_style`.

**Conexiones.** Importa `design_tokens`. La usan `main.py` y
`main_window.py`.

---

## `app/ui/components/`

Componentes reutilizables compartidos por varias vistas. Todos implementan
los seis estados obligatorios de la Seccion 4.1 de `UI_UX_DESIGN_GUIDELINES.md`
donde aplica (Default, Hover, Active, Focused, Disabled, Loading).

### `navigation_item.py`
**Proposito.** Item individual de la barra lateral: indicador de seleccion
por forma (barra vertical), no solo por color, para usuarios con CVD.
**Conexiones.** Lo usa `navigation_bar.py`.

### `navigation_bar.py`
**Proposito.** Panel lateral persistente; unico punto de cambio de ruta,
navegacion por teclado (flechas + Enter) y modo compacto.
**Conexiones.** Instancia `NavigationItem` por cada `NavigationDestination`;
la controla `main_window.py`.

### `surface_card.py`
**Proposito.** Tarjeta base reutilizable; expone `inner_radius` derivado
para que los hijos redondeados no se desalineen visualmente del contenedor.
El estado hover compara `bool(event.data)` (booleano real en Flet 0.86.x),
no `event.data == "true"` como en versiones antiguas de Flet — ver
Seccion 5, este fue el primer bug de API real que aparecio en el proyecto.
**Conexiones.** La usan todas las vistas para sus tarjetas de contenido.

### `app_header.py`
**Proposito.** Barra fija superior: contexto de la vista activa a la
izquierda, controles globales (correccion, tema) a la derecha. El estado de
correccion se comunica con icono + texto + borde, nunca solo con color
(regla critica CVD de la Seccion 2.3 de la guia de diseno).
**Conexiones.** La controla `main_window.py`.

---

## `app/ui/views/`

### `base_view.py`
**Proposito.** Contrato comun de las cuatro vistas enrutadas: contenedor
desplazable, y el ciclo de vida `activate()`/`deactivate()` que los servicios
con hilo (picker, en particular) usan para arrancar y detener trabajo solo
mientras la vista esta realmente visible.
**Conexiones.** La heredan las cuatro vistas.

### `dashboard_view.py`
**Proposito.** Resumen del perfil activo (tipo, severidad) y del estado de
filtros. Puramente de lectura: `update_summary()` la actualiza,
`main_window.py` decide cuando.
**Conexiones.** Ninguna hacia otros modulos de negocio; solo recibe datos ya
calculados.

### `picker_view.py`
**Proposito.** Superficie de lupa y lectura de la muestra actual, con el
bucle en vivo de `color_picker_service`. El callback del picker llega desde
su hilo dedicado y **nunca toca la UI directamente**: agenda
`_apply_picker_sample` con `page.run_task(...)` (ver Seccion 4). El boton
"Copiar HEX" usa `get_last_cursor_position()` en vez de la posicion actual
del cursor, y `page.clipboard.set()` (no `page.set_clipboard()`, que no
existe en Flet 0.86.5).
**Conexiones.** Importa `app.picker.color_picker_service` y
`app.core.screen_capture_service.encode_frame_as_png_base64`.

### `filters_view.py`
**Proposito.** Temperatura, techo de brillo y contraste, mas el interruptor
de programacion automatica. Cada slider publica su estado en
`overlay_renderer.update_filter_state()` al cambiar. El interruptor de
programacion arranca/detiene `filter_scheduler`; sus callbacks tambien
llegan desde un hilo ajeno a Flet y se agendan con `page.run_task(...)`.
**Conexiones.** Importa `app.core.overlay_renderer`,
`app.core.filter_scheduler`, `app.core.color_matrix_engine.IDENTITY_MATRIX`.

### `settings_view.py`
**Proposito.** Preferencias de arranque (persistidas en cada cambio, lectura-
fusion-escritura para no perder otras claves de `config.json`) e
importacion/exportacion del perfil de vision via `ft.FilePicker`
(`pick_files()`/`save_file()`, ambos corrutinas que devuelven directamente
el resultado, sin el patron `on_result` de versiones antiguas de Flet).
Notifica cambios de perfil a `MainWindow` via un callback inyectado
(`set_profile_changed_callback`), nunca con una referencia directa.
**Conexiones.** Importa `app.profiles.profile_importer`,
`app.profiles.profile_service`, `app.config.app_config`.

---

## `app/utils/`

### `control_sync.py`
**Proposito.** `request_update(control)` — solicita el repintado de un
control solo si ya esta montado en la pagina (Flet lanza `RuntimeError` al
consultar `.page` en un control aun no montado; esta funcion lo captura).
Debe usarse siempre en vez de `if self.page is not None: self.update()`.
**Conexiones.** La usa practicamente todo `app/ui/`.

### `logger.py`
**Proposito.** Configuracion centralizada de logging (`logging.basicConfig`
aplicado una sola vez por proceso). Previsto desde el spec original
(Seccion 4.3) pero sin uso real hasta que `filter_scheduler.py` lo necesito
en la Fase 4 para registrar la advertencia de coordenadas ausentes.
**Conexiones.** La usa `filter_scheduler.py`.

### `resource_path.py`
**Proposito.** Resuelve rutas a datos empaquetados, funcionando igual desde
codigo fuente y desde el ejecutable de PyInstaller. Necesario porque
`Path(__file__).resolve().parents[N]` deja de funcionar una vez congelado
(ver Seccion 5) — PyInstaller mantiene la mayoria de los modulos Python
puros dentro del archivo PYZ comprimido en vez de extraerlos como archivos
sueltos.
**Funciones clave.** `is_frozen()`, `resolve_shared_resource(relative_path)`
— usa `sys._MEIPASS` como raiz si el proceso esta congelado, o sube tres
niveles desde este archivo (la raiz del monorepo) si corre desde fuente.
**Conexiones.** La usan `color_matrix_engine.py` y `color_picker_service.py`.

---

## 2. Orden de lectura sugerido

Para un recien llegado, en este orden:

```
1.  main.py
2.  app/config/constants.py
3.  app/ui/theme/design_tokens.py
4.  app/ui/theme/theme_builder.py
5.  app/core/color_matrix_engine.py
6.  app/core/screen_capture_service.py
7.  app/core/overlay_renderer.py
8.  app/core/color_temperature.py
9.  app/core/filter_scheduler.py
10. app/profiles/profile_model.py
11. app/profiles/profile_service.py
12. app/profiles/profile_importer.py
13. app/tray/tray_service.py
14. app/tray/tray_menu_actions.py
15. app/picker/color_picker_service.py
16. app/picker/color_name_resolver.py
17. app/ui/main_window.py
18. app/ui/views/base_view.py
19. app/ui/views/dashboard_view.py
20. app/ui/views/picker_view.py
21. app/ui/views/filters_view.py
22. app/ui/views/settings_view.py
23. app/utils/control_sync.py
24. app/utils/logger.py
25. app/utils/resource_path.py
26. app/config/app_config.py
```

Motivo del orden: primero el punto de entrada y las constantes (para saber
que existe), despues el sistema de diseno (para leer la UI con contexto),
despues el motor de color puro (la logica de negocio central, sin hilos ni
Flet de por medio), despues los servicios con hilo en el orden en que un
usuario los usaria (overlay -> filtros -> perfiles -> bandeja -> selector),
y al final el shell de UI que los conecta a todos, seguido de las utilidades
transversales que son mas faciles de entender una vez que ya se vio quien las
usa.

---

## 3. Glosario

**Deuteranopia / Deuteranomalia** — Ausencia (deuteranopia) o sensibilidad
reducida (deuteranomalia) de los conos de longitud de onda media (verde) del
ojo. Es el tipo mas comun de daltonismo; produce confusion principalmente
entre rojos y verdes.

**Tritanopia / Tritanomalia** — Ausencia o sensibilidad reducida de los
conos de longitud de onda corta (azul). Produce confusion entre azules y
amarillos; mucho menos comun que la deficiencia rojo-verde.

**Daltonizacion** — Tecnica que redistribuye hacia los canales de color que
una persona con daltonismo si percibe, la informacion de color que pierde en
su eje deficiente. No es lo mismo que "simular" el daltonismo (que muestra
como ve una persona daltonica); daltonizar es *corregir* la imagen para que
esa persona distinga mejor lo que de otra forma se confundiria.

**Espacio de color LMS** — Modelo de color basado en la respuesta de los
tres tipos de cono del ojo humano (Long, Medium, Short — largo, medio,
corto). Es el espacio natural para modelar matematicamente el daltonismo,
porque cada tipo de deficiencia corresponde a la perdida o reduccion de uno
de esos tres canales.

**Lineas de confusion** — En un diagrama de cromaticidad, los pares de
colores que una persona con un tipo especifico de daltonismo no puede
distinguir caen sobre la misma "linea de confusion". Se usan para disenar
pruebas de deteccion (como las laminas de Ishihara) y para construir las
matrices de simulacion/correccion.

**Matriz de correccion** — Matriz 3x3 que transforma cada pixel `(R, G, B)`
de una imagen en un nuevo `(R', G', B')`. En este proyecto hay dos tipos:
las de "simulacion" (como ve la escena una persona con esa deficiencia) y
las de "correccion" o daltonizacion (redistribuyen la informacion perdida).

**Severidad (escala 0.0-1.0)** — Que tan completa es la deficiencia. `0.0`
es vision normal (matriz identidad); `1.0` es dicromacia completa (matriz de
deficiencia al 100%). Los valores intermedios se obtienen por interpolacion
lineal entre ambas matrices, no por un tercer juego de coeficientes.

**Superposicion (overlay)** — La capa de correccion de color que se aplica
en tiempo real sobre toda la pantalla capturada, antes de mostrarla al
usuario. Es lo que produce `overlay_renderer.py`.

**Fotofobia** — Sensibilidad excesiva a la luz, no relacionada con el
daltonismo. Este proyecto la atiende con los filtros de temperatura de
color, techo de brillo y contraste de `filters_view.py`, independientes de
la correccion CVD.

**Temperatura de color (Kelvin)** — Escala que describe el tono de una
fuente de luz: valores bajos (~2000K) son calidos (rojizos/anaranjados),
valores altos (~6500K) son neutros/frios (azulados). Reducir la temperatura
de la pantalla desplaza los colores hacia tonos calidos, disminuyendo la luz
azul percibida.

---

## 4. Diagrama de hilos

```
Hilo principal (loop de eventos de Flet)
    |
    |-- Todos los controles de UI, navegacion, animaciones
    |-- Los `on_click`/`on_change` de Flet corren aqui de forma nativa
    |-- page.run_task(corrutina, *args) es el UNICO puente confirmado
    |   thread-safe para que un hilo ajeno agende trabajo que toque la UI
    |
    +-- Hilo de render (overlay_renderer._run_render_loop)
    |       Arranca/detiene: MainWindow._handle_correction_toggle,
    |       FiltersView (sliders y programador de ocaso)
    |       Recibe matriz y estado de filtros via dos queue.Queue
    |       Entrega frames corregidos via un frame_sink (callback)
    |
    +-- Hilo del selector de color (color_picker_service._run_picker_loop)
    |       Activo SOLO mientras PickerView esta visible
    |       (arranca en PickerView.activate, detiene en .deactivate)
    |       Su callback jamas toca la UI: agenda con page.run_task
    |
    +-- Hilo de bandeja (pystray, daemon, arrancado por main.py)
    |       Bucle de eventos nativo de pystray (tray_service.run_tray_loop)
    |       Sus clics de menu tambien agendan con page.run_task cuando
    |       necesitan tocar la ventana (abrir/salir); las acciones que solo
    |       llaman a overlay_renderer/color_matrix_engine no lo necesitan,
    |       porque esos modulos ya son thread-safe por diseno (colas)
    |
    +-- Hilo del programador de ocaso (filter_scheduler._run_schedule_loop)
            Opcional: solo existe mientras el interruptor de "Activar
            despues del ocaso" esta encendido en FiltersView
            Revisa cada 60s (threading.Event.wait, no time.sleep, para
            responder de inmediato a stop_schedule_loop)
            Sus callbacks on_activate/on_deactivate tambien agendan con
            page.run_task
```

**Regla que se repite en los cuatro hilos de fondo:** ninguno modifica un
control de Flet directamente. Todos publican datos via una cola
(`overlay_renderer`, `filter_scheduler` que llama callbacks) o agendan una
corrutina con `page.run_task(...)` (picker, bandeja, programador). Esto no
es una preferencia de estilo: se confirmo por lectura del codigo fuente de
Flet que `Control.update()` termina en `asyncio.Queue.put_nowait()`, que no
es seguro de llamar desde un hilo distinto al que corre el loop de eventos.

---

## 5. Decisiones que se apartaron del spec original

Esta seccion existe porque el spec (`ProjectDaltonism.md`) describe la
arquitectura *deseada*, escrita antes de tocar la API real de Flet 0.86.x,
pystray o PyInstaller. El CHANGELOG (`info-md/CHANGELOG.md`) es el registro
fase por fase de cada divergencia real, verificada por ejecucion, no
asumida. Este es un resumen orientado a lectura; para el detalle completo,
incluidas las mediciones y el razonamiento, ir a la entrada de la fase
correspondiente en el CHANGELOG.

- **APIs de Flet que no eran las esperadas** (varias fases; varios de estos
  se encontraron ejecutando pruebas propias, no por el smoke test dado en
  cada prompt de fase): `event.data` en `on_hover` es un `bool` real, no el
  string `"true"` de versiones antiguas de Flet (Fase 0); `ft.Image` usa un
  solo campo `src` que acepta string/base64/bytes, no `src_base64` (Fase 1);
  `ft.BoxFit`, no `ft.ImageFit` (Fase 1); `page.window.on_close` no existe,
  es `page.window.on_event` con `WindowEventType.CLOSE` (Fase 2);
  `page.clipboard.set()`, no `page.set_clipboard()` (Fase 3); `ft.Dropdown`
  usa `on_select`, no `on_change` (Fase 5); `page.window.center()` es una
  corrutina que nunca se esperaba con `await` desde la Fase 0, y solo se
  detecto al ejecutar el `.exe` compilado en la Fase 6.
- **El patron `page.run_task(...)`** aparece en cuatro lugares distintos
  (bandeja, selector de color, programador de ocaso, importar/exportar
  perfil) porque es el unico puente confirmado thread-safe entre un hilo de
  fondo y el loop de eventos de Flet. No esta en el spec porque el spec no
  anticipaba que tantos servicios necesitarian su propio hilo.
  Ver Seccion 4.
- **Brillo y contraste nunca fueron una matriz 3x3.** El spec (Seccion
  13.2) describe la correccion CVD como transformaciones matriciales; brillo
  y contraste no encajan en ese modelo (no son lineales alrededor del
  origen). Se implementaron desde la Fase 1 como una nota explicita de
  "pendiente", y se construyeron en la Fase 4 como `np.clip` + escalar,
  nunca como matriz diagonal — ver `overlay_renderer._apply_brightness_
  contrast`.
- **Rendimiento del overlay: no alcanza los 30 FPS de la Seccion 4.4,**
  incluso despues de compilar con PyInstaller. Se perfilo cada etapa del
  pipeline antes de optimizar (Fase 6): la captura de pantalla en si
  (`mss`, ~35-58ms/frame a 1920x1080) ya es, sola, casi el techo del
  presupuesto de un frame a 30 FPS, y no se puede reescalar durante la
  captura. Reducir la resolucion de procesamiento (960x540) llevo el FPS
  medido de 2.0 a 8.0 — una mejora real de 4x, documentada con honestidad
  como insuficiente para el objetivo original, no maquillada como exito.
- **Empaquetar con PyInstaller no acelera el codigo.** Contrario a lo que
  asumia el brief de la Fase 6, PyInstaller empaqueta el interprete CPython
  estandar; no compila Python a codigo nativo. numpy/OpenCV ya eran
  extensiones C compiladas de antemano en cualquier caso.
- **Rutas de archivo relativas a `__file__` se rompen congeladas.** Dos
  modulos (`color_matrix_engine.py`, `color_picker_service.py`) tuvieron que
  migrar de `Path(__file__).resolve().parents[N]` a
  `app.utils.resource_path.resolve_shared_resource()` en la Fase 6, porque
  PyInstaller no extrae los modulos Python puros como archivos sueltos.
- **`flet` no tiene hook propio de PyInstaller.** `build.spec` necesita
  `collect_data_files("flet")` explicitamente, o el `.exe` compila sin
  error pero falla al abrir (`FileNotFoundError: ...icons.json`).
