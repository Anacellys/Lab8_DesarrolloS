"""
alertas/conexion.py
# LABORATORIO: archivo nuevo completo.

Detecta la perdida y la recuperacion de la conexion de red.

red.py mide el trafico en KB/s, pero un trafico en cero no significa que
no haya conexion: puede que simplemente no se este usando. Por eso este
modulo mira otra cosa: si existe alguna interfaz de red ACTIVA con una
direccion IPv4 real (ni loopback ni autoasignada).

Limitacion honesta: esto detecta "tengo una interfaz activa con IP", no
"llego a internet". Si el Wi-Fi esta conectado pero el router no tiene
salida, el nodo lo vera como conectado.

Eventos que genera (los consume el despachador de eventos):
    red_desconectada        flanco: conectada -> desconectada (una vez)
    red_conectada           flanco: desconectada -> conectada (una vez)
    red_sigue_desconectada  tiempo: cada PERIODO_RECORDATORIO_RED mientras
                            la red siga caida
"""
import socket
import time

import psutil

import config

# LABORATORIO - Estado anterior: sin el no hay deteccion de flancos.
_estado = {
    "conectada": None,            # None = todavia no se ha leido
    "desde": None,                # marca de tiempo de la caida
    "ultimo_recordatorio": None,  # marca de tiempo del ultimo recordatorio
    "ultima_revision": None,      # marca de tiempo de la ultima lectura
}


# LABORATORIO
def reiniciar():
    """Borra el estado, para que la siguiente lectura sea la 'primera'."""
    for clave in _estado:
        _estado[clave] = None


# LABORATORIO
def esta_conectada():
    """True si hay una interfaz activa con IPv4 real; False si no.
    Devuelve None si el sistema no permite averiguarlo."""
    try:
        interfaces = psutil.net_if_stats()
        direcciones = psutil.net_if_addrs()
    except Exception:
        return None
    for nombre, datos in interfaces.items():
        if not datos.isup or nombre.startswith(config.INTERFACES_IGNORADAS):
            continue
        for d in direcciones.get(nombre, []):
            if (d.family == socket.AF_INET
                    and not d.address.startswith(config.PREFIJOS_IP_IGNORADOS)):
                return True
    return False


# LABORATORIO
def detectar(ahora):
    """Devuelve la lista de eventos de conexion ocurridos en este instante.

    No espera nada: compara la hora recibida contra las marcas de tiempo
    guardadas y regresa de inmediato.
    """
    ultima = _estado["ultima_revision"]
    if ultima is not None and ahora - ultima < config.PERIODO_CONEXION:
        return []                         # todavia no toca revisar
    _estado["ultima_revision"] = ahora

    conectada = esta_conectada()
    if conectada is None:
        return []                         # no se pudo leer: no se inventa nada

    previa = _estado["conectada"]
    _estado["conectada"] = conectada

    if previa is None:                    # primera lectura: no hay flanco
        if not conectada:
            _estado["desde"] = ahora
            _estado["ultimo_recordatorio"] = ahora
        return []

    if previa and not conectada:          # flanco de bajada
        _estado["desde"] = ahora
        _estado["ultimo_recordatorio"] = ahora
        return [("red_desconectada", {"hora": time.strftime("%H:%M:%S")})]

    if not previa and conectada:          # flanco de subida
        segundos = round(ahora - _estado["desde"])
        _estado["desde"] = None
        _estado["ultimo_recordatorio"] = None
        return [("red_conectada", {"segundos_sin_red": segundos})]

    if not conectada:                     # sigue caida: recordatorio por tiempo
        if ahora - _estado["ultimo_recordatorio"] >= config.PERIODO_RECORDATORIO_RED:
            _estado["ultimo_recordatorio"] = ahora
            return [("red_sigue_desconectada",
                     {"segundos": round(ahora - _estado["desde"])})]
    return []
