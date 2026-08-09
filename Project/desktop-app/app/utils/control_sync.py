# Utilidad de sincronizacion de controles con la pagina
# Flet lanza RuntimeError al consultar page en un control aun no montado

import flet as ft


# Indica si el control ya forma parte del arbol montado en la pagina
def is_mounted(control: ft.BaseControl) -> bool:
    try:
        return control.page is not None
    except RuntimeError:
        return False


# Solicita el repintado del control solo cuando ya esta montado
def request_update(control: ft.BaseControl) -> None:
    if is_mounted(control):
        control.update()
