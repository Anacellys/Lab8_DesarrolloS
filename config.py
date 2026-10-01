"""
config.py
Parametros de configuracion del nodo de telemetria.
Todo lo que puede cambiar entre una instalacion y otra vive aqui.
Ningun otro archivo del proyecto debe contener un numero literal.
Unidad 2 - Programacion en Python para sistemas IoT
Facultad de Ingenieria de Sistemas Computacionales - UTP
"""
import os

# --------------------------------------------------------------------------
# Identificacion del nodo
# --------------------------------------------------------------------------
NODO = "nodo-boniche"
UBICACION = "Laboratorio 3 - FISC"
ESTUDIANTE = "Anacelis Boniche"
GRUPO = "IGS134"

# --------------------------------------------------------------------------
# Periodos de muestreo, en segundos.
# Cada metrica tiene el suyo: leer los procesos es caro, leer la CPU no.
# --------------------------------------------------------------------------
PERIODO_RAPIDO = 1.0      # cpu, memoria, red
PERIODO_LENTO = 5.0       # disco, procesos, bateria
PERIODO_REPORTE = 30.0    # resumen periodico hacia la bitacora
REFRESCO_MS = 200         # cada cuanto refresca el dashboard (milisegundos)

# --------------------------------------------------------------------------
# Umbrales. Dos valores por metrica: uno para entrar en alarma y otro,
# mas bajo, para salir de ella. Esa diferencia es la HISTERESIS y evita
# que una lectura oscilando en el limite genere decenas de eventos falsos.
# --------------------------------------------------------------------------
CPU_ALTO = 70.0
CPU_BAJO = 50.0
CPU_NUCLEO_SATURADO = 90.0   # un nucleo individual por encima de esto

RAM_ALTA = 85.0
RAM_BAJA = 75.0

DISCO_LLENO = 90.0           # porcentaje de ocupacion
DISCO_ALIVIADO = 85.0

RED_PICO_KBS = 500.0         # kilobytes por segundo
RED_CALMA_KBS = 200.0

BATERIA_BAJA = 20.0
BATERIA_RECUPERADA = 30.0

PROCESO_PESADO = 50.0        # % de CPU de un solo proceso

# Variacion brusca entre dos muestras consecutivas: evento de anomalia.
SALTO_ANOMALO = 40.0

# --------------------------------------------------------------------------
# Ventana movil y almacenamiento
# --------------------------------------------------------------------------
VENTANA = 10                 # muestras que se promedian para evaluar el umbral
MAX_EVENTOS_LOG = 200        # eventos que se conservan en pantalla
ARCHIVO_BITACORA = "bitacora.json"

# --------------------------------------------------------------------------
# Unidad de disco a vigilar. Se detecta sola segun el sistema operativo.
# --------------------------------------------------------------------------
UNIDAD_DISCO = "C:\\" if os.name == "nt" else "/"

# Cantidad de procesos que se muestran en el ranking.
TOP_PROCESOS = 8

# Procesos del sistema que no vale la pena reportar: en Linux los
# 'kworker' y 'kthread' aparecen y desaparecen constantemente y llenarian
# la bitacora de ruido.
PROCESOS_IGNORADOS = ("kworker", "kthread", "ksoftirqd", "migration",
                      "rcu_", "irq/", "svchost")


# ==========================================================================
# LABORATORIO N.1 - Alertas sonoras para el nodo de telemetria
# Todo lo agregado abajo es nuevo. Sonidos, tiempos y umbrales de las
# alertas viven SOLO aqui; el paquete alertas no contiene numeros literales.
# ==========================================================================

# LABORATORIO - Modo silencioso: la cola y los temporizadores funcionan
# igual, pero no se emite sonido; se anota en la bitacora que "sonaria".
# Se activa tambien con:  python main.py --silencio
MODO_SILENCIOSO = False

# LABORATORIO - Deteccion de conexion de red (eventos por flanco y por tiempo)
PERIODO_CONEXION = 1.0              # cada cuantos segundos se revisa la conexion
PERIODO_RECORDATORIO_RED = 15.0     # cada cuantos segundos se repite red_sigue_desconectada
# Direcciones que NO prueban que haya red (loopback y autoasignadas).
PREFIJOS_IP_IGNORADOS = ("127.", "169.254.")
# Interfaces virtuales que casi siempre estan "arriba" aunque no haya red.
INTERFACES_IGNORADAS = ("lo", "Loopback", "vEthernet", "VirtualBox",
                        "VMware", "docker", "br-", "veth", "virbr")

# LABORATORIO - Cola de alertas (deque) y marcas de tiempo
COLA_MAX_ALERTAS = 10               # maximo de alertas esperando turno
ALERTA_CADUCA_S = 20.0              # una alerta que espero mas que esto ya no suena
PAUSA_ENTRE_ALERTAS_MS = 400        # silencio al terminar cada alerta

# LABORATORIO - Cada tono es un par (frecuencia en Hz, duracion en ms).
# SILENCIO_HZ marca una pausa dentro de la secuencia.
SILENCIO_HZ = 0
SECUENCIAS = {
    # grave y repetido dos veces: el procesador "esta trabajando duro"
    "cpu": ((300, 250), (SILENCIO_HZ, 100), (300, 250)),
    # tres pulsos medios: un recurso que se va llenando
    "memoria": ((600, 150), (SILENCIO_HZ, 100), (600, 150),
                (SILENCIO_HZ, 100), (600, 150)),
    # un solo tono agudo y corto: informacion que entra y sale
    "trafico": ((1200, 200),),
    # descendente: algo se cayo
    "conexion_perdida": ((900, 250), (SILENCIO_HZ, 100), (600, 250),
                         (SILENCIO_HZ, 100), (300, 400)),
    # ascendente: algo se recupero
    "conexion_recuperada": ((300, 200), (SILENCIO_HZ, 100), (600, 200),
                            (SILENCIO_HZ, 100), (900, 350)),
    # un tono unico y mas bajo: recordatorio, no alarma completa
    "recordatorio": ((500, 300),),
}

# LABORATORIO - Que evento dispara que secuencia
ALERTAS_POR_EVENTO = {
    "cpu_alta": "cpu",
    "ram_alta": "memoria",
    "red_pico": "trafico",
    "red_desconectada": "conexion_perdida",
    "red_conectada": "conexion_recuperada",
    "red_sigue_desconectada": "recordatorio",
}

# LABORATORIO - Generacion de los archivos de sonido (solo Windows).
# En macOS/Linux se usa la campana del sistema.
MUESTREO_HZ = 44100                 # muestras por segundo
CANALES = 1
BYTES_MUESTRA = 2                   # 16 bits
AMPLITUD_MAX = 32767                # maximo de un entero de 16 bits con signo
VOLUMEN = 0.5                       # 0.0 a 1.0
FADE_MS = 10                        # entrada/salida suave para evitar "clics"
MS_POR_SEGUNDO = 1000.0
CARPETA_SONIDOS = "telemetria_alertas"
EXTENSION_SONIDO = ".wav"
