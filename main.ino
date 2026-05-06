#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

// 1. Definice senzorů
Sensor temp(SENSOR_ID_TEMP);
Sensor hum(SENSOR_ID_HUM);
Sensor baro(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ accel(SENSOR_ID_ACC);

// 2. Definice datového balíčku
struct SensorData {
  uint32_t timestamp; 
  float temp;        
  float hum;          
  float press;        
  float gas;          
  float accX;         
  float accY;         
  float accZ;         
}; 

SensorData currentData; 

// 3. Nastavení Bluetooth
BLEService mySensorService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataChar("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, sizeof(SensorData));

// 4. Proměnné pro časování
unsigned long previousMillis = 0;          
const unsigned long interval = 100; 

unsigned long ledTurnOnTime = 0;           
const unsigned long ledDuration = 10;      
bool isLedOn = false;                      

void setup() {
  Serial.begin(115200);
  
  BHY2.begin();
  temp.begin();
  hum.begin();
  baro.begin();
  gas.begin();
  accel.begin();

  if (!BLE.begin()) {
    Serial.println("Error: Bluetooth start failed!");
    while (1); 
  }

  BLE.setLocalName("Nicla Sense ME");
  BLE.setAdvertisedService(mySensorService);
  mySensorService.addCharacteristic(dataChar);

  BLE.addService(mySensorService);
  BLE.advertise();

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.println("Cekam na pripojeni...");
}

void loop() {
  BLE.poll();
  BHY2.update();

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis; 

    if (BLE.connected()) {
      currentData.timestamp = currentMillis; 
      currentData.temp = temp.value();
      currentData.hum = hum.value();
      currentData.press = baro.value();
      currentData.gas = gas.value();
      currentData.accX = accel.x();
      currentData.accY = accel.y();
      currentData.accZ = accel.z();
      
      // 2. Odešleme celý 32bytový struct
      dataChar.writeValue((byte*)&currentData, sizeof(SensorData));
      
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
