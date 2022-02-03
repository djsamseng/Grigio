import asyncio
import numpy as np
import pyaudio
import time
import serial
import socketio

sio = socketio.AsyncClient()


PORT ="/dev/ttyACM0"
BAUDRATE = 19200



def process_arduino_audio(data):
    try:
        vals_per_t = data.rstrip("-").split("-")
        num_intervals = len(vals_per_t)
        num_channels = len(vals_per_t[0].split(","))
        audio_per_channel = np.zeros((num_intervals, num_channels), dtype=np.float32)
        for i in range(len(vals_per_t)):
            vals = vals_per_t[i].split(",")
            audio_per_channel[i,:] = np.array([int(v) for v in vals if v])
        audio_per_channel /= 1024.
        print("===========")
        print(audio_per_channel.shape)
        return audio_per_channel
    except Exception as e:
        print(e)

async def read_arduino():
    ser = serial.Serial(PORT, BAUDRATE)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
        channels=1,
        rate=1000,
        output=True)
    while True:
        await sio.sleep(0.001)
        try:
            t0 = time.time()
            val = ser.readline().decode("UTF-8").strip("\r\n")
            
            audio_per_channel = process_arduino_audio(val)
            if audio_per_channel is not None:
                print(audio_per_channel[:, 0])
                audio_play = audio_per_channel[:,0].tostring()
                stream.write(audio_play, 99)
            t1 = time.time()
            print("took:", t1-t0)
            #await sio.emit("audiodata", val)
        except Exception as e:
            print(e)
            continue

async def main():
    await read_arduino()

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