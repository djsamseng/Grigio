import asyncio
import multiprocessing
import socketio

import connection_managers
import joystick_managers

import cv2
import base64

import av
from aiortc import RTCPeerConnection,\
    RTCSessionDescription,\
    VideoStreamTrack,\
    RTCIceCandidate,\
    RTCIceGatherer,\
    RTCIceServer,\
    sdp,\
    MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import object_to_string, object_from_string

import matplotlib.pyplot as plt
from numba import cuda
import numpy as np
import os
import time

import pyaudio
from scipy.io import wavfile

import multiprocessing
from inputs import get_gamepad

sio = socketio.AsyncClient()

## GLOBALS
pc = None
isInitiator = False
player = None
p_stream = None
audio_replay_track = None
resampler = None

class AudioReplayTrack(MediaStreamTrack):
    kind = "audio"
    def __init__(self):
        super().__init__()
        self.dataQueue = asyncio.Queue()
        self.itr = 0
        self.is_playing = False
        self.wavedata = np.array([])
        self.rate = 44100
        self.waveitr = 0

    async def recv(self):
        try:
            data_old = await self.dataQueue.get()
            
            if True:
                data = self.readWave()
                end = min(self.waveitr + 1280, data.shape[0])
                inc = end - self.waveitr
                layout = 'stereo'
                audio_array = np.zeros((1, 1280), dtype='int16')
                if layout == 'stereo':
                    audio_array = np.zeros((1, 1280 * 2), dtype='int16')
                if self.is_playing:
                    if layout == 'stereo':
                        audio_array[0,:inc*2:2] = data[self.waveitr:self.waveitr+inc, 0]
                        audio_array[0,1:inc*2:2] = data[self.waveitr:self.waveitr+inc, 1]
                    else:
                        audio_array[0,:inc] = data[self.waveitr:self.waveitr+inc, 0]
                    print(self.waveitr, ":", self.waveitr+inc)
                    print(data.shape)
                self.waveitr += inc
                frame = av.AudioFrame.from_ndarray(audio_array, 's16', layout=layout)
                frame.sample_rate = self.rate
                frame.time_base = '1/' + str(self.rate)
                frame.pts = self.itr
                self.itr += 960 * 2 # TODO: Correctly increment base
                return frame
            
            audio_array = np.zeros((1, 1920), dtype='int16')
            audio_array[:,:] = data["data"][:,:]
            frame = av.AudioFrame.from_ndarray(audio_array, 's16')
            frame.sample_rate = 48000
            frame.time_base = '1/48000'
            frame.pts = data["pts"]
            self.itr += 960 # TODO: Correctly increment base
            return frame
        except Exception as e:
            print("AudioReplayTrack recv was called with Exception:", e)

    def addFrame(self, frame):
        self.dataQueue.put_nowait(frame)

    def openWave(self, filename):
        self.is_playing = True
        self.waveitr = 0
        (self.rate, self.wavedata) = wavfile.read(filename)
        if len(self.wavedata.shape) == 1:
            print("Converting to stereo")
            self.wavedata = np.repeat(
                self.wavedata.reshape(-1, 1),
                2,
                axis=1
            )
        print("RATE:", self.rate)

    def readWave(self):
        size = 1920
        if self.waveitr >= self.wavedata.shape[0]:
            self.is_playing = False
        return self.wavedata

    def stop(self):
        try:
            super().stop()
            print("AudioReplayTrack stop was called")
        except Exception as e:
            print("AudioReplayTrack stop was called with exception:", e)


async def sendMessage(msg):
    await sio.emit("message", msg)

@sio.event
async def message(data):
    print("Received message")

@sio.on("offer")
async def on_offer(data):
    print("GOT OFFER:", data)
    try:
        obj = object_from_string(data)
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
    except Exception as e:
        print("Could not decompose offer into session description directly")
        await pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=data["sdp"], type=data["type"]
            )
        )
    
    await addTracks()
    localDesc = await pc.createAnswer()
    print("CREATED LOCAL DESC:", localDesc)
    await pc.setLocalDescription(localDesc)
    print("SENDING MESSAGE: on_offer", localDesc.type)
    await sio.emit("answer", object_to_string(pc.localDescription))

didGetAnswer = False
@sio.on("answer")
async def on_answer(data):
    global didGetAnswer
    if didGetAnswer:
        return
    didGetAnswer = True
    print("GOT ANSWER:", data)
    try:
        obj = object_from_string(data)
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
    except Exception as e:
        print("Could not decompose answer into session description directly")
        await pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=data["sdp"], type=data["type"]
            )
        )

@sio.on("candidate")
async def on_candidate(data):
    print("Got candidate NEW:", data)
    can = sdp.candidate_from_sdp(data["candidate"])
    can.sdpMid = data["id"]
    can.sdMLineIndex = data["label"]
    await pc.addIceCandidate(can)

@sio.on("message")
async def on_message(data):
    print("Received on_message", data)

def add_player(pc, player):
    if player.audio:
        print("Adding audio")
        pc.addTrack(player.audio)
    if player.video:
        print("Adding video")
        pc.addTrack(player.video)

async def createPeerConnection():
    global pc
    global resampler
    p = pyaudio.PyAudio()
    p_stream = None
    resampler = av.audio.resampler.AudioResampler(
        layout="mono",
        rate=16000)
    if pc:
        raise Exception("RTCPeerConnection alread established")

    pc = RTCPeerConnection()
    print("Created RTCPeerConnection")
    @pc.on("track")
    async def on_track(track):
        global p_stream
        print("Received track:", track.kind)
        if track.kind == "audio":
            while True:
                try:
                    frame = await track.recv()

                    if not p_stream:
                        assert frame.format.bits == 16
                        assert frame.sample_rate == 48000
                        assert frame.layout.name == "stereo"
                        p_stream = p.open(format=pyaudio.paInt16,
                            channels=2,
                            rate=48000,
                            output=True)

                    do_transcribe = False
                    if do_transcribe:
                        resampled = resampler.resample(frame)
                        resampled_np = resampled.to_ndarray()
                        f32_ar = resampled_np.astype(np.float32, order='C') / 32768.0
                        #print("Resampled:", f32_ar)
                        audio_array = f32_ar[0]
                        #voiceToText.receive_audio_array(audio_array)
                        ### CONTINUE
                        continue


                    as_np = frame.to_ndarray()
                    audio_replay_track.addFrame({
                        "data": as_np,
                        "pts": frame.pts
                    })

                    ## Resample


                    as_np = as_np.astype(np.int16).tostring()
                    p_stream.write(as_np)

                except Exception as e:
                    print("Error receiving audio:", e)
                    raise e

        if track.kind == "video":
            while True:
                try:
                    frame = await track.recv()
                    img = frame.to_rgb().to_ndarray()
                    #print("Got frame", img)
                    cv2.imshow("test", img)
                    cv2.waitKey(5)
                except Exception as e:
                    print("Error receiving track", e)
                    raise e

    @pc.on("connectionstatechange")
    def on_connectionstatechange():
        print("connectionstatechange:", pc.connectionState)

async def addTracks():
    global player
    global audio_replay_track
    if player:
        if player.video:
            player.video.stop()
        if player.audio:
            player.audio.stop()
    
    SEND_ONLY = True
    if SEND_ONLY:
        #transceiver = pc.addTransceiver("video", direction="recvonly")
        
        audio_replay_track = AudioReplayTrack()
        pc.addTrack(audio_replay_track)

        return

    player = MediaPlayer('/dev/video0', format='alsa', options={
        'video_size': '640x360'
    })
    add_player(pc, player)

    #audio_replay_track = AudioReplayTrack()
    #pc.addTrack(audio_replay_track)

    print("Created peer")

async def createOffer():
    if not isInitiator:
        return
        # raise Exception("Should createOffer only when the initiator")

    await addTracks()
    print("isInitiator: creating offer")
    desc = await pc.createOffer()
    print("Created local description")
    await pc.setLocalDescription(desc)
    print("SENDING MESSAGE: createOffer", desc)
    await sio.emit("offer", object_to_string(pc.localDescription))

async def cleanup():
    global pc
    await pc.close()
    pc = None

@sio.on("created")
async def on_created(data, *args):
    global isInitiator
    print("Received on_created", data, args)
    isInitiator = True

@sio.on("isinitiator")
async def on_isinitiator(room):
    global isInitiator
    global pc
    print("Received isInitiator", room)
    isInitiator = True
    await cleanup()
    await createPeerConnection()

@sio.on("full")
async def on_full(data):
    print("Received on_full", data)

@sio.on("join")
async def on_join(data):
    print("Received on_join", data)

@sio.on("joined")
async def on_joined(room, socket_id):
    print("Received on_joined", room, socket_id)

@sio.on("ready")
async def on_ready():
    print("Received ready")
    await createOffer()

@sio.on("log")
async def on_log(data):
    print("Received on_log", data)

num = 0
@sio.on("frame")
async def on_frame(data):
    global num
    data = base64.b64decode(data)
    data = np.frombuffer(data, dtype=np.uint8)
    data = cv2.imdecode(data, flags=cv2.IMREAD_COLOR)
    print("Got frame:", num)
    num += 1
    cv2.imshow("frame", data)
    cv2.waitKey(5)

def configure_graph():
    x_len = 1024 * 1
    fig, (ax1, ax2) = plt.subplots(2, figsize=(15, 10))
    x = np.arange(0, x_len)
    line, = ax1.plot(x, np.random.rand(x_len), '-', lw=2)
    line2, = ax2.plot(x, np.random.rand(x_len), '-', lw=2)
    y_range = 500
    ax1.set_title("Left Audio Waveform")
    ax1.set_xlabel('samples')
    ax1.set_ylabel('volume')
    ax1.set_ylim(-y_range, y_range)
    ax1.set_xlim(0, x_len)
    y_ticks = np.arange(0, y_range, 1000)
    plt.setp(ax1, xticks=[0, x_len, x_len], yticks=y_ticks)

    ax2.set_title("Right Audio Waveform")
    ax2.set_xlabel('samples')
    ax2.set_ylabel('volume')
    ax2.set_ylim(-y_range, y_range)
    ax2.set_xlim(0, x_len)
    plt.setp(ax2, xticks=[0, x_len, x_len], yticks=y_ticks)

    fig.show()

    return (x_len, fig, line, line2)

do_graph = True
if do_graph:
    (x_len, fig, line, line2) = configure_graph()
    itr = 0
    to_graph = np.zeros(x_len)

@sio.on("audiodata")
async def on_audio_data(data):
    global itr
    global to_graph
    try:
        vals = data.split(",")
        vals = np.array([int(v) for v in vals if v])
        if do_graph:
            if itr + len(vals) >= to_graph.shape[0]:
                itr = 0
            to_graph[itr:itr + len(vals)] = vals[:]
            itr += len(vals)
            line.set_ydata(to_graph)
            fig.canvas.draw()
            fig.canvas.flush_events()
    except Exception as e:
        print(e)

@sio.on("braincontrol")
async def on_brain_control(data):
    print("BRAIN:", data)
    if "speak" in data:
        print("SPEAK:", data["speak"])
        text = data["speak"].lower()
        filename = "./wav/" + text + ".wav"
        if os.path.exists(filename):
            audio_replay_track.openWave(filename)
        else:
            print("Cannot speak: no file")

throttle = 255//2
joystick_right = 1020/2
joystick_down = 1020/2
def get_joystick_data():
    global throttle
    global joystick_right
    global joystick_down

    events = get_gamepad()
    THROTTLE = "ABS_Z" # Forward is 0, toward me is 255
    JOYSTICK_RIGHT = "ABS_X" # Right is 1020, Left is 0
    JOYSTICK_DOWN = "ABS_Y" # Towards me is 1020, Forward is 0
    for evt in events:
        if evt.code == THROTTLE:
            throttle = 255//2 - evt.state
        elif evt.code == JOYSTICK_RIGHT:
            joystick_right = evt.state
        elif evt.code == JOYSTICK_DOWN:
            joystick_down = evt.state
    
    left_motor = 0
    right_motor = 0
    right_motor = throttle + int(throttle * (1020/2 - joystick_right) / 1020)
    left_motor = throttle + int(throttle * (joystick_right - 1020/2) / 1020)
    data = {
        "left": left_motor,
        "right": right_motor,
    }
    return data

def joystick_timeout(signum, frame):
    raise Exception("Joystick timeout")

def get_joystick_p2(joystick_queue):
    while True:
        joystick_data = get_joystick_data()
        joystick_queue.put(joystick_data)

async def watch_joystick_process():
    joystick_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=get_joystick_p2, args=(joystick_queue,))
    p.start()
    while True:
        await sio.sleep(0.001)
        joystick_data = None
        while not joystick_queue.empty():
            joystick_data = joystick_queue.get_nowait()
        if joystick_data is not None:
            await sio.emit("motor", joystick_data)

async def main():
    joystick_manager = joystick_managers.JoystickManager()
    webrtc_manager = connection_managers.WebRTCManager()
    socketio_manager = connection_managers.SocketIOManager(
        webrtc_manager, 
        joystick_manager=joystick_manager
    )
    if True:
        await socketio_manager.connect_sio()
        while True:
            await socketio_manager.tick(sleep_interval=0.001)
    
    await sio.connect("http://localhost:4000")
    print("My sid:", sio.sid)
    room = "foo"
    await createPeerConnection()
    await sio.emit("create or join", room)
    # await sendMessage("got user media")
    await sio.emit("ready")
    await sio.emit("registerForAudioData")
    await sio.emit("registerForBrainControl")
    # get_gamepad hangs until an event arrives (requires moving the joystick)
    sio.start_background_task(watch_joystick_process)
    await sio.wait()

async def close():
    await asyncio.sleep(0.1)

def rank0():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            main()
        )
    except KeyboardInterrupt as e:
        print("Keyboard Interrupt")
    finally:
        print("Cleaning up")
        loop.run_until_complete(
            close()
        )

        print("Exiting")

if __name__ == "__main__":
    rank0()
