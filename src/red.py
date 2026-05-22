# Importaciones necesarias para manejar la conexión WiFi y realizar solicitudes HTTP en MicroPython.
try:
	import network
except ImportError:
	network = None
try:
	import socket
except ImportError:
	import usocket as socket
try:
	import ujson as json
except ImportError:
	import json
try:
	import time
except ImportError:
	import utime as time

# Funciones para conectar a WiFi y realizar solicitudes HTTP POST con JSON, adaptadas para MicroPython.
def conectar_wifi(ssid, password, timeout_ms=8000):
	if network is None:
		raise RuntimeError('Este modulo requiere MicroPython')
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	if wlan.isconnected():
		return wlan
	wlan.connect(ssid, password)
	inicio = time.ticks_ms()
	while not wlan.isconnected():
		if time.ticks_diff(time.ticks_ms(), inicio) > timeout_ms:
			raise RuntimeError('No se pudo conectar a WiFi')
		time.sleep_ms(200)
	return wlan

# Función para realizar una solicitud HTTP POST con un payload JSON, manejando la construcción de la solicitud y la lectura de la respuesta.
def http_post_json(url, payload, timeout_s=3):
	esquema, resto = url.split('://', 1)
	if esquema != 'http':
		raise ValueError('Solo se admite http://')
	host_port, path = _separar_host_y_path(resto)
	host, port = _separar_host_y_port(host_port)
	cuerpo = json.dumps(payload)
	request = (
		'POST {} HTTP/1.1\r\n'
		'Host: {}\r\n'
		'Content-Type: application/json\r\n'
		'Content-Length: {}\r\n'
		'Connection: close\r\n\r\n'
		'{}'
	).format(path, host, len(cuerpo), cuerpo)
	return _http_request(host, port, request, timeout_s)

# Funciones auxiliares para parsear URLs y manejar la construcción de solicitudes HTTP, adaptadas para MicroPython.
def _separar_host_y_path(resto):
	if '/' in resto:
		host_port, path = resto.split('/', 1)
		return host_port, '/' + path
	return resto, '/'

# Función para separar el host y el puerto de una cadena, con un valor predeterminado de puerto 80 si no se especifica.
def _separar_host_y_port(host_port):
	if ':' in host_port:
		host, port = host_port.split(':', 1)
		return host, int(port)
	return host_port, 80

# Función para realizar una solicitud HTTP, manejando la conexión, el envío de la solicitud y la lectura de la respuesta, con manejo de excepciones para conexiones cerradas.
def _http_request(host, port, request, timeout_s):
	client = socket.socket()
	try:
		addr = socket.getaddrinfo(host, port)[0][-1]
		client.settimeout(timeout_s)
		client.connect(addr)
		client.send(request.encode())
		respuesta = b''
		while True:
			try:
				chunk = client.recv(256)
			except OSError as exc:
				# Algunos firmwares reportan ECONNRESET cuando el peer cierra rápido.
				if len(exc.args) > 0 and exc.args[0] in (104,):
					break
				raise
			if not chunk:
				break
			respuesta += chunk
		return respuesta.decode(errors='ignore')
	finally:
		try:
			client.close()
		except Exception:
			pass
