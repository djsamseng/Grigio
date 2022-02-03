import time
import math
from openal import oalOpen, oalQuit
import pyaudio
import wave

def oalTest():
    source = oalOpen("./sam.wav")
    source.set_looping(True)
    source.play()
    
    t = 0
    while True:
        x_pos = 5 * math.sin(math.radians(t))
        source.set_position([0, 0, x_pos])
        print("Playing at:", source.position)
        time.sleep(0.1)
        t += 5
    oalQuit()

def record10():
    p = pyaudio.PyAudio()
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 10
    WAVE_OUTPUT = "./tenseconds.wav"
    stream = p.open(format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK)

    frames = []
    print("Recording")
    for i in range(int(RATE/CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


def main():
    record10()

if __name__ == "__main__":
    main()