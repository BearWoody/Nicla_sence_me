import asyncio
import struct
import csv
import datetime
import math
from bleak import BleakScanner, BleakClient

# KONFIGURACE
DEVICE_NAME = "Nicla Sense ME"

# UUIDs
UUID_TEMP = "19B10001-E8F2-537E-4F6C-D104768A1214"
UUID_HUM = "19B10002-E8F2-537E-4F6C-D104768A1214"
UUID_PRES = "19B10003-E8F2-537E-4F6C-D104768A1214"
UUID_GAS = "19B10004-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_X = "19B10005-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_Y = "19B10006-E8F2-537E-4F6C-D104768A1214"
UUID_ACC_Z = "19B10007-E8F2-537E-4F6C-D104768A1214"

# KALIBRACE JEDNOTEK
ACC_DIVISOR = 4096.0

current_data = {
    "temp": 0.0, "hum": 0.0, "press": 0.0, "gas": 0.0,
    "acc_x": 0.0, "acc_y": 0.0, "acc_z": 0.0
}

# CSV Logování
csv_filename = "nicla_data_final_fixed.csv"


def decode_float(data):
    return struct.unpack('<f', data)[0]


# --- Callbacky ---
def callback_temp(sender, data): current_data["temp"] = decode_float(data)


def callback_hum(sender, data): current_data["hum"] = decode_float(data)


def callback_press(sender, data): current_data["press"] = decode_float(data)


def callback_gas(sender, data): current_data["gas"] = decode_float(data)


def callback_acc_x(sender, data): current_data["acc_x"] = decode_float(data)


def callback_acc_y(sender, data): current_data["acc_y"] = decode_float(data)


def callback_acc_z(sender, data): current_data["acc_z"] = decode_float(data)


async def main():
    print(f"Hledám zařízení '{DEVICE_NAME}'...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)

    if not device:
        print(f"Zařízení '{DEVICE_NAME}' nebylo nalezeno.")
        return

    print(f"Nalezeno: {device.address}. Připojuji se...")

    async with BleakClient(device) as client:
        print("Připojeno! Data běží...")

        await client.start_notify(UUID_TEMP, callback_temp)
        await client.start_notify(UUID_HUM, callback_hum)
        await client.start_notify(UUID_PRES, callback_press)
        await client.start_notify(UUID_GAS, callback_gas)
        await client.start_notify(UUID_ACC_X, callback_acc_x)
        await client.start_notify(UUID_ACC_Y, callback_acc_y)
        await client.start_notify(UUID_ACC_Z, callback_acc_z)

        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = [
                "Timestamp", "Teplota", "Vlhkost", "Tlak", "Plyn",
                "AccX_g", "AccY_g", "AccZ_g",
                "Pitch_deg", "Roll_deg", "Total_G"
            ]
            writer.writerow(header)

            print("-" * 130)

            try:
                while True:
                    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    # Načtení RAW hodnot
                    raw_ax = current_data['acc_x']
                    raw_ay = current_data['acc_y']
                    raw_az = current_data['acc_z']

                    # PŘEPOČET NA REÁLNÉ G
                    ax_g = raw_ax / ACC_DIVISOR
                    ay_g = raw_ay / ACC_DIVISOR
                    az_g = raw_az / ACC_DIVISOR

                    try:
                        # Pitch / Roll
                        pitch = math.atan2(ay_g, math.sqrt(ax_g * ax_g + az_g * az_g)) * 180.0 / math.pi
                        roll = math.atan2(-ax_g, az_g) * 180.0 / math.pi

                        # Celkové přetížení
                        total_g = math.sqrt(ax_g ** 2 + ay_g ** 2 + az_g ** 2)
                    except Exception:
                        pitch, roll, total_g = 0.0, 0.0, 0.0

                    # Zápis do CSV
                    writer.writerow([
                        now,
                        f"{current_data['temp']:.2f}",
                        f"{current_data['hum']:.2f}",
                        f"{current_data['press']:.1f}",
                        f"{current_data['gas']:.0f}",
                        f"{ax_g:.3f}", f"{ay_g:.3f}", f"{az_g:.3f}",
                        f"{pitch:.1f}", f"{roll:.1f}", f"{total_g:.2f}"
                    ])
                    file.flush()

                    # FORMÁT VÝPISU
                    print(f"\r[{now}] "
                          f"Teplota: {current_data['temp']:4.1f}°C | "
                          f"Vlhkost:{current_data['hum']:4.1f}% | "
                          f"Tlak: {current_data['press']:6.0f}hPa | "
                          f"Náklon: {roll:5.1f}° | "
                          f"Sklon: {pitch:5.1f}° | "
                          f"Přetížení: {total_g:4.2f} g |",
                          end="")

                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                print("\nUkončování...")
                if client.is_connected:
                    await client.stop_notify(UUID_TEMP)
                print("Odpojeno.")


if __name__ == "__main__":
    asyncio.run(main())
