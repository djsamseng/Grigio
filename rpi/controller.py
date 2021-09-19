import asyncio
import socketio
import serial
import numpy as np

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

from romi_controller import RomiMotorController

SERVER_URL = "http://192.168.1.220:4000"
PORT ="/dev/ttyACM0"
BAUDRATE = 19200


motorController = RomiMotorController()
sio = socketio.AsyncClient()

## GLOBALS
pc = None
isInitiator = False
player = None
p_stream = None

async def addTracks():
    global player
    global audio_replay_track
    if player:
        if player.video:
            player.video.stop()
        if player.audio:
            player.audio.stop()

    player = MediaPlayer('/dev/video0', format='v4l2', options={
        'video_size': '320x240'
    })
    add_player(pc, player)

    print("Created peer")

@sio.on("offer")
async def on_offer(data):
    print("GOT OFFER:", data)
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
    await sio.emit("answer", {
        "sdp": localDesc.sdp,
        "type": localDesc.type
    })

didGetAnswer = False
@sio.on("answer")
async def on_answer(data):
    global didGetAnswer
    if didGetAnswer:
        return
    didGetAnswer = True
    print("GOT ANSWER:", data)
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
    if pc:
        raise Exception("RTCPeerConnection alread established")

    pc = RTCPeerConnection()
    print("Created RTCPeerConnection")
    @pc.on("track")
    async def on_track(track):
        global p_stream
        print("Received track:", track.kind)
        
    @pc.on("connectionstatechange")
    def on_connectionstatechange():
        print("connectionstatechange:", pc.connectionState)

async def createOffer():
    if not isInitiator:
        return
        # raise Exception("Should createOffer only when the initiator")

    await addTracks()
    print("isInitiator: creating offer")
    desc = await pc.createOffer()
    print("Created local description")
    await pc.setLocalDescription(desc)
    print("SENDING MESSAGE: createOffer", desc.type)
    await sio.emit("offer", {
        "sdp": desc.sdp,
        "type": desc.type
    })

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

@sio.on("motor")
async def on_motor(data):
    print("Received on_motor:", data)
    motorController.set_motors(int(data["left"]), int(data["right"]))

async def read_arduino():
    ser = serial.Serial(PORT, BAUDRATE)
    while True:
        await sio.sleep(0.001)
        try:
            val = ser.readline().decode("UTF-8").strip("\r\n")
            await sio.emit("audiodata", val)
        except Exception as e:
            print(e)
            continue

async def main():
    await sio.connect(SERVER_URL)
    print("Socket IO SID:", sio.sid)
    await sio.emit("registerForMotorControl")
    room = "foo"
    await createPeerConnection()
    await sio.emit("create or join", room)
    # await sendMessage("got user media")
    await sio.emit("ready")
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
