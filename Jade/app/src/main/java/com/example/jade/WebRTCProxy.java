package com.example.jade;

import android.Manifest;
import android.content.Context;
import android.se.omapi.Session;
import android.util.Log;
import android.view.SurfaceView;

import org.json.JSONException;
import org.json.JSONObject;
import org.webrtc.AudioSource;
import org.webrtc.AudioTrack;
import org.webrtc.Camera1Enumerator;
import org.webrtc.Camera2Enumerator;
import org.webrtc.CameraEnumerator;
import org.webrtc.DataChannel;
import org.webrtc.EglBase;
import org.webrtc.IceCandidate;
import org.webrtc.MediaConstraints;
import org.webrtc.MediaStream;
import org.webrtc.PeerConnection;
import org.webrtc.PeerConnectionFactory;
import org.webrtc.SdpObserver;
import org.webrtc.SessionDescription;
import org.webrtc.SurfaceViewRenderer;
import org.webrtc.VideoCapturer;
import org.webrtc.VideoRenderer;
import org.webrtc.VideoSource;
import org.webrtc.VideoTrack;

import java.net.URISyntaxException;
import java.util.ArrayList;

import io.socket.client.IO;
import io.socket.client.Socket;
import static io.socket.client.Socket.EVENT_CONNECT;
import static io.socket.client.Socket.EVENT_DISCONNECT;

import static org.webrtc.SessionDescription.Type.ANSWER;
import static org.webrtc.SessionDescription.Type.OFFER;

public class WebRTCProxy {
    private static final String TAG = "WebRTCProxy";
    private static final String ROOM_NAME = "foo";
    public static final String VIDEO_TRACK_ID = "ARDAMSv0";
    public static final int VIDEO_RESOLUTION_WIDTH = 1280;
    public static final int VIDEO_RESOLUTION_HEIGHT = 720;
    public static final int FPS = 30;

    private Socket socket;
    private PeerConnectionFactory peerConnectionFactory;
    private PeerConnection peerConnection;
    private SurfaceViewRenderer previewSurfaceViewRenderer;
    private EglBase rootEglBase;
    private AudioSource audioSource;
    private AudioTrack localAudioTrack;
    private VideoTrack videoTrackFromCamera;

    private boolean isInitiator = false;
    private boolean streamingVideo = false;


    public WebRTCProxy(SurfaceViewRenderer surfaceViewRenderer, Context context, EglBase eglBase) {
        previewSurfaceViewRenderer = surfaceViewRenderer;
        rootEglBase = eglBase;
        initializeSurfaceViews();
        initializePeerConnectionFactory(context);
        createVideoTrackFromCamera(context);
    }

    public void start(String url, Context context) {
        String[] permissions = {Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO};


        initializePeerConnections();
        connectToServer(url);
        socket.emit("ready");

    }

    private boolean logAndThrow(String str) throws Exception {
        Log.e(TAG, str);
        throw new Exception(str);
    }

    private boolean canOfferOrAnswer() throws Exception {
        if (peerConnection == null) {
            logAndThrow("peerConnection is null");
        }
        if (!socket.connected()) {
            logAndThrow("socket is not connected");
        }
        if (videoTrackFromCamera == null) {
            logAndThrow("videoTrackFromCamera is null");
        }
        if (localAudioTrack == null) {
            logAndThrow("localAudioTrack is null");
        }
        if (audioSource == null) {
            logAndThrow("audioSource is null");
        }
        if (peerConnection.getLocalDescription() != null) {
            logAndThrow("localDescription already set");
        }
        if (peerConnection.getRemoteDescription() != null) {
            logAndThrow("remoteDescription already set");
        }
        return true;
    }

    private void initializeSurfaceViews() {
        rootEglBase = EglBase.create();
        previewSurfaceViewRenderer.init(rootEglBase.getEglBaseContext(), null);
        previewSurfaceViewRenderer.setEnableHardwareScaler(true);
        previewSurfaceViewRenderer.setMirror(true);
    }

    private void initializePeerConnectionFactory(Context context) {
        if (peerConnectionFactory != null) {
            Log.e(TAG, "Already created a peerConnectionFactory");
            return;
        }
        PeerConnectionFactory.initializeAndroidGlobals(context, true, true, true);
        peerConnectionFactory = new PeerConnectionFactory();
        peerConnectionFactory.setVideoHwAccelerationOptions(rootEglBase.getEglBaseContext(), rootEglBase.getEglBaseContext());
    }

    private boolean connectToServer(String url) {
        try {
            Log.d(TAG, "Connecting to:" + url);
            socket = IO.socket(url);
            socket.on(EVENT_CONNECT, args -> {
                Log.d(TAG, "Connected to:" + url + ". Creating or joining room:" + ROOM_NAME);
                socket.emit("create or join", ROOM_NAME);
            }).on("created", args -> {
                Log.d(TAG, "Created room. Becoming initiator");
                isInitiator = true;
            }).on("isinitiator", args -> {
                Log.d(TAG, "Becoming initiator");
                isInitiator = true;
                streamingVideo = false;
                peerConnection = null;
                initializePeerConnections();
            }).on("ready", args -> {
                Log.d(TAG, "Received ready");
                try {
                    if (canOfferOrAnswer()) {
                        createOffer();
                    }
                }
                catch (Exception e) {
                    Log.e(TAG, "Exception receiving ready:" + e);
                    e.printStackTrace();
                }

            }).on("joined", args -> {
                Log.d(TAG, "Joined room");
            }).on("join", args -> {
                Log.d(TAG, "Another peer has joined the room");
            }).on("message", args -> {
                Log.e(TAG, "DROPPING MESSAGE:" + args);
            }).on("offer", args -> {
                Log.e(TAG, "GOT OFFER:" + args);
                try {
                    if (canOfferOrAnswer()) {
                        JSONObject message = (JSONObject) args[0];
                        peerConnection.setRemoteDescription(
                                new SimpleSdpObserver(),
                                new SessionDescription(OFFER, message.getString("sdp")));
                        startStreamingVideo();
                        createAnswer();
                    }
                }
                catch (Exception e) {
                    Log.e(TAG, "Offer invalid JSON object:" + e);
                    e.printStackTrace();
                }
            }).on("answer", args -> {
                Log.e(TAG, "GOT ANSWER:" + args);
                try {
                    JSONObject message = (JSONObject) args[0];
                    peerConnection.setRemoteDescription(new SimpleSdpObserver(),
                            new SessionDescription(ANSWER, message.getString("sdp")));
                }
                catch (JSONException e) {
                    Log.e(TAG, "Answer invalid JSON object:"  + e);
                    e.printStackTrace();
                }

            }).on("candidate", args -> {
                Log.e(TAG, "GOT CANDIDATE:" + args);
                try {
                    JSONObject message = (JSONObject) args[0];
                    IceCandidate candidate = new IceCandidate(message.getString("id"),
                            message.getInt("label"),
                            message.getString("candidate"));
                    peerConnection.addIceCandidate(candidate);
                }
                catch (JSONException e) {
                    Log.e(TAG, "Candidate invalid JSON object:" + e);
                    e.printStackTrace();
                }
            }).on(EVENT_DISCONNECT, args -> {
                Log.w(TAG, "Disconnected from:" + url);
            });
            socket.connect();

            return true;
        }
        catch (URISyntaxException e) {
            Log.e(TAG, "Error connecting to server");
            e.printStackTrace();
            return false;
        }

    }

    private void createOffer() {
        Log.e(TAG, "CREATE OFFER");
        if (!isInitiator) {
            Log.e(TAG, "Should not createOffer when not the initiator");
            return;
        }
        startStreamingVideo();
        MediaConstraints sdpMediaConstraints = new MediaConstraints();

        sdpMediaConstraints.mandatory.add(
                new MediaConstraints.KeyValuePair("OfferToReceiveAudio", "true"));
        sdpMediaConstraints.mandatory.add(
                new MediaConstraints.KeyValuePair("OfferToReceiveVideo", "true"));
        peerConnection.createOffer(new SimpleSdpObserver() {
            @Override
            public void onCreateSuccess(SessionDescription sessionDescription) {
                Log.d(TAG, "onCreateSuccess: ");
                peerConnection.setLocalDescription(new SimpleSdpObserver(), sessionDescription);
                JSONObject message = new JSONObject();
                try {
                    message.put("type", "offer");
                    message.put("sdp", sessionDescription.description);
                    socket.emit("offer", message);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }, sdpMediaConstraints);
    }

    private void createAnswer() {
        if (isInitiator) {
            Log.e(TAG, "Should not createAnswer when the initiator");
            return;
        }
        peerConnection.createAnswer(new SimpleSdpObserver() {
            @Override
            public void onCreateSuccess(SessionDescription sessionDescription) {
                peerConnection.setLocalDescription(new SimpleSdpObserver(), sessionDescription);
                JSONObject message = new JSONObject();
                try {
                    message.put("type", "answer");
                    message.put("sdp", sessionDescription.description);
                    socket.emit("answer", message);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }, new MediaConstraints());
    }

    private void createVideoTrackFromCamera(Context context) {
        MediaConstraints audioConstraints = new MediaConstraints();
        VideoCapturer videoCapturer = createVideoCapturer(context);
        VideoSource videoSource = peerConnectionFactory.createVideoSource(videoCapturer);
        videoCapturer.startCapture(VIDEO_RESOLUTION_WIDTH, VIDEO_RESOLUTION_HEIGHT, FPS);

        videoTrackFromCamera = peerConnectionFactory.createVideoTrack(VIDEO_TRACK_ID, videoSource);
        videoTrackFromCamera.setEnabled(true);
        //videoTrackFromCamera.addRenderer(new VideoRenderer(previewSurfaceViewRenderer));

        //create an AudioSource instance
        audioSource = peerConnectionFactory.createAudioSource(audioConstraints);
        localAudioTrack = peerConnectionFactory.createAudioTrack("101", audioSource);
    }

    private VideoCapturer createVideoCapturer(Context context) {
        VideoCapturer videoCapturer;
        videoCapturer = createCameraCapturer(new Camera2Enumerator(context));
        //videoCapturer = createCameraCapturer(new Camera1Enumerator(true));
        return videoCapturer;
    }

    private VideoCapturer createCameraCapturer(CameraEnumerator enumerator) {
        final String[] deviceNames = enumerator.getDeviceNames();

        for (String deviceName : deviceNames) {
            if (enumerator.isFrontFacing(deviceName)) {
                VideoCapturer videoCapturer = enumerator.createCapturer(deviceName, null);

                if (videoCapturer != null) {
                    return videoCapturer;
                }
            }
        }

        for (String deviceName : deviceNames) {
            if (!enumerator.isFrontFacing(deviceName)) {
                VideoCapturer videoCapturer = enumerator.createCapturer(deviceName, null);

                if (videoCapturer != null) {
                    return videoCapturer;
                }
            }
        }

        return null;
    }

    private void initializePeerConnections() {
        ArrayList<PeerConnection.IceServer> iceServers = new ArrayList<>();
        String URL = "stun:stun.l.google.com:19302";
        iceServers.add(new PeerConnection.IceServer(URL));

        PeerConnection.RTCConfiguration rtcConfig = new PeerConnection.RTCConfiguration(iceServers);
        MediaConstraints pcConstraints = new MediaConstraints();

        PeerConnection.Observer pcObserver = new PeerConnection.Observer() {
            @Override
            public void onSignalingChange(PeerConnection.SignalingState signalingState) {
                Log.d(TAG, "onSignalingChange: ");
            }

            @Override
            public void onIceConnectionChange(PeerConnection.IceConnectionState iceConnectionState) {
                Log.d(TAG, "onIceConnectionChange: " + iceConnectionState.name());
            }

            @Override
            public void onIceConnectionReceivingChange(boolean b) {
                Log.d(TAG, "onIceConnectionReceivingChange: ");
            }

            @Override
            public void onIceGatheringChange(PeerConnection.IceGatheringState iceGatheringState) {
                Log.d(TAG, "onIceGatheringChange: ");
            }

            @Override
            public void onIceCandidate(IceCandidate iceCandidate) {
                Log.d(TAG, "onIceCandidate: ");
                JSONObject message = new JSONObject();

                try {
                    message.put("type", "candidate");
                    message.put("label", iceCandidate.sdpMLineIndex);
                    message.put("id", iceCandidate.sdpMid);
                    message.put("candidate", iceCandidate.sdp);

                    Log.d(TAG, "onIceCandidate: sending candidate " + message);
                    socket.emit("candidate", message);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }

            @Override
            public void onIceCandidatesRemoved(IceCandidate[] iceCandidates) {
                Log.d(TAG, "onIceCandidatesRemoved: ");
            }

            @Override
            public void onAddStream(MediaStream mediaStream) {
                Log.d(TAG, "onAddStream: " + mediaStream.videoTracks.size());
                if (mediaStream.videoTracks.size() > 0) {
                    VideoTrack remoteVideoTrack = mediaStream.videoTracks.get(0);
                    remoteVideoTrack.setEnabled(true);
                    remoteVideoTrack.addRenderer(new VideoRenderer(previewSurfaceViewRenderer));
                }
                else {
                    Log.w(TAG, "No remote video tracks");
                }

                if (mediaStream.audioTracks.size() > 0) {
                    AudioTrack remoteAudioTrack = mediaStream.audioTracks.get(0);
                    remoteAudioTrack.setEnabled(true);
                }
                else {
                    Log.w(TAG, "No remote audio tracks");
                }
            }

            @Override
            public void onRemoveStream(MediaStream mediaStream) {
                Log.d(TAG, "onRemoveStream: ");
            }

            @Override
            public void onDataChannel(DataChannel dataChannel) {
                Log.d(TAG, "onDataChannel: ");
            }

            @Override
            public void onRenegotiationNeeded() {
                Log.d(TAG, "onRenegotiationNeeded: ");
            }
        };
        if (peerConnection != null) {
            Log.e(TAG, "Already created a peerConnection");
            return;
        }

        peerConnection = peerConnectionFactory.createPeerConnection(rtcConfig, pcConstraints, pcObserver);
    }

    private void startStreamingVideo() {
        if (streamingVideo) {
            Log.e(TAG, "Already streaming video");
            return;
        }
        MediaStream mediaStream = peerConnectionFactory.createLocalMediaStream("ARDAMS");
        mediaStream.addTrack(videoTrackFromCamera);
        mediaStream.addTrack(localAudioTrack);
        peerConnection.addStream(mediaStream);
        streamingVideo = true;
    }
}

class SimpleSdpObserver implements SdpObserver {
    @Override
    public void onCreateSuccess(SessionDescription sessionDescription) {
    }

    @Override
    public void onSetSuccess() {
    }

    @Override
    public void onCreateFailure(String s) {
    }

    @Override
    public void onSetFailure(String s) {
    }
}
