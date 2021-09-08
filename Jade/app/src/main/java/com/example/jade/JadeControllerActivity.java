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
    private static String TAG = "JadeControllerActivity";
    EglBase rootEglBase;

    private WebRTCProxy webRTCProxy;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webRTCProxy = null;
        setContentView(R.layout.activity_jade_controller);

        Intent intent = getIntent();
        String url = intent.getStringExtra(MainActivity.INTENT_URL_KEY);
        String roomName = intent.getStringExtra(MainActivity.INTENT_ROOM_KEY);

        TextView textView = findViewById(R.id.textView);
        textView.setText(url);

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
        webRTCProxy.start(url, roomName, this);
    }

    @Override
    public void onDestroy() {
        super.onDestroy();

        rootEglBase.release();
        rootEglBase = null;
        webRTCProxy.close();
        webRTCProxy = null;
    }
}