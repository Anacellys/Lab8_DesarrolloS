"""
alertas/reproductor.py
# LABORATORIO: archivo nuevo completo.

Reproductor de alertas sonoras que NO bloquea el ciclo de monitoreo.

Piezas:
  _cola     deque con las alertas que esperan turno: (nombre, marca_de_tiempo)
  _pasos    deque con los tonos pendientes de la alerta que esta sonando
  _fin_paso marca de tiempo en la que termina el tono actual

Cada vez que nucleo.ciclo() llama a actualizar(ahora) pasa UNA de estas tres
cosas, y en los tres casos la funcion regresa enseguida:
  1. El tono actual todavia no termina       -> no hace nada.
  2. Ya termino y quedan tonos en la alerta  -> empieza el siguiente tono.
  3. La alerta termino                       -> toma la siguiente de la cola
                                                (descartando las caducadas).
Nunca hay una espera: solo se compara la hora actual con una marca guardada.
"""
import time
from collections import deque

import almacenamiento as registro
import config
from . import sonidos

# LABORATORIO
_cola = deque(maxlen=config.COLA_MAX_ALERTAS)
_pasos = deque()
_fin_paso = None
_silencio = config.MODO_SILENCIOSO


# LABORATORIO
def iniciar():
    """Prepara el reproductor: vacia la cola y genera los sonidos."""
    global _fin_paso, _silencio
    _cola.clear()
    _pasos.clear()
    _fin_paso = None
    _silencio = config.MODO_SILENCIOSO
    sonidos.preparar(config.SECUENCIAS)


# LABORATORIO
def silenciar(valor):
    """Activa o desactiva el modo silencioso y lo anota en la bitacora."""
    global _silencio
    _silencio = bool(valor)
    registro.registrar_evento(
        "INFO", "alertas",
        "Modo silencioso activado" if _silencio
        else "Modo silencioso desactivado")
    return _silencio


# LABORATORIO
def alternar_silencio():
    return silenciar(not _silencio)


# LABORATORIO
def esta_silenciado():
    return _silencio


# LABORATORIO
def encolar(evento, ahora=None):
    """Agrega a la cola la alerta que corresponde a un evento.

    Solo anota la alerta y la hora; no suena nada aqui. Devuelve True si el
    evento tiene alerta sonora y False si no (por ejemplo disco_lleno).
    """
    nombre = config.ALERTAS_POR_EVENTO.get(evento)
    if nombre is None:
        return False
    marca = time.time() if ahora is None else ahora
    _cola.append((nombre, marca))
    return True


# LABORATORIO
def _iniciar_paso(ahora):
    """Empieza el siguiente tono de la alerta en curso."""
    global _fin_paso
    hz, ms = _pasos.popleft()
    _fin_paso = ahora + ms / config.MS_POR_SEGUNDO
    if hz != config.SILENCIO_HZ and not _silencio:
        sonidos.tono(hz, ms)


# LABORATORIO
def actualizar(ahora):
    """Avanza el reproductor. NUNCA espera: regresa siempre de inmediato."""
    global _fin_paso
    if _fin_paso is not None and ahora < _fin_paso:
        return                                  # caso 1: aun suena
    if _pasos:
        _iniciar_paso(ahora)                    # caso 2: siguiente tono
        return
    _fin_paso = None                            # caso 3: buscar otra alerta
    while _cola:
        nombre, marca = _cola.popleft()
        if ahora - marca > config.ALERTA_CADUCA_S:
            continue                            # espero demasiado: ya no sirve
        _pasos.extend(config.SECUENCIAS[nombre])
        _pasos.append((config.SILENCIO_HZ, config.PAUSA_ENTRE_ALERTAS_MS))
        if _silencio:
            registro.registrar_evento(
                "INFO", "alertas", f"[silencio] sonaria la alerta: {nombre}")
        _iniciar_paso(ahora)
        return


# LABORATORIO
def estado():
    """Resumen para pruebas y pantalla: si suena algo y cuantas esperan."""
    return {"sonando": bool(_pasos) or _fin_paso is not None,
            "en_cola": len(_cola)}
