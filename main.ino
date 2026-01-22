#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

// 1. Definice senzorů 
Sensor temp(SENSOR_ID_TEMP);
Sensor hum(SENSOR_ID_HUM);
Sensor baro(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ accel(SENSOR_ID_ACC);

// 2. Nastavení Bluetooth 
BLEService mySensorService("19B10000-E8F2-537E-4F6C-D104768A1214");

// Charakteristiky
BLEFloatCharacteristic tempChar("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic humChar("19B10002-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic pressChar("19B10003-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic gasChar("19B10004-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic accXChar("19B10005-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic accYChar("19B10006-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);
BLEFloatCharacteristic accZChar("19B10007-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify);

// 3. Proměnné pro časování (Non-blocking)
unsigned long lastUpdate = 0;        
const int interval = 100;            

unsigned long ledTurnOffTime = 0;   
bool isLedOn = false;                
const int ledDuration = 10;          

void setup() {
  Serial.begin(115200);
  
  // Start senzorů
  BHY2.begin();
  temp.begin();
  hum.begin();
  baro.begin();
  gas.begin();
  accel.begin();

  if (!BLE.begin()) {
    Serial.println("CHYBA: Bluetooth start failed!");
    while (1);
  }

  BLE.setLocalName("Nicla Sense ME");
  BLE.setAdvertisedService(mySensorService);
  
  mySensorService.addCharacteristic(tempChar);
  mySensorService.addCharacteristic(humChar);
  mySensorService.addCharacteristic(pressChar);
  mySensorService.addCharacteristic(gasChar);
  mySensorService.addCharacteristic(accXChar);
  mySensorService.addCharacteristic(accYChar);
  mySensorService.addCharacteristic(accZChar);

  BLE.addService(mySensorService);
  BLE.advertise();

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); 
  
  Serial.println("System bezi (Non-blocking). Cekam na pripojeni...");
}

void loop() {
  // A. Aktualizace systémů
  BLE.poll();
  BHY2.update();
  unsigned long currentMillis = millis();

  // B. Odesílání dat (10 Hz)
  if (currentMillis - lastUpdate >= interval) {
    lastUpdate = currentMillis;

    if (BLE.connected()) {
      // 1. Načtení hodnot
      float t = temp.value();
      float h = hum.value();
      float p = baro.value();
      float g = gas.value();
      float ax = accel.x();
      float ay = accel.y();
      float az = accel.z();

      // 2. Odeslání
      tempChar.writeValue(t);
      humChar.writeValue(h);
      pressChar.writeValue(p);
      gasChar.writeValue(g);
      accXChar.writeValue(ax);
      accYChar.writeValue(ay);
      accZChar.writeValue(az);
      
      // 3. Rozsvícení LED
      digitalWrite(LED_BUILTIN, HIGH);
      isLedOn = true;
      ledTurnOffTime = currentMillis + ledDuration; 
    }
  }

  if (isLedOn && currentMillis >= ledTurnOffTime) {
    digitalWrite(LED_BUILTIN, LOW);
    isLedOn = false;
  }
}
