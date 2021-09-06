package com.example.jade;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.hardware.Camera;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.SurfaceView;
import android.view.TextureView;
import android.view.View;
import android.widget.SeekBar;
import android.widget.TextView;

import com.example.jade.CameraHelper;

import org.json.JSONObject;
import org.webrtc.EglBase;
import org.webrtc.SurfaceViewRenderer;

import java.io.BufferedInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.Policy;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;


public class JadeControllerActivity extends AppCompatActivity {
    private MediaRecorder d_mediaRecorder;
    private Camera d_camera;
    private int d_cameraId = 1;
    private int d_cameraOrientation = 90;
    private boolean d_isRecording = false;
    private File d_outputFile;
    private static String TAG = "JadeControllerActivity";
    AudioRecord d_audioRecord;
    Thread d_audioThread;
    EglBase rootEglBase;

    private WebRTCProxy webRTCProxy;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_jade_controller);

        Intent intent = getIntent();
        String message = intent.getStringExtra(MainActivity.EXTRA_MESSAGE);

        TextView textView = findViewById(R.id.textView);
        textView.setText(message);

        SeekBar seekBar = findViewById(R.id.seekBar);
        seekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                TextView textView = (TextView) findViewById(R.id.seekBarTextView);
                textView.setText(String.valueOf(progress));
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });

        rootEglBase = EglBase.create();
        SurfaceViewRenderer previewSurfaceView = findViewById(R.id.surfaceView);
        webRTCProxy = new WebRTCProxy(previewSurfaceView, this, rootEglBase);
        String URL = "http://192.168.1.220:4000";
        webRTCProxy.start(URL, this);
        // startRecording();
    }

    public void onNextCameraButtonPress(View view) {
        d_cameraId += 1;
        if (d_cameraId >= Camera.getNumberOfCameras()) {
            d_cameraId = 0;
        }
        //startRecording();
    }

    public void onRotateButtonPress(View view) {
        d_cameraOrientation += 90;
        if (d_cameraOrientation >= 360) {
            d_cameraOrientation = 0;
        }
        d_camera.setDisplayOrientation(d_cameraOrientation);
    }

    private void startRecording() {
        if (d_isRecording) {
            stopRecording();
        }
        try {
            Thread.sleep(1000);
        } catch (Exception e) {
            Log.d("startRecording", "Failed to sleep before restarting camera");
        }
        new MediaPrepareTask().execute(null, null, null);
    }

    private void stopRecording() {
        try {
            d_mediaRecorder.stop();
        }
        catch (RuntimeException e) {
            Log.d("startRecording", "RuntimeException: stop() is called immediately after start()");

        }
        releaseMediaRecorder();
        d_camera.lock();
        d_isRecording = false;
        releaseCamera();
        d_audioRecord.stop();
        d_audioRecord.release();
        d_audioRecord = null;
        d_audioThread = null;
    }

    private boolean prepareVideoRecorder() {
        Log.d("prepareVideoRecorder", "Number of cameras:" + Camera.getNumberOfCameras() + " Opening:" + d_cameraId);
        d_camera = Camera.open(d_cameraId);

        Camera.Parameters parameters = d_camera.getParameters();
        List<Camera.Size> supportedPreviewSizes = parameters.getSupportedPreviewSizes();
        List<Camera.Size> supportedVideoSizes = parameters.getSupportedVideoSizes();
        TextureView previewTextureView = findViewById(R.id.textureView2);
        Camera.Size optimalSize = CameraHelper.getOptimalVideoSize(
                null,
                supportedPreviewSizes,
                previewTextureView.getWidth(),
                previewTextureView.getHeight()
        );
        //CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_HIGH);
        //profile.videoFrameWidth = optimalSize.width;
        //profile.videoFrameHeight = optimalSize.height;
        parameters.setPreviewSize(optimalSize.width, optimalSize.height);
        Log.d("prepareVideoRecorder", "Width:" + optimalSize.width + " Height:" + optimalSize.height);
        Log.d(TAG, "Supported:" + parameters.getSupportedPreviewSizes());
        d_camera.setParameters(parameters);
        d_camera.setDisplayOrientation(90);
        try {
            if (true) {
                d_camera.setPreviewTexture(previewTextureView.getSurfaceTexture());
            }

        }
        catch (IOException e) {
            Log.e("prepareVideoRecorder", "Surface texture is unavailable or unsuitable" + e.getMessage());
            return false;
        }

        ExecutorService executorService = Executors.newFixedThreadPool(4);

        Camera.PreviewCallback callback = new Camera.PreviewCallback() {
            boolean didSend = false;
            @Override
            public void onPreviewFrame(byte[] data, Camera camera) {
                executorService.execute(new Runnable() {
                    @Override
                    public void run() {
                        if (!didSend) {
                            sendVideoData(data);
                            didSend = true;
                        }
                    }
                });

                // Log.d(TAG, "GOT DATA!!!!!");
            }
        };
        d_camera.setPreviewCallback(callback);


        //d_mediaRecorder = new MediaRecorder();
        //d_camera.unlock();
        return true;
        /*d_mediaRecorder.setCamera(d_camera);
        d_mediaRecorder.setAudioSource(MediaRecorder.AudioSource.DEFAULT);
        d_mediaRecorder.setVideoSource(MediaRecorder.VideoSource.CAMERA);
        d_mediaRecorder.setProfile(profile);

        // TODO
        d_outputFile = CameraHelper.getOutputMediaFile(CameraHelper.MEDIA_TYPE_VIDEO);
        if (d_outputFile == null) {
            Log.d("prepareVideoRecorder", "Unable to get output file");
            return false;
        }
        d_mediaRecorder.setOutputFile(d_outputFile.getPath());

        try {
            d_mediaRecorder.prepare();
        }
        catch (IllegalStateException e) {
            Log.d("prepareVideoRecorder", "IllegalStateExpection preparing MediaRecorder: " + e.getMessage());
            releaseMediaRecorder();
            return false;
        }
        catch (IOException e) {
            Log.d("prepareVideoRecorder", "IOException preparing MediaRecorder: " + e.getMessage());
            releaseMediaRecorder();
            return false;
        }

        Log.d("prepareVideoRecorder", "Return TRUE!!!!!!!!!!!!!!!!!!!!!!");
        return true;*/
    }

    private void startAudioRecording() {
        int RECORDER_SAMPLERATE = 8000;
        int RECORDER_CHANNELS = AudioFormat.CHANNEL_IN_MONO;
        int RECORDER_AUDIO_ENCODING = AudioFormat.ENCODING_PCM_16BIT;
        int BufferElements2Rec = 1024; // Want 2048 (2k) - thus 2048/2 since 2 bytes per 16 bit format
        int BytesPerElement = 2; // 2 bytes in 16bit format
        d_audioRecord = new AudioRecord(MediaRecorder.AudioSource.MIC,
                RECORDER_SAMPLERATE,
                RECORDER_CHANNELS,
                RECORDER_AUDIO_ENCODING,
                BufferElements2Rec * BytesPerElement);
        d_audioRecord.startRecording();

        d_audioThread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (d_isRecording) {
                    short sData[] = new short[BufferElements2Rec];
                    d_audioRecord.read(sData, 0, BufferElements2Rec);
                    // sendAudioData(sData);
                }
            }
        }, "AudioRecorder thread");
        d_audioThread.start();
    }

    private void sendVideoData(byte[] data) {
        TextView textView = findViewById(R.id.textView);
        String urlInput = textView.getText().toString() + "/video";
        HttpURLConnection urlConnection = null;
        try {
            URL url = new URL(urlInput);
            urlConnection = (HttpURLConnection) url.openConnection();
            urlConnection.setRequestMethod("POST");
            urlConnection.setRequestProperty("Content-Type", "application/json;charset=UTF-8");
            urlConnection.setRequestProperty("Accept", "application/json");
            urlConnection.setDoOutput(true);
            urlConnection.setDoInput(false);

            JSONObject jsonParam = new JSONObject();
            jsonParam.put("video", new String(data));
            DataOutputStream os = new DataOutputStream(urlConnection.getOutputStream());
            //os.write();
            os.writeBytes(jsonParam.toString());
            os.flush();
            os.close();
            Log.i(TAG, urlConnection.getResponseMessage());
        }
        catch (Exception e) {
            Log.e(TAG, "Failed to send request:" + e.getMessage() + e.toString());
        }
        finally {
            if (urlConnection != null) {
                urlConnection.disconnect();
            }
        }
    }

    private void sendAudioData(short sData[]) {
        TextView textView = findViewById(R.id.textView);
        String urlInput = textView.getText().toString() + "/happiness";
        Log.d(TAG, "URL:" + urlInput);
        HttpURLConnection urlConnection = null;
        try {
            URL url = new URL(urlInput);
            urlConnection = (HttpURLConnection) url.openConnection();
            urlConnection.setRequestMethod("POST");
            urlConnection.setRequestProperty("Content-Type", "application/json;charset=UTF-8");
            urlConnection.setRequestProperty("Accept", "application/json");
            urlConnection.setDoOutput(true);
            urlConnection.setDoInput(true);

            JSONObject jsonParam = new JSONObject();
            jsonParam.put("happiness", 10);
            DataOutputStream os = new DataOutputStream(urlConnection.getOutputStream());
            os.writeBytes(jsonParam.toString());
            os.flush();
            os.close();
            Log.i(TAG, urlConnection.getResponseMessage());
        }
        catch (Exception e) {
            Log.e(TAG, "Failed to send request:" + e.getMessage());
        }
        finally {
            if (urlConnection != null) {
                urlConnection.disconnect();
            }
        }
    }

    private void releaseMediaRecorder() {
        if (d_mediaRecorder != null) {
            d_mediaRecorder.reset();
            d_mediaRecorder.release();
            d_mediaRecorder = null;
            d_camera.lock();
        }
    }

    private void releaseCamera() {
        if (d_camera != null) {
            d_camera.release();
            d_camera = null;
        }
    }

    class MediaPrepareTask extends AsyncTask<Void, Void, Boolean> {

        @Override
        protected Boolean doInBackground(Void... voids) {
            try {
                Thread.sleep(1000);
                if (prepareVideoRecorder()) {
                    Log.d("MediaPrepareTask", "Success: calling start");
                    Thread.sleep(1000);
                    //d_mediaRecorder.start();
                    d_isRecording = true;
                    d_camera.startPreview();
                    startAudioRecording();
                    return true;
                }
            }
            catch (Exception e) {
                Log.e("doInBackground", "Failed:" + e.getMessage() + e.toString());
            }

            releaseMediaRecorder();
            return false;
        }

        @Override
        protected void onPostExecute(Boolean result) {
            Log.d("MediaPrepareTask", "onPostExecute:" + d_isRecording);
        }
    }
}