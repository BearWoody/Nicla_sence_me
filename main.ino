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

// 3. Proměnné pro Non-blocking časování
unsigned long previousMillis = 0;          // Čas posledního odeslání dat
const unsigned long interval = 100;        // Interval odesílání v ms

unsigned long ledTurnOnTime = 0;           // Čas kdy se LED rozsvítila
const unsigned long ledDuration = 10;      // Doba po kterou má LED svítit (v ms)
bool isLedOn = false;                      // Aktuální stav LED 

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
    Serial.println("Error: Bluetooth start failed!");
    while (1); // Pokud se BLE nespustí, zastavíme program
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
  
  Serial.println("Cekam na pripojeni...");
}

void loop() {
  BLE.poll();
  BHY2.update();

  // Získání aktuálního času (pouze jednou za cyklus pro zajištění synchronizace)
  unsigned long currentMillis = millis();

  // B. Blok odesílání dat (proběhne přesně každých 100 ms)
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis; 

    if (BLE.connected()) {
      // Odeslání hodnot přímo z bufferu senzoru 
      tempChar.writeValue(temp.value());
      humChar.writeValue(hum.value());
      pressChar.writeValue(baro.value());
      gasChar.writeValue(gas.value());
      accXChar.writeValue(accel.x());
      accYChar.writeValue(accel.y());
      accZChar.writeValue(accel.z());
      
      // Spuštění indikátoru přenosu
      if (!isLedOn) {
        digitalWrite(LED_BUILTIN, HIGH);
        isLedOn = true;
        ledTurnOnTime = currentMillis; 
      }
    }
  }

  if (isLedOn && (currentMillis - ledTurnOnTime >= ledDuration)) {
    digitalWrite(LED_BUILTIN, LOW);
    isLedOn = false;
  }
}
