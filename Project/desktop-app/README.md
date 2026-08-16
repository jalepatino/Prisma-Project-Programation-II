# ChromaticVision Desktop

Herramienta de accesibilidad visual para deficiencias de vision al color
(deuteranopia, deuteranomalia, tritanopia, tritanomalia) y fotofobia. Corrige
los colores de toda la pantalla en tiempo real, incluye una lupa selectora de
color y filtros de temperatura/brillo/contraste con programacion automatica al
anochecer.

## Requisitos del sistema

- Windows 10 o superior (la integracion de bandeja del sistema y el arranque
  automatico usan APIs especificas de Windows).
- Para ejecutar el `.exe`: ningun requisito adicional, es un ejecutable
  autocontenido.
- Para ejecutar desde codigo fuente: Python 3.11 o superior.

## Instalacion del ejecutable

1. Descarga `ChromaticVision.exe` desde la carpeta `dist/` generada por el
   build (ver seccion siguiente si vas a compilarlo vos mismo).
2. Ejecuta el `.exe`. No requiere instalador ni permisos de administrador.
3. La aplicacion se minimiza a la bandeja del sistema en vez de cerrarse; usa
   la opcion "Salir" del menu de la bandeja para terminar el proceso por
   completo.

## Ejecucion desde codigo fuente

```bash
cd desktop-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Generar el ejecutable

```bash
cd desktop-app
pip install pyinstaller
python assets/icons/generate_icon.py
pyinstaller build.spec --clean
```

El `.exe` resultante queda en `desktop-app/dist/ChromaticVision.exe`.

## Las cuatro vistas principales

| Vista | Atajo | Descripcion |
|---|---|---|
| Panel | Ctrl+1 | Resumen del perfil de vision activo, severidad y filtros aplicados |
| Selector de color | Ctrl+2 | Lupa de pantalla en vivo con lectura HEX, RGB y nombre de color bajo el cursor |
| Filtros | Ctrl+3 | Temperatura de color, techo de brillo y contraste, con programacion automatica al ocaso |
| Ajustes | Ctrl+4 | Comportamiento de arranque, importar/exportar el perfil de vision |

## Atajos de teclado

| Atajo | Accion |
|---|---|
| Ctrl+1 / Ctrl+2 / Ctrl+3 / Ctrl+4 | Navega directamente a cada vista |
| Ctrl+B | Contrae o expande la barra lateral |
| Ctrl+D | Alterna entre tema claro y oscuro |
| Flecha arriba / abajo | Mueve el foco de teclado entre destinos de la barra lateral |
| Enter | Activa el destino con foco de teclado |
| Escape | Retira el foco de teclado de la barra lateral |
