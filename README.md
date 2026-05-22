# iot_arq_computadoras_esp32_micropython
Programa MicroPython para un ESP32 que controla una cerradura inteligente, con comunicación HTTP para recibir comandos y reportar cambios de estado a un servidor.
El ESP32 expone un servidor HTTP simple en la red local y registra cada cambio en un backend por IP fija.

## Configuracion
Edita [src/main.py](src/main.py) y ajusta estas variables:
- `SSID` y `PASSWORD` para tu red WiFi.
- `BACKEND_URL` con la IP o nombre resoluble del backend, por ejemplo `http://10.33.131.61:3000`.
- `BUTTON_PIN` segun tu cableado.
- `SERVO_PIN`, `SERVO_ON_DEG` y `SERVO_OFF_DEG` segun tu servo.
- `LED_PIN` para el LED principal.
- `RED_LED_PIN` para el LED rojo que se enciende cuando el sistema esta apagado.
- `BUZZER_PIN` para el buzzer.

## Endpoints del ESP32
- `GET /esp/rele?state=on|off` para cambiar el estado desde el servidor.
- `POST /esp/receive-state` manda registro al servidor si se manipula fisicamnte.

El estado `on` mueve el servo a `SERVO_ON_DEG` y enciende el LED principal.
El estado `off` mueve el servo a `SERVO_OFF_DEG` y enciende el LED rojo.

## Flujo
- El backend puede mandar el cambio al ESP32 por HTTP.
- El boton fisico cambia el estado localmente.
- Cada cambio intenta registrarse en `POST /esp/receive-state` del backend.

## Notas
- El servidor escucha en el puerto 80.
- Se trabaja con la IP del ESP32.
