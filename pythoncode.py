import serial
import time
import re
import pymysql
from threading import Thread
from flask import Flask, render_template

app = Flask(__name__)

pins = {
    3: {'name': 'LED', 'state': 0},
    4: {'name': 'Relay', 'state': 0}
}

dht = {
    2: {'name': 'DHT', 'TempC': 0, 'Humidity': 0, 'Light': 0}
}

mode = 0

ser = serial.Serial('/dev/ttyS2', 9600, timeout=1)

def read_sensor_data():
    global dht
    while True:
        data = ser.readline().decode('utf-8').strip()
        if data:
            humidity_match = re.search(r'Humidity:(\d+\.\d+)', data)
            temperature_match = re.search(r'Temperature:(\d+\.\d+)', data)
            light_match = re.search(r'Light:(\d+)', data)
            if humidity_match and temperature_match and light_match:
                humidity = float(humidity_match.group(1))
                temperature = float(temperature_match.group(1))
                light = float(light_match.group(1))
                dht[2]['TempC'] = temperature
                dht[2]['Humidity'] = humidity
                dht[2]['Light'] = light
                if mode == 1:
                    if dht[2]['Light'] > 500:
                        pins[3]['state'] = 1
                    else:
                        pins[3]['state'] = 0
                    if dht[2]['TempC'] > 30:
                        pins[4]['state'] = 1
                    else:
                        pins[4]['state'] = 0
                print("Temperature:", temperature, "°C, Humidity:", humidity, "%, Light", light)
                try:
                    dbConn = pymysql.connect("localhost", "ec2", "", "data_sensor")
                    cursor = dbConn.cursor()
                    cursor.execute("INSERT INTO logs (temperature, humidity, light, led_state, relay_state) VALUES (%s, %s, %s, %s, %s)",
                    (temperature, humidity, light, pins[3]['state'], pins[4]['state']))
                    dbConn.commit()
                    print("Data inserted successfully.")
                except pymysql.Error as e:
                    print("Error inserting data into the database:", e)
                finally:
                    dbConn.close()
            else:
                print("Data format error. Check Arduino output.")
        else:
            print("Sensor failure. Check wiring.")
        time.sleep(4)

@app.route("/")
def index():
    global dht
    try:
        dbConn = pymysql.connect("localhost", "ec2", "", "data_sensor")
        cursor = dbConn.cursor()
        cursor.execute("SELECT temperature, humidity, light, led_state, relay_state, timestamp FROM logs ORDER BY id DESC LIMIT 10")
        sensor_data = cursor.fetchall()
        dbConn.close()
    except pymysql.Error as e:
        print("Error fetching data from the database:", e)
        sensor_data = []
    Data = {'pins': pins, 'dht': dht, 'sensor_data': sensor_data, 'mode': mode}
    return render_template('index.html', **Data)
    
@app.route("/set_mode/<int:mode_value>")
def set_mode(mode_value):
    global mode
    mode = mode_value
    return "Mode set to " + str(mode)

@app.route("/<changePin>/<toggle>")
def toggle_function(changePin, toggle):
    changePin = int(changePin)
    if toggle == "on":
        if changePin == 3:
            ser.write(b"1")
            pins[changePin]['state'] = 1
    if toggle == "off":
        if changePin == 3:
            ser.write(b"2")
            pins[changePin]['state'] = 0
    if toggle == "on":
        if changePin == 4:
            ser.write(b"3")
            pins[changePin]['state'] = 1
    if toggle == "off":
        if changePin == 4:
            ser.write(b"4")
            pins[changePin]['state'] = 0
    try:
        dbConn = pymysql.connect("localhost", "ec2", "", "data_sensor")
        cursor = dbConn.cursor()
        cursor.execute("SELECT temperature, humidity, light, led_state, relay_state, timestamp FROM logs ORDER BY id DESC LIMIT 10")
        sensor_data = cursor.fetchall()
        dbConn.close()
    except pymysql.Error as e:
        print("Error fetching data from the database:", e)
        sensor_data = []
    Data = {'pins': pins, 'dht': dht, 'sensor_data': sensor_data, 'mode': mode}
    return render_template('index.html', **Data)

if __name__ == '__main__':
    sensor_thread = Thread(target=read_sensor_data)
    sensor_thread.daemon = True
    sensor_thread.start()
    app.run(host='0.0.0.0', port=80, debug=True)