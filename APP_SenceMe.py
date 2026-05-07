import asyncio
import struct
import csv
import datetime
import math
from bleak import BleakScanner, BleakClient

# Konfigurace
DEVICE_NAME = "Nicla Sense ME"
UUID_DATA = "19B10001-E8F2-537E-4F6C-D104768A1214"
ACC_DIVISOR = 4096.0

# Nastavení doby měření
MEASUREMENT_HOURS = 0
MEASUREMENT_MINUTES = 10
MEASUREMENT_SECONDS = 0

TOTAL_MEASUREMENT_SEC = (MEASUREMENT_HOURS * 3600) + (MEASUREMENT_MINUTES * 60) + MEASUREMENT_SECONDS

data_queue = None


def callback_data(sender, data):
    try:
        unpacked = struct.unpack('<I7f', data)

        snapshot = {
            "arduino_ms": unpacked[0],
            "temp": unpacked[1],
            "hum": unpacked[2],
            "press": unpacked[3],
            "gas": unpacked[4],
            "acc_x": unpacked[5],
            "acc_y": unpacked[6],
            "acc_z": unpacked[7],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }

        if data_queue is not None:
            data_queue.put_nowait(snapshot)

    except Exception as e:
        print(f"Chyba při dekódování paketu: {e}")


async def main():
    global data_queue
    data_queue = asyncio.Queue()

    print(f"Hledám zařízení '{DEVICE_NAME}'...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)

    if not device:
        print(f"Zařízení '{DEVICE_NAME}' nebylo nalezeno.")
        return

    print(f"Nalezeno: {device.address}. Připojování...")

    async with BleakClient(device) as client:
        print("Připojeno")

        await client.start_notify(UUID_DATA, callback_data)

        start_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"nicla_data_{start_time_str}.csv"
        print(f"Zápis do souboru: {csv_filename}")

        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = [
                "Timestamp_PC", "Arduino_ms", "Teplota", "Vlhkost", "Tlak", "Plyn",
                "AccX_g", "AccY_g", "AccZ_g",
                "Pitch_deg", "Roll_deg", "Total_G"
            ]
            writer.writerow(header)

            print("-" * 130)

            start_datetime = datetime.datetime.now()

            try:
                while True:
                    now_time = datetime.datetime.now()
                    elapsed_sec = (now_time - start_datetime).total_seconds()
                    remaining_sec = int(TOTAL_MEASUREMENT_SEC - elapsed_sec)

                    rem_h = remaining_sec // 3600
                    rem_m = (remaining_sec % 3600) // 60
                    rem_s = remaining_sec % 60

                    if elapsed_sec >= TOTAL_MEASUREMENT_SEC:
                        print(f"\nKonec měření po {MEASUREMENT_HOURS}h {MEASUREMENT_MINUTES}m {MEASUREMENT_SECONDS}s.")
                        break

                    snapshot = await data_queue.get()

                    now_full = snapshot["timestamp"]
                    now_console = now_full.split(" ")[1][:-3]

                    raw_ax = snapshot['acc_x']
                    raw_ay = snapshot['acc_y']
                    raw_az = snapshot['acc_z']

                    ax_g = raw_ax / ACC_DIVISOR
                    ay_g = raw_ay / ACC_DIVISOR
                    az_g = raw_az / ACC_DIVISOR

                    try:
                        pitch = math.atan2(ay_g, math.sqrt(ax_g * ax_g + az_g * az_g)) * 180.0 / math.pi
                        roll = math.atan2(-ax_g, az_g) * 180.0 / math.pi
                        total_g = math.sqrt(ax_g ** 2 + ay_g ** 2 + az_g ** 2)
                    except Exception:
                        pitch, roll, total_g = 0.0, 0.0, 0.0

                    writer.writerow([
                        now_full,
                        snapshot['arduino_ms'],
                        f"{snapshot['temp']:.2f}",
                        f"{snapshot['hum']:.2f}",
                        f"{snapshot['press']:.1f}",
                        f"{snapshot['gas']:.0f}",
                        f"{ax_g:.3f}", f"{ay_g:.3f}", f"{az_g:.3f}",
                        f"{pitch:.1f}", f"{roll:.1f}", f"{total_g:.2f}"
                    ])
                    file.flush()

                    print(f"\r[{now_console} | Zbývá: {rem_h:02d}:{rem_m:02d}:{rem_s:02d} | Nicla: {snapshot['arduino_ms']} ms] "
                          f"Teplota: {snapshot['temp']:4.1f}°C | "
                          f"Vlhkost:{snapshot['hum']:4.1f}% | "
                          f"Tlak: {snapshot['press']:6.0f}hPa | "
                          f"Náklon: {roll:5.1f}° | "
                          f"Sklon: {pitch:5.1f}° | "
                          f"Přetížení: {total_g:4.2f} g |",
                          end="")

            except KeyboardInterrupt:
                print("\nUkončování...")
                if client.is_connected:
                    await client.stop_notify(UUID_DATA)
                print("Odpojeno.")


if __name__ == "__main__":
    asyncio.run(main())
