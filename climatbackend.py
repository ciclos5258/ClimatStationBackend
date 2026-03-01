import paho.mqtt.client as mqtt
import json
import time

BROKER = "vps ip"
PORT = 1883
USERNAME = "user name"          
PASSWORD = "user password"
TOPIC = "esp32/sensors"
TIMEOUT = 15

# Флаг получения данных
data_received = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Подключено к брокеру")
        client.subscribe(TOPIC)
        print(f"Подписка на топик {TOPIC}")
    else:
        print(f"Ошибка подключения, код {rc}")

def on_message(client, userdata, msg):
    global data_received
    try:
        payload = json.loads(msg.payload.decode())
        print("\nПолучены данные:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        data_received = True
        client.disconnect()  # отключаемся после получения
    except Exception as e:
        print("Ошибка обработки сообщения:", e)

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()  # запускаем фоновый поток

# Ждём получения данных или таймаута
start = time.time()
while not data_received and (time.time() - start) < TIMEOUT:
    time.sleep(0.1)

if not data_received:
    print("Таймаут: данные не получены за", TIMEOUT, "секунд")

client.loop_stop()
client.disconnect()
