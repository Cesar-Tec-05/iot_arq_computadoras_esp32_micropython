# Importaciones con manejo de compatibilidad para MicroPython, tiempo y servos.
try:
	from machine import Pin
except ImportError:
	Pin = None
try:
	import time
except ImportError:
	import utime as time
try:
	from microservo import Servo as MicroServo
except Exception:
	MicroServo = None

"""
ControladorFoco: 
	clase que maneja el estado del servo, el boton, los LED y el buzzer.
"""
class ControladorFoco:
	"""
	Funcion para inicializar el controlador con la configuración de hardware.
	Parametros:
		- servo_pin: GPIO del servo (opcional)
		- servo_on_deg/servo_off_deg: grados para encendido/apagado del servo
		- led_pin: GPIO del LED principal (opcional)
		- led_off_pin: GPIO del LED que indica estado OFF (opcional)
		- buzzer_pin: GPIO del buzzer (opcional)
		- button_pin: GPIO del botón (opcional)
		- button_active_low: si el botón es activo en bajo (default True)
		- debounce_ms: tiempo de debounce para el botón (default 250ms)
	"""
	def __init__(
		self,
		servo_pin=None,
		servo_on_deg=90,
		servo_off_deg=180,
		led_pin=None,
		led_off_pin=None,
		buzzer_pin=None,
		button_pin=None,
		button_active_low=True,
		debounce_ms=250,
	):
		if Pin is None:
			raise RuntimeError('Este modulo requiere MicroPython')
		# Configuración de botón y debounce (para evitar rebotes en el botón físico)
		self.button_active_low = button_active_low
		self.debounce_ms = debounce_ms
		self._state = False
		self._button_event = False
		self._last_button_ms = 0
		# Configuración de servo
		self.servo_pin_no = servo_pin
		self._servo_on_deg = servo_on_deg
		self._servo_off_deg = servo_off_deg
		# Configuración de LED y buzzer
		self.led_pin_no = led_pin
		self.led_off_pin_no = led_off_pin
		self.buzzer_pin_no = buzzer_pin
		# Inicializar servo si se proporcionó pin y la librería está disponible
		self.servo = None
		if self.servo_pin_no is not None and MicroServo is not None:
			try:
				self.servo = MicroServo(pin_id=self.servo_pin_no)
			except Exception:
				self.servo = None
		# LED principal (on cuando state True)
		self.led = Pin(self.led_pin_no, Pin.OUT) if (self.led_pin_no is not None and Pin is not None) else None
		# LED adicional (on cuando state False)
		self.led_off = Pin(self.led_off_pin_no, Pin.OUT) if (self.led_off_pin_no is not None and Pin is not None) else None
		self.buzzer_pin = Pin(self.buzzer_pin_no, Pin.OUT) if (self.buzzer_pin_no is not None and Pin is not None) else None
		# Configurar botón con pull-up o pull-down según button_active_low
		self.button = None
		if button_pin is not None and Pin is not None:
			self.button = Pin(
				button_pin,
				Pin.IN,
				Pin.PULL_UP if button_active_low else Pin.PULL_DOWN,
			)
		# Inicializar estado sin producir el beep del buzzer al arrancar
		self._suppress_beep = True
		self._apply_state(False)
		self._suppress_beep = False
		# Configurar interrupción para el botón si se proporcionó
		if self.button is not None:
			trigger = Pin.IRQ_FALLING if button_active_low else Pin.IRQ_RISING
			self.button.irq(trigger=trigger, handler=self._on_button_irq)

	"""
	Funciones internas para aplicar el estado a los actuadores (servo, LED, buzzer).
	- El servo se mueve a los grados configurados para ON/OFF.
	- El LED principal se enciende cuando el estado es True.
	- El LED adicional se enciende cuando el estado es False.
	- El buzzer emite un beep corto cada vez que se cambia el estado (excepto durante la inicialización).
	"""
	def _apply_state(self, state):
		self._state = bool(state)
		# Control del servo: mover a posición ON u OFF según el estado
		if self.servo is not None:
			try:
				angle = self._servo_on_deg if self._state else self._servo_off_deg
				self.servo.write(angle)
			except Exception:
				pass
		# LED principal: on when state True
		if self.led is not None:
			try:
				self.led.value(1 if self._state else 0)
			except Exception:
				pass
		# LED_off (rojo): on when state is False
		if self.led_off is not None:
			try:
				self.led_off.value(1 if not self._state else 0)
			except Exception:
				pass
		# Buzzer: short beep on state change
		if self.buzzer_pin is not None:
			try:
				# Evitar beep durante la inicialización
				if not getattr(self, '_suppress_beep', False):
					self.buzzer_pin.value(1)
					time.sleep_ms(150)
					self.buzzer_pin.value(0)
			except Exception:
				pass

	"""
	Funciones para manejar eventos del botón físico y cambiar el estado.
	- `_on_button_irq`: manejador de interrupción para el botón, con debounce.
	- `consume_button_event`: función que se llama en el loop principal para verificar si hubo un evento de botón y consumirlo.
	- `set_state`: función para establecer el estado desde el servidor HTTP o el botón, aplicando los cambios a los actuadores.
	- `toggle`: función para alternar el estado actual (usada por el botón).
	- `state` y `state_name`: propiedades para obtener el estado actual en formato booleano o como cadena 'on'/'off'.
	"""
	def _on_button_irq(self, pin):
		now = time.ticks_ms()
		if time.ticks_diff(now, self._last_button_ms) < self.debounce_ms:
			return
		self._last_button_ms = now
		self._button_event = True
	def consume_button_event(self):
		if not self._button_event:
			return False
		self._button_event = False
		return True
	def set_state(self, state):
		self._apply_state(state)
		return self._state
	# removed PWM fallback; using microservo
	def toggle(self):
		return self.set_state(not self._state)
	@property
	def state(self):
		return self._state
	@property
	def state_name(self):
		return 'on' if self._state else 'off'
