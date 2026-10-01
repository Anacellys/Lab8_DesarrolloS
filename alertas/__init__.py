"""
Paquete alertas
---------------
# LABORATORIO: paquete nuevo completo.

Alertas sonoras del nodo de telemetria. Responsabilidades, una por archivo:

    conexion.py     decide SI se perdio o se recupero la conexion de red
    reproductor.py  decide CUANDO suena cada alerta (cola + marcas de tiempo)
    sonidos.py      hace sonar un tono, sin esperar a que termine

El resto del programa solo necesita conocer las funciones de abajo.
"""
from .conexion import detectar as revisar_conexion
from .reproductor import (iniciar as _iniciar_reproductor, encolar,
                          actualizar as reproducir, silenciar,
                          alternar_silencio, esta_silenciado, estado)
from . import conexion


def iniciar():
    """Prepara todo el paquete. Se llama una vez desde nucleo.iniciar()."""
    conexion.reiniciar()
    _iniciar_reproductor()
