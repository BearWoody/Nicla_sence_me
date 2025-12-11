import asyncio
import struct
import csv
import datetime
from bleak import BleakScanner, BleakClient

# KONFIGURACE 
DEVICE_NAME = "Nicla Sense ME"

UUID_TEMP = "19B10001-E8F2-537E-4F6C-D104768A1214"
UUID_HUM = "19B10002-E8F2-537E-4F6C-D104768A1214"
UUID_PRES = "19B10003-E8F2-537E-4F6C-D104768A1214"
UUID_GAS = "19B10004-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_X = "19B10005-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_Y = "19B10006-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_Z = "19B10007-E8F2-537E-4F6C-D104768A1214"

current_data = {
    "temp": 0.0, "hum": 0.0, "press": 0.0, "gas": 0.0,
    "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0
}

# CSV Logování
csv_filename = "nicla_data_log.csv"


def decode_float(data):
    return struct.unpack('<f', data)[0]


def callback_temp(sender, data):
    current_data["temp"] = decode_float(data)


def callback_hum(sender, data):
    current_data["hum"] = decode_float(data)


def callback_press(sender, data):
    current_data["press"] = decode_float(data)


def callback_gas(sender, data):
    current_data["gas"] = decode_float(data)


def callback_acc_x(sender, data):
    current_data["acc_x"] = decode_float(data)


def callback_acc_y(sender, data):
    current_data["acc_y"] = decode_float(data)


def callback_acc_z(sender, data):
    current_data["acc_z"] = decode_float(data)


async def main():
    print(f"Hledám zařízení '{DEVICE_NAME}'...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)

    if not device:
        print(f"Zařízení '{DEVICE_NAME}' nebylo nalezeno. Je zapnuté?")
        return

    print(f"Nalezeno: {device.address}. Připojuji se...")

    async with BleakClient(device) as client:
        print("Připojeno! Aktivuji notifikace...")

        await client.start_notify(UUID_TEMP, callback_temp)
        await client.start_notify(UUID_HUM, callback_hum)
        await client.start_notify(UUID_PRES, callback_press)
        await client.start_notify(UUID_GAS, callback_gas)
        await client.start_notify(UUID_ACC_X, callback_acc_x)
        await client.start_notify(UUID_ACC_Y, callback_acc_y)
        await client.start_notify(UUID_ACC_Z, callback_acc_z)

        # Otevření CSV souboru pro zápis
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Teplota", "Vlhkost", "Tlak", "Plyn_Ohm", "Acc_X", "Acc_Y", "Acc_Z"])

            print(f"Logování zahájeno do souboru: {csv_filename}")
            print("Stiskni Ctrl+C pro ukončení.")
            print("-" * 60)

            try:
                while True:
                    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    writer.writerow([
                        now,
                        f"{current_data['temp']:.2f}",
                        f"{current_data['hum']:.2f}",
                        f"{current_data['press']:.1f}",
                        f"{current_data['gas']:.0f}",
                        f"{current_data['acc_x']:.2f}",
                        f"{current_data['acc_y']:.2f}",
                        f"{current_data['acc_z']:.2f}"
                    ])
                    file.flush()  # Vynutit zápis na disk
                    print(f"\r[{now}] T:{current_data['temp']:5.1f}°C | "
                          f"H:{current_data['hum']:4.1f}% | "
                          f"P:{current_data['press']:6.0f}hPa | "
                          f"Acc: {current_data['acc_x']:5.2f} {current_data['acc_y']:5.2f} {current_data['acc_z']:5.2f}",
                          end="")

                    # synchronizace s Arduinem 10Hz
                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                print("\nUkončování...")
                await client.stop_notify(UUID_TEMP)
                print("Odpojeno. Data uložena.")


if __name__ == "__main__":
    asyncio.run(main())
