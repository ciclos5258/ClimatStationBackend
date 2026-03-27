import paho.mqtt.client as mqtt
import json
import time
import sqlite3

BROKER = "91.199.154.71"
PORT = 1883
USERNAME = "python"
PASSWORD = "pythonpassword"
TOPIC = "esp32/sensors"
TIMEOUT = 15

# Флаг получения данных
data_received = False

def init_database():
    """Создаёт таблицу при запуске программы"""
    conn = sqlite3.connect("sensors.db")
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temp REAL,
                hum REAL
            )
        ''')
        conn.commit()
        print("База данных готова")
    finally:
        conn.close()

def save_data(temp, hum):
    """Сохраняет данные в базу"""
    conn = sqlite3.connect("sensors.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sensors (temp, hum) VALUES (?, ?)", (temp, hum))
        conn.commit()
        print(f"✅ Данные сохранены: temp={temp}, hum={hum}")
    finally:
        conn.close()

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

        # Извлекаем данные из JSON
        temperature = payload.get('temperature')
        humidity = payload.get('humidity')

        # Сохраняем в базу, если данные есть
        if temperature is not None and humidity is not None:
            save_data(temperature, humidity)
        else:
            print("⚠️ Не найдены поля temperature или humidity в JSON")

        data_received = True
        client.disconnect()
    except Exception as e:
        print("Ошибка обработки сообщения:", e)

# Инициализируем базу данных
init_database()

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

# Ждём получения данных или таймаута
start = time.time()
while not data_received and (time.time() - start) < TIMEOUT:
    time.sleep(0.1)

if not data_received:
    print("Таймаут: данные не получены за", TIMEOUT, "секунд")

client.loop_stop()
client.disconnect()