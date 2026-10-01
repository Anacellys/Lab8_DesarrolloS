"""
pruebas/test_alertas.py
# LABORATORIO: archivo nuevo completo.

Pruebas unitarias con unittest. No necesitan parlantes ni red real:
la lectura de conexion y el sonido se sustituyen por versiones falsas.

Ejecutar desde la carpeta raiz del proyecto:
    python -m unittest pruebas.test_alertas -v
"""
import os
import tempfile
import time
import unittest
import wave
from unittest import mock

import almacenamiento as registro
import alertas
import config
import eventos
from alertas import conexion, reproductor, sonidos

BASE = time.time()                       # LABORATORIO - hora de referencia


# LABORATORIO
class PruebasConexion(unittest.TestCase):
    """Eventos de conexion: flanco de bajada, de subida y recordatorio."""

    def setUp(self):
        conexion.reiniciar()

    def _lectura(self, valor):
        return mock.patch.object(conexion, "esta_conectada",
                                 return_value=valor)

    def test_primera_lectura_no_genera_evento(self):
        with self._lectura(True):
            self.assertEqual(conexion.detectar(BASE), [])

    def test_perdida_genera_red_desconectada_una_sola_vez(self):
        with self._lectura(True):
            conexion.detectar(BASE)
        t1 = BASE + config.PERIODO_CONEXION
        with self._lectura(False):
            primeros = conexion.detectar(t1)
            repetido = conexion.detectar(t1 + config.PERIODO_CONEXION)
        self.assertEqual([e[0] for e in primeros], ["red_desconectada"])
        self.assertEqual(repetido, [])        # flanco: no se repite

    def test_recuperacion_genera_red_conectada(self):
        with self._lectura(True):
            conexion.detectar(BASE)
        t1 = BASE + config.PERIODO_CONEXION
        with self._lectura(False):
            conexion.detectar(t1)
        t2 = t1 + config.PERIODO_CONEXION
        with self._lectura(True):
            evs = conexion.detectar(t2)
        self.assertEqual([e[0] for e in evs], ["red_conectada"])

    def test_recordatorio_solo_al_cumplirse_el_intervalo(self):
        with self._lectura(True):
            conexion.detectar(BASE)
        t1 = BASE + config.PERIODO_CONEXION
        with self._lectura(False):
            conexion.detectar(t1)
            antes = conexion.detectar(
                t1 + config.PERIODO_RECORDATORIO_RED - config.PERIODO_CONEXION)
            llega = conexion.detectar(t1 + config.PERIODO_RECORDATORIO_RED)
        self.assertEqual(antes, [])
        self.assertEqual([e[0] for e in llega], ["red_sigue_desconectada"])

    def test_respeta_el_periodo_de_revision(self):
        with self._lectura(True) as falso:
            conexion.detectar(BASE)
            conexion.detectar(BASE)           # misma hora: no vuelve a leer
            self.assertEqual(falso.call_count, 1)

    def test_lectura_desconocida_no_inventa_eventos(self):
        with self._lectura(None):
            self.assertEqual(conexion.detectar(BASE), [])


# LABORATORIO
class PruebasCola(unittest.TestCase):
    """Los eventos con alerta entran a la cola; los demas, no."""

    def setUp(self):
        reproductor._cola.clear()
        reproductor._pasos.clear()
        reproductor._fin_paso = None

    def test_evento_con_alerta_entra_a_la_cola(self):
        self.assertTrue(alertas.encolar("cpu_alta", BASE))
        self.assertEqual(list(reproductor._cola), [("cpu", BASE)])

    def test_evento_sin_alerta_no_entra(self):
        self.assertFalse(alertas.encolar("disco_lleno", BASE))
        self.assertEqual(list(reproductor._cola), [])

    def test_orden_de_llegada(self):
        alertas.encolar("cpu_alta", BASE)
        alertas.encolar("ram_alta", BASE)
        self.assertEqual([a[0] for a in reproductor._cola],
                         ["cpu", "memoria"])

    def test_la_cola_respeta_el_maximo(self):
        for _ in range(config.COLA_MAX_ALERTAS + config.COLA_MAX_ALERTAS):
            alertas.encolar("cpu_alta", BASE)
        self.assertEqual(len(reproductor._cola), config.COLA_MAX_ALERTAS)

    def test_todos_los_eventos_de_config_tienen_secuencia(self):
        for secuencia in config.ALERTAS_POR_EVENTO.values():
            self.assertIn(secuencia, config.SECUENCIAS)

    def test_el_despachador_encola_el_evento_atendido(self):
        eventos.atender("red_desconectada", {"hora": "00:00:00"})
        self.assertEqual([a[0] for a in reproductor._cola],
                         ["conexion_perdida"])


# LABORATORIO
class PruebasReproductor(unittest.TestCase):
    """El reproductor avanza por marcas de tiempo y nunca espera."""

    def setUp(self):
        reproductor._cola.clear()
        reproductor._pasos.clear()
        reproductor._fin_paso = None
        reproductor._silencio = False
        patcher = mock.patch.object(sonidos, "tono")
        self.tono = patcher.start()
        self.addCleanup(patcher.stop)

    def test_inicia_el_primer_tono_de_la_alerta(self):
        alertas.encolar("red_pico", BASE)
        reproductor.actualizar(BASE)
        hz, ms = config.SECUENCIAS["trafico"][0]
        self.tono.assert_called_once_with(hz, ms)

    def test_mientras_suena_no_arranca_otro_tono(self):
        alertas.encolar("cpu_alta", BASE)
        reproductor.actualizar(BASE)
        llamadas = self.tono.call_count
        _, ms = config.SECUENCIAS["cpu"][0]
        reproductor.actualizar(BASE + ms / config.MS_POR_SEGUNDO / 2)
        self.assertEqual(self.tono.call_count, llamadas)

    def test_al_terminar_un_tono_sigue_el_siguiente(self):
        alertas.encolar("cpu_alta", BASE)
        reproductor.actualizar(BASE)
        _, ms = config.SECUENCIAS["cpu"][0]
        t = BASE + ms / config.MS_POR_SEGUNDO
        reproductor.actualizar(t)                # empieza la pausa
        _, ms_pausa = config.SECUENCIAS["cpu"][1]
        reproductor.actualizar(t + ms_pausa / config.MS_POR_SEGUNDO)
        hz2, ms2 = config.SECUENCIAS["cpu"][-1]
        self.tono.assert_called_with(hz2, ms2)

    def test_llegan_alertas_mientras_suena_otra(self):
        alertas.encolar("cpu_alta", BASE)
        reproductor.actualizar(BASE)             # empieza a sonar
        alertas.encolar("ram_alta", BASE)        # llega otra mientras tanto
        self.assertEqual([a[0] for a in reproductor._cola], ["memoria"])

    def test_alerta_caducada_se_descarta(self):
        alertas.encolar("cpu_alta", BASE)
        tarde = BASE + config.ALERTA_CADUCA_S + config.PERIODO_CONEXION
        reproductor.actualizar(tarde)
        self.tono.assert_not_called()
        self.assertEqual(list(reproductor._cola), [])

    def test_modo_silencioso_no_emite_sonido_pero_avanza(self):
        reproductor._silencio = True
        alertas.encolar("cpu_alta", BASE)
        reproductor.actualizar(BASE)
        self.tono.assert_not_called()
        self.assertTrue(reproductor.estado()["sonando"])

    def test_actualizar_regresa_de_inmediato(self):
        """Aunque haya alertas largas, actualizar() no espera nada."""
        for _ in range(config.COLA_MAX_ALERTAS):
            alertas.encolar("red_desconectada", BASE)
        inicio = time.perf_counter()
        reproductor.actualizar(BASE)
        self.assertLess(time.perf_counter() - inicio,
                        config.PERIODO_CONEXION)


# LABORATORIO
class PruebasSonidos(unittest.TestCase):
    """La generacion del .wav produce un archivo con la duracion correcta."""

    def test_el_wav_generado_dura_lo_configurado(self):
        hz, ms = config.SECUENCIAS["trafico"][0]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "tono" + config.EXTENSION_SONIDO)
            sonidos._generar(ruta, hz, ms)
            with wave.open(ruta, "rb") as w:
                duracion = w.getnframes() / w.getframerate()
        self.assertAlmostEqual(duracion, ms / config.MS_POR_SEGUNDO,
                               places=3)


# LABORATORIO
class PruebasIntegracion(unittest.TestCase):
    """Los tres eventos nuevos tienen manejador registrado."""

    def test_eventos_de_conexion_conocidos(self):
        conocidos = eventos.eventos_conocidos()
        for nombre in ("red_desconectada", "red_conectada",
                       "red_sigue_desconectada"):
            self.assertIn(nombre, conocidos)

    def test_el_manejador_registra_en_la_bitacora(self):
        antes = len(registro.eventos())
        eventos.atender("red_sigue_desconectada", {"segundos": BASE})
        self.assertGreater(len(registro.eventos()), antes)


if __name__ == "__main__":
    unittest.main()
