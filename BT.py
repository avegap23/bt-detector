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
import tkinter as tk # https://docs.python.org/3/library/tkinter.html
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

    # 1.- Aparecen los dispositivos cercanos: recibimos el nombre y la distancia al dispositivo
    dispositivos_encontrados.sort(key = lambda elemento: (elemento["distancia"] if elemento["distancia"] is not None else float("inf"), elemento["nombre"].lower()))
    # Si el dispositivo tiene la distancia calculada, usalá
    # Si tiene None, utiliza distancia "infinita", como si fuese "X"

    return dispositivos_encontrados

# CLASS --------------------------------------------------------------------------------------
class AppBluetooth:
    # Método constructor
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Escaner de cercanía Bluetooth")
        self.ventana.geometry("880x500")
        self.ventana.minsize(700, 400)

        self.crear_interfaz() # llamada al método de la clase para la creación del frontend

    # Métodos de la clase
    def crear_interfaz(self):
        # Título
        titulo = ttk.Label(self.ventana, text="Dispositivos detectados", font=("Segoe UI", 16, "bold"))
        titulo.pack(pady=(15, 5))

        # Descripción
        descripcion = ttk.Label(self.ventana, text="Muestra nombre, RSSI y la estimación de la distancia")
        descripcion.pack(pady=(0, 4))

        # Avisos
        aviso = ttk.Label(self.ventana, text="El cálculo de distancia suele variar si hay interferencias (muebles, paredes, personas...)")
        aviso.pack(pady=(0, 10))

        # Tabla
        marco_tabla = ttk.Frame(self.ventana)
        marco_tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.tabla = ttk.Treeview(marco_tabla, columns=("nombre", "direccion", "rssi", "distancia"), show="headings", selectmode="browse")

        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("direccion", text="Dirección/UUID")
        self.tabla.heading("rssi", text="RSSI")
        self.tabla.heading("distancia", text="Distancia (aprox.)")

        self.tabla.column("nombre", width=220, minwidth=130, anchor=tk.W)
        self.tabla.column("direccion", width=280, minwidth=180, anchor=tk.W)
        self.tabla.column("rssi", width=100, minwidth=80, anchor=tk.CENTER)
        self.tabla.column("distancia", width=170, minwidth=130, anchor=tk.CENTER)

        # Construcción de la barra vertical (scrollbar)
        scroll_vertical = ttk.Scrollbar(marco_tabla, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_vertical.set)

        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_vertical.pack(side=tk.RIGHT, fill=tk.Y)

        # Marco inferior tabla
        marco_inferior = ttk.Frame(self.ventana)
        marco_inferior.pack(fill=tk.X, padx=15, pady=15)

        self.estado = ttk.Label(marco_inferior, text="Preparado para escanear...")
        self.estado.pack(side=tk.LEFT)

        # Creación de botón
        self.boton_escanear = ttk.Button(marco_inferior, text="Escanear", command=self.iniciar_escaneo)
        self.boton_escanear.pack(side=tk.RIGHT)

    def iniciar_escaneo(self):
        self.boton_escanear.config(state=tk.DISABLED, text="Escaneando...")
        self.estado.config(text=(f"Buscando dispositivos durante {SCAN_TIMEOUT:.0f} segundos..."))

        # Preparación de la tabla para insertar información
        for elemento in self.tabla.get_children():
            self.tabla.delete(elemento)

        # Vamos de costureo: hilos
        hilo = threading.Thread(target=self.ejecutar_escaneo, daemon=True)
        hilo.start()

    def ejecutar_escaneo(self):
        # Creación del escaner de eventos (bucle de eventos, mejor dicho)
        loop = asyncio.new_event_loop()

        # Escuchando...
        try:
            asyncio.set_event_loop(loop)
            dispositivos = loop.run_until_complete(buscar_dispositivos()) # procedemos a buscar...

            self.ventana.after(0, self.mostrar_resultados, dispositivos) # después del escaneo

        except Exception as error:
            self.ventana.after(0, self.mostrar_error, str(error))

        finally:
            loop.close() # cierre del bucle

    def mostrar_resultados(self, dispositivos):
        for dispositivo in dispositivos:
            #adquiriendo la información desde el dispositivo
            rssi = dispositivo["rssi"]
            distancia = dispositivo["distancia"]

            # textualizando la información
            texto_rssi = (f"{rssi} dBm" if rssi is not None else "No disponible")
            texto_distancia = (f"{distancia:.2f} m" if rssi is not None else "No disponible")

            # inserción de la info en la tabla
            self.tabla.insert("", tk.END, values=(dispositivo["nombre"], dispositivo["direccion"], texto_rssi, texto_distancia))

        # calculando los dispositivos que se hayan encontrado para...
        cantidad = len(dispositivos)

        if cantidad == 0:
            self.estado.config(text="No se han encontrado dispositivos BLE")
        else:
            self.estado.config(text=f"Escaneo finalizado: {cantidad} dispositivo(s)")

        # boton escanear
        self.boton_escanear.config(state=tk.NORMAL, text="Escanear")

    def mostrar_error(self, mensaje):
        self.estado.config(text="El escaneo no se pudo completar")
        self.boton_escanear.config(state=tk.NORMAL, text="Escanear")

        # mostrando una ventana de información y error
        messagebox.showerror(
             "Error",
             "No se ha podido completar el escaneo:\n\n"
             f"{mensaje}\n\n"
             "Comprobar la conexión Bluetooth y si 'Bleak' está instalado"
        )

# MAIN --------------------------------------------------------------------------------------------
def main():
    ventana = tk.Tk()
    AppBluetooth(ventana)
    ventana.mainloop()

if __name__ == "__main__":
    main()