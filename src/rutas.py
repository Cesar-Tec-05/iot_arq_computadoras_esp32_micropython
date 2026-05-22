# Importaciones necesarias para manejar rutas HTTP, parsear solicitudes y enviar respuestas, así como para realizar solicitudes HTTP a un backend.
try:
	import ujson as json
except ImportError:
	import json
from red import http_post_json

# Clase RouterHTTP que maneja las rutas HTTP para controlar el hardware y registrar eventos, con funciones para parsear solicitudes y construir respuestas.
class RouterHTTP:
	# Función de inicialización que recibe un controlador para manejar el hardware y una URL de backend para enviar logs de eventos.
	def __init__(self, controlador, backend_url=None):
		self.controlador = controlador
		self.backend_url = backend_url

	# Función para despachar las solicitudes HTTP entrantes, manejando la ruta /status para controlar el estado del hardware y registrar eventos, y devolviendo respuestas JSON.
	def dispatch(self, metodo, ruta, query):
		if metodo == 'GET' and ruta == '/rele':
			estado = query.get('state')
			if estado not in ('on', 'off'):
				return 400, {'Content-Type': 'application/json'}, json.dumps({
					'error': 'state debe ser on u off',
				})
			self.controlador.set_state(estado == 'on')
			self._enviar_log(estado, 'server')
			return 200, {'Content-Type': 'application/json'}, json.dumps({
				'ok': True,
				'state': self.controlador.state_name,
				'source': 'server',
			})
		return 404, {'Content-Type': 'application/json'}, json.dumps({
			'error': 'Ruta no encontrada',
		})

	# Función para manejar el evento del botón físico, alternando el estado del hardware, registrando el evento y devolviendo el nuevo estado.
	def atender_boton(self):
		estado = self.controlador.toggle()
		self._enviar_log(self.controlador.state_name, 'button')
		return estado

	# Funciones auxiliares para obtener el estado básico del hardware y enviar logs de eventos al backend, con manejo de excepciones para evitar fallos en caso de problemas de conexión.
	def _estado_basico(self):
		return {
			'ok': True,
			'state': self.controlador.state_name,
		}

	# Función para enviar un log de evento al backend, con el formato de acción y fuente, y manejo de excepciones para evitar fallos en caso de problemas de conexión.
	def _enviar_log(self, action, source):
		if not self.backend_url:
			return
		try:
			http_post_json(
				self.backend_url.rstrip('/') + '/esp/receive-state',
				{
					'action': action,
					'source': source,
				},
			)
		except Exception:
			pass

# Funciones auxiliares para parsear la línea de solicitud HTTP, construir respuestas HTTP y manejar rutas y consultas, adaptadas para MicroPython.
def parse_request_line(request_text):
	primera_linea = request_text.split('\r\n', 1)[0]
	partes = primera_linea.split()
	if len(partes) < 2:
		return None, None, {}
	metodo = partes[0]
	ruta_completa = partes[1]
	ruta, query = _parse_path_and_query(ruta_completa)
	return metodo, ruta, query

# Función para construir una respuesta HTTP con el código de estado, encabezados y cuerpo proporcionados, formateando correctamente la respuesta para ser enviada al cliente.
def _parse_path_and_query(ruta_completa):
	if '?' not in ruta_completa:
		return ruta_completa, {}
	ruta, query_string = ruta_completa.split('?', 1)
	query = {}
	for pair in query_string.split('&'):
		if not pair:
			continue
		if '=' in pair:
			key, value = pair.split('=', 1)
		else:
			key, value = pair, ''
		query[key] = value
	return ruta, query

# Función para construir una respuesta HTTP con el código de estado, encabezados y cuerpo proporcionados, formateando correctamente la respuesta para ser enviada al cliente.
def build_response(status_code, headers, body):
	messages = {
		200: 'OK',
		400: 'Bad Request',
		404: 'Not Found',
		500: 'Internal Server Error',
	}
	reason = messages.get(status_code, 'OK')
	header_lines = ['HTTP/1.1 {} {}'.format(status_code, reason)]
	for key, value in headers.items():
		header_lines.append('{}: {}'.format(key, value))
	header_lines.append('Content-Length: {}'.format(len(body)))
	header_lines.append('Connection: close')
	header_lines.append('')
	header_lines.append(body)
	return '\r\n'.join(header_lines)
