import asyncio
import socketio
import serial
import numpy as np

from romi_controller import RomiMotorController

SERVER_URL = "http://192.168.1.220:4000"
PORT ="/dev/ttyACM0"
BAUDRATE = 19200


motorController = RomiMotorController()
sio = socketio.AsyncClient()


@sio.on("motor")
async def on_motor(data):
    print("Received on_motor:", data)
    motorController.set_motors(int(data["left"]), int(data["right"]))

async def read_arduino():
    ser = serial.Serial(PORT, BAUDRATE)
    while True:
        try:
            val = ser.readline().decode("UTF-8").strip("\r\n")
            vals = val.split(",")
            vals = np.array([int(v) for v in vals if v])
            print(vals)
        except Exception as e:
            print(e)
            continue

async def main():
    await sio.connect(SERVER_URL)
    print("Socket IO SID:", sio.sid)
    await sio.emit("registerForMotorControl")
    sio.start_background_task(read_arduino)
    await sio.wait()

async def close():
    await asyncio.sleep(0.1)

def run_loop():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
                main()
        )
    except KeyboardInterrupt as e:
        print("Keyboard interrupt")
    finally:
        print("Cleaning up")
        loop.run_until_complete(
                close()
        )
        print("Exiting")

if __name__ == "__main__":
    run_loop()
