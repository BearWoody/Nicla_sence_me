#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

// Senzory
Sensor temp(SENSOR_ID_TEMP);
Sensor hum(SENSOR_ID_HUM);
Sensor baro(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ accel(SENSOR_ID_ACC);

// Datový paket (32 bytů)
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

// --- PŘIDÁVÁME RING BUFFER (Kruhová fronta) ---
const int BUFFER_SIZE = 50; // Kapacita na 5 sekund výpadku
SensorData dataBuffer[BUFFER_SIZE];
int head = 0;   // Ukazatel pro zápis
int tail = 0;   // Ukazatel pro čtení
int count = 0;  // Aktuální počet zpráv ve frontě

// BLE nastavení
BLEService mySensorService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataChar("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, sizeof(SensorData));

// Časování
unsigned long previousMillis = 0;          
const unsigned long interval = 100; // 10 Hz

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

  BLE.setConnectionInterval(12, 24); 

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

  // 1. ZÁPIS DO FRONTY 
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis; 

    if (count < BUFFER_SIZE) {
      dataBuffer[head].timestamp = currentMillis; 
      dataBuffer[head].temp = temp.value();
      dataBuffer[head].hum = hum.value();
      dataBuffer[head].press = baro.value();
      dataBuffer[head].gas = gas.value();
      dataBuffer[head].accX = accel.x();
      dataBuffer[head].accY = accel.y();
      dataBuffer[head].accZ = accel.z();
      
      head = (head + 1) % BUFFER_SIZE;
      count++;
    }
  }

  // 2. ODESÍLÁNÍ Z FRONTY 
  if (BLE.connected() && count > 0) {
    if (dataChar.writeValue((byte*)&dataBuffer[tail], sizeof(SensorData))) {
      tail = (tail + 1) % BUFFER_SIZE;
      count--;
      
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
