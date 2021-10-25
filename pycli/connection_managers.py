import asyncio
import socketio

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

import base64
import cv2
import numpy as np
import os
import pyaudio
from scipy.io import wavfile

class SocketIOManager():
    def __init__(
        self, 
        webrtc_manager,
        joystick_manager=None,
        register_for_audio_data=False,
        register_for_brain_control=False
    ) -> None:
        self.sio = socketio.AsyncClient()
        self.webrtc_manager = webrtc_manager
        self.joystick_manager = joystick_manager
        self.register_for_audio_data = register_for_audio_data
        self.register_for_brain_control = register_for_brain_control
        self.__hookup_sio()
    
    async def connect_sio(self):
        await self.sio.connect("http://localhost:4000")
        await self.webrtc_manager.createPeerConnection()
        room = "foo"
        await self.sio.emit("create or join", room)
        await self.sio.emit("ready")
        if self.register_for_audio_data:
            await self.sio.emit("registerForAudioData")
        if self.register_for_brain_control:
            await self.sio.emit("registerForBrainControl")

    async def tick(self, sleep_interval):
        await self.sio.sleep(sleep_interval)
        joystick_data = self.joystick_manager.tick()
        if joystick_data is not None:
            await self.sio.emit("motor", joystick_data)

    def __hookup_sio(self):
        sio = self.sio

        @sio.on("ready")
        async def on_ready():
            print("Received ready")
            offer = await self.webrtc_manager.createOffer()
            await sio.emit("offer", offer)

        @sio.on("created")
        async def on_created(data, *args):
            print("Received on_created")
            self.webrtc_manager.isInitiator = True

        @sio.on("isinitiator")
        async def on_isinitiator(room):
            print("Received isInitiator")
            await self.webrtc_manager.cleanup()
            self.webrtc_manager.isInitiator = True
            await self.webrtc_manager.createPeerConnection()

        @sio.on("candidate")
        async def on_candidate(data):
            await self.webrtc_manager.on_candidate(data)
        
        @sio.on("offer")
        async def on_offer(data):
            answer = await self.webrtc_manager.on_offer(data)
            await self.sio.emit("answer", answer)

        @sio.on("answer")
        async def on_answer(data):
            await self.webrtc_manager.on_answer(data)

        @sio.on("braincontrol")
        async def on_brain_control(data):
            # Comes from web browser
            print("BRAIN:", data)
            if "speak" in data:
                print("SPEAK:", data["speak"])
                text = data["speak"].lower()
                filename = "./wav/" + text + ".wav"
                if os.path.exists(filename):
                    self.webrtc_manager.audio_replay_track.openWave(filename)
                else:
                    print("Cannot speak: no file")

        @sio.on("audiodata")
        async def on_audio_data(data):
            try:
                vals = data.split(",")
                vals = np.array([int(v) for v in vals if v])
                '''
                if do_graph:
                    if itr + len(vals) >= to_graph.shape[0]:
                        itr = 0
                    to_graph[itr:itr + len(vals)] = vals[:]
                    itr += len(vals)
                    line.set_ydata(to_graph)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                '''
            except Exception as e:
                print(e)

        @sio.on("frame")
        async def on_frame(data):
            data = base64.b64decode(data)
            data = np.frombuffer(data, dtype=np.uint8)
            data = cv2.imdecode(data, flags=cv2.IMREAD_COLOR)
            cv2.imshow("frame", data)
            cv2.waitKey(5)

class WebRTCManager():
    def __init__(self) -> None:
        self.isInitiator = False
        self.pc = None
        self.last_video_frame = np.zeros((600, 800, 3)) # Changes
        self.last_audio_frame = np.zeros((1, 1920))
        self.audio_replay_track = AudioReplayTrack()

    async def cleanup(self):
        await self.pc.close()
        self.pc = None

    async def createPeerConnection(self):
        p = pyaudio.PyAudio()
        self.p_stream = None
        if self.pc:
            raise Exception("RTCPeerConnection alread established")

        self.pc = RTCPeerConnection()
        pc = self.pc
        print("Created RTCPeerConnection")
        @pc.on("track")
        async def on_track(track):
            global p_stream
            print("Received track:", track.kind)
            if track.kind == "audio":
                while True:
                    try:
                        frame = await track.recv()

                        if not self.p_stream:
                            assert frame.format.bits == 16
                            assert frame.sample_rate == 48000
                            assert frame.layout.name == "stereo"
                            self.p_stream = p.open(format=pyaudio.paInt16,
                                channels=2,
                                rate=48000,
                                output=True)

                        as_np = frame.to_ndarray()
                        self.last_audio_frame = as_np
                        self.audio_replay_track.addFrame({
                            "data": as_np,
                            "pts": frame.pts
                        })

                        as_np = as_np.astype(np.int16).tostring()
                        self.p_stream.write(as_np)

                    except Exception as e:
                        print("Error receiving audio:", e)
                        raise e

            if track.kind == "video":
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_rgb().to_ndarray()
                        self.last_video_frame = img
                        cv2.imshow("Android Camera", img)
                        cv2.waitKey(5)
                    except Exception as e:
                        print("Error receiving track", e)
                        raise e

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("connectionstatechange:", pc.connectionState)
            if pc.connectionState == "connected":
                self.speek("hey")
                self.speek("sam")

    async def createOffer(self):
        if not self.isInitiator:
            return
            # raise Exception("Should createOffer only when the initiator")

        await self.addTracks()
        print("isInitiator: creating offer")
        desc = await self.pc.createOffer()
        print("Created local description")
        await self.pc.setLocalDescription(desc)
        print("SENDING MESSAGE: createOffer", desc)
        return object_to_string(self.pc.localDescription)
        

    async def on_candidate(self, data):
        print("Got candidate NEW:", data)
        can = sdp.candidate_from_sdp(data["candidate"])
        can.sdpMid = data["id"]
        can.sdMLineIndex = data["label"]
        await self.pc.addIceCandidate(can)

    async def on_offer(self, data):
        print("GOT OFFER:", data)
        try:
            obj = object_from_string(data)
            if isinstance(obj, RTCSessionDescription):
                await self.pc.setRemoteDescription(obj)
        except Exception as e:
            print("Could not decompose offer into session description directly", e)
            await self.pc.setRemoteDescription(
                RTCSessionDescription(
                    sdp=data["sdp"], type=data["type"]
                )
            )
        
        await self.addTracks()
        localDesc = await self.pc.createAnswer()
        print("CREATED LOCAL DESC:", localDesc)
        await self.pc.setLocalDescription(localDesc)
        print("SENDING MESSAGE: on_offer", localDesc.type)
        return object_to_string(self.pc.localDescription)
        

    async def on_answer(self, data):
        try:
            obj = object_from_string(data)
            if isinstance(obj, RTCSessionDescription):
                await self.pc.setRemoteDescription(obj)
        except Exception as e:
            print("Could not decompose answer into session description directly", e)
            await self.pc.setRemoteDescription(
                RTCSessionDescription(
                    sdp=data["sdp"], type=data["type"]
                )
            )

    async def addTracks(self):
        
        self.pc.addTrack(self.audio_replay_track)

    def speek(self, text):
        filename = "./wav/" + text + ".wav"
        if os.path.exists(filename):
            self.audio_replay_track.openWave(filename)
        else:
            print("Cannot speak: no file")


class AudioReplayTrack(MediaStreamTrack):
    kind = "audio"
    def __init__(self):
        super().__init__()
        self.dataQueue = asyncio.Queue()
        self.playQueue = asyncio.Queue()
        self.itr = 0
        self.is_playing = False
        self.wavedata = np.array([])
        self.rate = 44100
        self.waveitr = 0

    async def recv(self):
        try:
            data_old = await self.dataQueue.get()
            do_replay = False
            if not do_replay:
                data = await self.readWave()
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
            audio_array[:,:] = data_old["data"][:,:]
            frame = av.AudioFrame.from_ndarray(audio_array, 's16')
            frame.sample_rate = 48000
            frame.time_base = '1/48000'
            frame.pts = data_old["pts"]
            self.itr += 960 # TODO: Correctly increment base
            return frame
        except Exception as e:
            print("AudioReplayTrack recv was called with Exception:", e)

    def addFrame(self, frame):
        self.dataQueue.put_nowait(frame)

    def openWave(self, filename):
        (rate, wavedata) = wavfile.read(filename)
        if len(wavedata.shape) == 1:
            print("Converting to stereo")
            wavedata = np.repeat(
                wavedata.reshape(-1, 1),
                2,
                axis=1
            )
        self.playQueue.put_nowait((rate, wavedata))

    async def readWave(self):
        if self.is_playing:
            if self.waveitr >= self.wavedata.shape[0]:
                if self.playQueue.qsize() > 0:
                    (self.rate, self.wavedata) = self.playQueue.get_nowait()
                    self.waveitr = 0
                else:
                    self.waveitr = 0
                    self.is_playing = False
        else:
            if self.playQueue.qsize() > 0:
                (self.rate, self.wavedata) = self.playQueue.get_nowait()
                self.waveitr = 0
                self.is_playing = True
        return self.wavedata

    def stop(self):
        try:
            super().stop()
            print("AudioReplayTrack stop was called")
        except Exception as e:
            print("AudioReplayTrack stop was called with exception:", e)
