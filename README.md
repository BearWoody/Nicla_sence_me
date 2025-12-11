# Nicla_sence_me
BOSCH sencors and bluetooth sharing

Testování komunikačních možností senzoru Nicla Sense ME a vývoj aplikace pro zpracování senzorových dat

Autor: Vojtěch Jiříkovský

Obor: Informatika a kybernetika ve zdravotnictví

Předmět/Projekt: Projekt I

Anotace projektu
Cílem této práce je ověření schopností desky Arduino Nicla Sense ME, která integruje senzorový systém Bosch (BHI260AP, BMM150, BMP390 a BME688).

Projekt se zaměřuje na:
1.	Implementaci výpočtu environmentálních dat (teplota, tlak, vlhkost, plyn).
2.	Zprovoznění bezdrátové komunikace přes Bluetooth Low Energy (BLE).
3.	Experimentální ověření stability přenosu při frekvenci vzorkování 10 Hz.
4.	Vytvoření prototypu aplikace pro vizualizaci dat.
   
Technická specifikace
•	Hardware: Arduino Nicla Sense ME (Cortex-M4 nRF52832)
•	Senzory:
o	BMP390 (Tlak)
o	BME688 (Teplota, Vlhkost, Plyny/VOC)
•	Komunikační protokol: Bluetooth Low Energy (GATT Server)
•	Cílová frekvence přenosu: 10 Hz (interval 100 ms)

Návod k použití (Prototyp)
1. Příprava hardwaru
•	Nahrát přiložený firmware (.ino soubor) do desky Nicla Sense ME pomocí Arduino IDE 2.x.
•	Po nahrání se rozbliká LED dioda, indikující vysílání (Advertising).
2. Připojení klientské aplikace
   
Jako referenční aplikace pro sběr dat je použit software nRF Connect nebo Bluetooth LE Explorer.
1.	Spusťte BLE skener na přijímacím zařízení (PC/Mobil).
2.	Vyhledejte zařízení s názvem Nicla Sense ME.
3.	Připojte se a povolte notifikace u služby s UUID 19B10000....
4.	Data (Teplota, Tlak, Vlhkost, CO2 ekvivalent) jsou aktualizována každých 100 ms.
   
Metodika ověření 10 Hz
Pro splnění zadání (ověření rychlosti) byl v kódu nastaven interval na 100 ms.
•	Ověření: Sledováním časových značek (timestamps) příchozích paketů v klientské aplikaci.
•	Stabilita: Indikována pravidelným blikáním LED diody na desce synchronně s odesláním dat.

Struktura dat (BLE GATT)
Zařízení vystavuje jednu primární službu se čtyřmi charakteristikami typu Float (32-bit):
•	UUID ...0001: Teplota [°C]
•	UUID ...0002: Vlhkost [%]
•	UUID ...0003: Tlak [hPa]
•	UUID ...0004: Odhad CO2 [ppm]
________________________________________
Vypracováno v rámci studia na oboru Informatika a kybernetika ve zdravotnictví.

