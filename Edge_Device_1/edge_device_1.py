import time
import paho.mqtt.client as mqtt
import json
import serial
import pymysql

device = '/dev/ttyS2'
arduino = serial.Serial(device, 9600)

broker = 'demo.thingsboard.io'
ACCESS_TOKEN = 'UX0FcasnTGEu9lXRuT3m'

client = mqtt.Client()

def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe('v1/devices/me/rpc/request/+')
    client.subscribe('v1/devices/me/attributes')

def on_message(client, userdata, message, properties=None):
    data = json.loads(message.payload)
    print(data)
    if data['method'] == 'setState':
        if data['params'] == 'turnon1':
            arduino.write(b'1')  # Set state to 1
            update_sensor_state(1)
        elif data['params'] == 'turnon2':
            arduino.write(b'2')  # Set state to 1
            update_sensor_state(2)

def update_sensor_state(state):
    dbConn = pymysql.connect(user='nguyen', password='123321', host='192.168.56.1', port=3306, database='data_sensor')
    cursor = dbConn.cursor()

    query = "UPDATE sensor_data SET state = %s WHERE id = 1"
    cursor.execute(query, (state,))
    dbConn.commit()

client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(ACCESS_TOKEN)
client.connect(broker, 1883, 60)
client.loop_start()

try:
    while True:
        data = arduino.readline().decode('utf-8').strip()
        values = data.split(';')

        if len(values) == 3:
            water_value = int(values[0])
            humidity = float(values[1])
            temperature = float(values[2])
            print(water_value)
            print(humidity)
            print(temperature)

            dbConn = pymysql.connect(user='nguyen', password='123321', host='192.168.56.1', port=3306, database='data_sensor')
            cursor = dbConn.cursor()

            query = "UPDATE sensor_data SET water_level = %s, temperature = %s, humidity = %s WHERE id = 1"
            cursor.execute(query, (water_value, temperature, humidity))
            dbConn.commit()

            sensor_data = {'temperature': temperature, 'humidity': humidity, 'water': water_value}
            client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()
