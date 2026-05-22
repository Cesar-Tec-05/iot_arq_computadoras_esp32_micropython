# Importaciones necesarias para el funcionamiento del servidor HTTP, control del servo, manejo de GPIO, y conexión WiFi.
from controlador import ControladorFoco
from red import conectar_wifi, http_post_json
from rutas import RouterHTTP, build_response, parse_request_line
try:
	import socket
except ImportError:
	import usocket as socket
try:
	import time
except ImportError:
	import utime as time

# Variables de configuración para WiFi, hardware y servidor HTTP.
SSID = 'INF.'
PASSWORD = 'cesar2005'
BACKEND_URL = 'http://10.33.131.61:3000'
BUTTON_PIN = 16
BUTTON_ACTIVE_LOW = True
SERVO_PIN = 27
SERVO_ON_DEG = 50
SERVO_OFF_DEG = 140
LED_PIN = 32
BUZZER_PIN = 15
RED_LED_PIN = 33
HOST = '0.0.0.0'
PORT = 80

"""
Ejecutar el servidor HTTP que maneja las solicitudes para controlar el el hardware y eventos http.
"""
def ejecutar_servidor():
	wlan = conectar_wifi(SSID, PASSWORD, timeout_ms=8000)
	backend_url = BACKEND_URL
	controlador = ControladorFoco(
		servo_pin=SERVO_PIN,
		servo_on_deg=SERVO_ON_DEG,
		servo_off_deg=SERVO_OFF_DEG,
		led_pin=LED_PIN,
		led_off_pin=RED_LED_PIN,
		buzzer_pin=BUZZER_PIN,
		button_pin=BUTTON_PIN,
		button_active_low=BUTTON_ACTIVE_LOW,
	)
	router = RouterHTTP(controlador, backend_url=backend_url)
	print('WiFi conectado:', wlan.ifconfig())
	print('Servidor HTTP listo en http://{}:{}'.format(wlan.ifconfig()[0], PORT))
	print('Backend URL:', backend_url)
	servidor = socket.socket()
	servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	servidor.bind((HOST, PORT))
	servidor.listen(1)
	servidor.settimeout(1)
	try:
		while True:
			if controlador.consume_button_event():
				estado = router.atender_boton()
				print('Boton fisico:', 'ON' if estado else 'OFF')
			try:
				cliente, _ = servidor.accept()
			except OSError:
				time.sleep_ms(20)
				continue
			try:
				cliente.settimeout(1)
				request = cliente.recv(1024).decode('utf-8', 'ignore')
				metodo, ruta, query = parse_request_line(request)
				if metodo is None:
					respuesta = build_response(
						400,
						{'Content-Type': 'application/json'},
						'{"error":"Solicitud invalida"}',
					)
				else:
					status, headers, body = router.dispatch(metodo, ruta, query)
					respuesta = build_response(status, headers, body)
				cliente.send(respuesta.encode())
			except Exception as exc:
				error = build_response(
					500,
					{'Content-Type': 'application/json'},
					'{{"error":"{}"}}'.format(exc),
				)
				try:
					cliente.send(error.encode())
				except Exception:
					pass
			finally:
				cliente.close()
	finally:
		servidor.close()

# Punto de entrada del programa, que inicia el servidor HTTP.
if __name__ == '__main__':
	ejecutar_servidor()
