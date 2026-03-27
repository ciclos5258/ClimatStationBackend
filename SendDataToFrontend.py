import paho.mqtt.client as mqtt
import json
import time
import threading
from flask import Flask, jsonify
from flask_cors import CORS

BROKER = "91.199.154.71"
PORT = 1883
USERNAME = "python"
PASSWORD = "pythonpassword"
TOPIC = "esp32/sensors"

chart_data = {
    "labels": [],
    "values": []
}

MAX_POINTS = 50

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Подключено к MQTT брокеру")
        client.subscribe(TOPIC)
        print(f"📡 Подписка на топик {TOPIC}")
    else:
        print(f"❌ Ошибка подключения к MQTT, код {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Выводим полученные данные для отладки
        print(f"📨 Получено: {payload}")
        
        update_chart_data(payload)
        
    except json.JSONDecodeError:
        print("❌ Ошибка: получен невалидный JSON")
    except Exception as e:
        print(f"❌ Ошибка обработки сообщения: {e}")

def update_chart_data(payload):
    global chart_data
    
    # Пробуем разные возможные имена полей
    temperature = payload.get('temperature') or payload.get('temp') or payload.get('value')
    
    if temperature is not None:
        timestamp = time.strftime('%H:%M:%S')
        chart_data["labels"].append(timestamp)
        chart_data["values"].append(float(temperature))
        
        if len(chart_data["labels"]) > MAX_POINTS:
            chart_data["labels"] = chart_data["labels"][-MAX_POINTS:]
            chart_data["values"] = chart_data["values"][-MAX_POINTS:]
            
        print(f"✅ Данные обновлены: {timestamp} = {temperature}°C")
    else:
        print(f"⚠️ Температура не найдена. Поля: {list(payload.keys())}")

def run_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:  # Добавляем цикл для автоматического переподключения
        try:
            print("🔄 Подключение к MQTT брокеру...")
            client.connect(BROKER, PORT, 60)
            client.loop_forever()
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            print("⏳ Повторная попытка через 10 секунд...")
            time.sleep(10)

# Flask Server
app = Flask(__name__)
CORS(app)

@app.route('/data', methods=['GET'])
def get_data():
    global chart_data
    return jsonify(chart_data)

@app.route('/health', methods=['GET'])
def health():
    """Эндпоинт для проверки работоспособности"""
    return jsonify({
        "status": "ok",
        "points": len(chart_data["labels"]),
        "last_value": chart_data["values"][-1] if chart_data["values"] else None
    })

def start_mqtt_thread():
    mqtt_thread = threading.Thread(target=run_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()

# Для запуска
if __name__ == '__main__':
    start_mqtt_thread()

    app.run(host='0.0.0.0', port=5000, debug=False)