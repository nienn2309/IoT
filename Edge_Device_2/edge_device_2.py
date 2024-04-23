import serial
import pymysql
import time
import paho.mqtt.client as mqtt
import json
import time

device = '/dev/ttyS0'
arduino = serial.Serial(device, 9600)

broker = 'demo.thingsboard.io'
ACCESS_TOKEN = '72cHCx1j27tVhd7ka0nC'

INTERVAL = 2

next_reading = time.time()

client = mqtt.Client()

def on_connect(client, userdate, flags, reason_code, properties=None):
    client.subscribe('v1/devices/me/rpc/request/+')
    client.subscribe('v1/devices/me/attributes')
    
def on_message(client, userdata, message, properties=None):
    data = json.loads(message.payload)
    print(data)
    if data['method'] == 'setState':
        print("setState method received.")
        if data['params'] == 'turn1':
            arduino.write(b'1')
            update_sensor_state_led1(True)
        elif data['params'] =='turn2':
            arduino.write(b'2')
            update_sensor_state_led1(False)
        elif data['params'] == 'turn3':
            arduino.write(b'3')
            update_sensor_state_led2(True)
        elif data['params'] == 'turn4':
            arduino.write(b'4')
            update_sensor_state_led2(False)
        else:
            print("INVALID params value")
    else:
        print("Unknown method:", data['method'])
        
def update_sensor_state_led1(state):
    dbConn = pymysql.connect(user='nguyen', password='123321', host='192.168.56.1', port=3306, database='data_sensor')
    cursor = dbConn.cursor()
    query = "UPDATE sensor_data SET bstate1 = %s WHERE id = 1"
    cursor.execute(query, (state,))
    dbConn.commit()
    
def update_sensor_state_led2(state):
    dbConn = pymysql.connect(user='nguyen', password='123321', host='192.168.56.1', port=3306, database='data_sensor')
    cursor = dbConn.cursor()
    query = "UPDATE sensor_data SET bstate2 = %s WHERE id = 1"
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
        if len(values) == 2:
            lights = int(values[0])
            moist = int(values[1])
            print(lights)
            print(moist)
            dbConn = pymysql.connect(user='nguyen', password='123321', host='192.168.56.1', port=3306, database='data_sensor')
            cursor = dbConn.cursor()
            query = "UPDATE sensor_data SET lights = %s, moisture = %s WHERE id = 1"
            cursor.execute(query, (lights, moist))
            dbConn.commit()
            sensor_data = {'lights': lights, 'moisture': moist}
            client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

except KeyboardInterrupt:
    pass
    
client.loop_stop()
client.disconnect()
