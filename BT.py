'''
PAN: Personal Area Network
Bluetooth: es una tecnología de radiofrecuencia, utilizada para el intercambio de datos a corta
distancia.

Caracterísitcas:
    - utiliza radio UHF (banda ISM de 2.4GHz)
    - se pueden unir múltiples dispositivos entre sí, eliminando problemas de sincronización
    - se utiliza (principalmente) para dispositivos BLE (Bluetooth Low Energy)
    - es casi todos los casos, tenemos dispositivos maestros y dispositivos esclavos

Funcionamiento:
    1º: arrancamos en modo "descubrimiento", es decir se emite y recibe información:
        - dirección MAC: la huella (identificador único) del dispositivo
        - nombre dispositivo: nombre "legible", normalmente marca-modelo
        - RSSI: indicador de fuerza de señar recibida: medida de potencia de señal recibida, la cual
        utilizamos para estimar la distancia
        - servicios disponibles: conjunto de funcionalidades disponibles en el dispositivo
        - características de esos servicios: detalles específicos
    
    2º: RSSI - indicador de fuerza de señal recibida, NO CALIDAD DE LA SEÑAL. Valores de 0 a -80 dBm
        - dBm: unidad de medida en relación a la potencia expresada en decibelios relativa a milivatio, es decir,
        nivel de cobertura en función de los dBm en aire recibidos

    · 0: señal ideal, sólo con condiciones de laboratorio (ideales)
    · -40 a -60: señal idónea, tasas de transmisión estables
    · -60: enlace bueno, ajustando la transmisión se puede lograr una conexión estable (80%)
    · -70: enlace medio-bajo, señal buena, pero sufre problemas con lluvia y viento
    · -80: señal mínima, con cortes de transmisión (llamada, envío de mensajes...), incluyendo llegada
    de mensajes corruptos e incompletos

    ¡TRADUCIENDO!
    - Menos de -76 dBm: cobertura excelente
    - Entre -89 y -77 dBm: cobertura muy buena
    - Entre -97 y -90 dBm: cobertura buena/media
    - Entre -103 y -98 dBm: cobertura baja
    - Entre -112 y -104 dBm: cobertura muy baja (problemas establecimiento de llamadas)
    - Estre -113 y -132 dBm: cobertura excesivamente baja (problemas de llamadas y bajo rendimiento)
    - A partir de -135 dBm: sin cobertura

    3º: calculo de distancias:
        distancia - 10 ^((RSSI_REF - RSSI) / (10 * n))
            - distancia: estimación de distancia entre dispositivos (emisor - receptor)
            - RSSI_REF: RSSI medido a 1 metro del emisor
            - RSSI: medición actual del RSSI
            - n: exponente de pérdida de trayectoria (2 espacios abiertos / 2.2-3.0 espacios con obstaculos)
'''

# IMPORTS -----------------------------------------------------------------------------------------
import asyncio # https://docs.python.org/3/library/asyncio.html
import threading # https://docs.python.org/3/library/threading.html
import tkinter as tk # https://docs.python.org/3/library/tkinter.htm
from tkinter import messagebox, ttk # https://docs.python.org/3/library/tkinter.messagebox.html, https://docs.python.org/3/library/tkinter.ttk.html

from bleak import BleakScanner # https://bleak.readthedocs.io/en/latest/index.html

# CONSTANTES --------------------------------------------------------------------------------------
SCAN_TIMEOUT = 6.0 # duración de cada búsqueda BT
RSSI_A_UN_METRO = -50 # RSSI aproximado recibido a 1 metro cuando el dispositivo no anuncia su potencia
EXPONENTE_ENTORNO = 2.2 # 2.0 (espacio abierto) y 2.2-3.0 (interiores con obstáculos)

# FUNCTIONS ---------------------------------------------------------------------------------------
def calcular_distancia(rssi, tx_power=None):
    """
    Calcula la distancia aproximada en metros usando RSSI.
    ¡Es una estimación orientativa, ya que hay interferencias/orientaciones que pueden interferir!
    """

    # Maldades: no hay cobertura
    if rssi is None:
        return None
    
    potencia_referencia = (tx_power if tx_power is not None else RSSI_A_UN_METRO)

    # Cálculo real de la distancia: distancia al emisor teniendo en cuenta los "problemas"
    distancia = 10 ** (potencia_referencia - rssi) / (10 * EXPONENTE_ENTORNO)
    # https://www.minew.com/es/bluetooth-technology/

    return max(0.05, min(distancia, 1000.0))

async def buscar_dispositivos():
    """
    Busca dispositivos Bluetooth Low Energy, devolviendo:
        - nombre            - RSSI      - distancia aproximada
        - dirección MAC     - TX power  - servicios (depende del BLE)
    """

    dispositivos_encontrados = []

    # Vamos a la búsqueda del "Santo Grial" para nuestro BT
    try:
        resultados = await BleakScanner.discover(
            timeout = SCAN_TIMEOUT, return_adv=True
        )

        for dispositivo, anuncio in resultados.values():
            nombre = (getattr(anuncio, "local_name", None) or dispositivo.name or "Sin nombre")
            rssi = getattr(anuncio, "rssi", None)
            tx_power = getattr(anuncio, "tx_power", None)

            dispositivos_encontrados.append({
                "nombre": nombre,
                "direccion": dispositivo.address, # dirección MAC del dispositivo
                "rssi": rssi,
                "tx_power": tx_power,
                "distancia": calcular_distancia(rssi, tx_power),
            })
            
    except TypeError:
        # compatibilidad con las versiones antiguas de Bleak

        resultados = await BleakScanner.discover(timeout=SCAN_TIMEOUT)

        for dispositivo in resultados:
            nombre = dispositivo.name or "Sin nombre"
            rssi = getattr(anuncio, "rssi", None)

            dispositivos_encontrados.append({
                "nombre": nombre,
                "direccion": dispositivo.address, # dirección MAC del dispositivo
                "rssi": rssi,
                "tx_power": None,
                "distancia": calcular_distancia(rssi),
            })