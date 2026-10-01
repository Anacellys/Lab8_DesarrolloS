"""
alertas/sonidos.py
# LABORATORIO: archivo nuevo completo.

Unica parte del programa que "toca" el hardware de sonido.

Windows:  winsound.PlaySound(archivo, SND_ASYNC) devuelve de inmediato y
          el sonido sigue en segundo plano. Por eso los tonos se generan
          antes como archivos .wav pequenos (en la carpeta temporal).
          NO se usa winsound.Beep(): esa funcion se queda esperando hasta
          que el tono termina y congelaria el dashboard.
macOS / Linux: se usa la campana del sistema (caracter BEL), que tampoco
          bloquea.
"""
import math
import os
import struct
import sys
import tempfile
import wave

import config

try:
    import winsound            # solo existe en Windows
except ImportError:
    winsound = None

# LABORATORIO - (frecuencia, duracion) -> ruta del .wav ya generado
_rutas = {}


# LABORATORIO
def _carpeta():
    return os.path.join(tempfile.gettempdir(), config.CARPETA_SONIDOS)


# LABORATORIO
def _generar(ruta, hz, ms):
    """Escribe un archivo .wav con un tono senoidal de `hz` durante `ms`."""
    muestras = int(config.MUESTREO_HZ * ms / config.MS_POR_SEGUNDO)
    fade = int(config.MUESTREO_HZ * config.FADE_MS / config.MS_POR_SEGUNDO)
    datos = bytearray()
    for i in range(muestras):
        # La envolvente sube y baja suavemente en los extremos del tono.
        envolvente = min(i, muestras - i, fade) / fade
        onda = math.sin(math.tau * hz * i / config.MUESTREO_HZ)
        valor = int(config.AMPLITUD_MAX * config.VOLUMEN * envolvente * onda)
        datos += struct.pack("<h", valor)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(config.CANALES)
        w.setsampwidth(config.BYTES_MUESTRA)
        w.setframerate(config.MUESTREO_HZ)
        w.writeframes(bytes(datos))


# LABORATORIO
def preparar(secuencias):
    """Genera, una sola vez al arrancar, los .wav de todos los tonos."""
    if winsound is None:
        return
    os.makedirs(_carpeta(), exist_ok=True)
    for secuencia in secuencias.values():
        for hz, ms in secuencia:
            if hz != config.SILENCIO_HZ and (hz, ms) not in _rutas:
                ruta = os.path.join(
                    _carpeta(), f"{hz}_{ms}{config.EXTENSION_SONIDO}")
                _generar(ruta, hz, ms)
                _rutas[(hz, ms)] = ruta


# LABORATORIO
def tono(hz, ms):
    """Empieza a sonar un tono y REGRESA DE INMEDIATO (no espera)."""
    if winsound is None:
        sys.stdout.write("\a")
        sys.stdout.flush()
        return
    ruta = _rutas.get((hz, ms))
    if ruta is None:
        return
    winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC)
