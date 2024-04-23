#include "DHT.h"

#define DHT11Pin 3
#define DHTType DHT11
DHT HT(DHT11Pin, DHTType);

float humi;
float tempC;
const int Water = A0;
int WaterValue = 0;

const int ledPin = 2;
bool ledState = LOW;
unsigned long previousMillis = 0;
const long interval = 5000;

void setup() {
  pinMode(DHT11Pin, INPUT);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  HT.begin();
  delay(1000);
}

void loop() {
  delay(1000);
  humi = HT.readHumidity();
  tempC = HT.readTemperature();

  WaterValue = analogRead(Water);
  Serial.print(WaterValue);
  Serial.print(";");
  Serial.print(humi);
  Serial.print(";");
  Serial.print(tempC);
  Serial.println();

  int value = Serial.parseInt();
  if (value == 1) {
    digitalWrite(ledPin, HIGH);
    previousMillis = millis();
    ledState = HIGH;
  } else if (value == 2) {
    digitalWrite(ledPin, HIGH);
    delay(5000);
    digitalWrite(ledPin, LOW);
    delay(500);
    digitalWrite(ledPin, HIGH);
    delay(5000);
    digitalWrite(ledPin, LOW);
    ledState = LOW;
  }

  // Check if it's time to turn off the LED
  if (ledState == HIGH && millis() - previousMillis >= interval) {
    digitalWrite(ledPin, LOW);
    ledState = LOW;
  }
}
