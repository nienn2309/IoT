
#define lightSensorPin A1
#define soilSensorPower 7
#define soilSensorPin A0

void setup() {
    pinMode(3,OUTPUT);
    pinMode(2,OUTPUT);
    pinMode(soilSensorPower, OUTPUT);
    digitalWrite(soilSensorPower, LOW);
    Serial.begin(9600);
}

void loop() {
    int lightValue = analogRead(lightSensorPin);
    Serial.print(lightValue);
    Serial.print(";");
    int moisture = readSoilSensor();
    Serial.print(moisture); 
    Serial.println();
    if (Serial.available()>0)
   {
      int value = Serial.read();
      if (value == '1')
      {
        digitalWrite(2,HIGH);
      }
      else if (value == '2')
      {
        digitalWrite(2,LOW);
      }
      else if (value == '3')
      {
        digitalWrite(3,HIGH);
      }
      else if (value == '4')
      {
        digitalWrite(3,LOW);
      }
   }
    delay(1000);
}

int readSoilSensor() {
    digitalWrite(soilSensorPower, HIGH);
    delay(10);
    int val = analogRead(soilSensorPin);
    digitalWrite(soilSensorPower, LOW);
    return val;
}
