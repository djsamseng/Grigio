package com.example.jade;

import androidx.appcompat.app.AppCompatActivity;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.widget.EditText;
import android.widget.SeekBar;
import android.widget.TextView;

public class SoundGenerationActivity extends AppCompatActivity {
    private static String TAG = "SoundGenerationActivity";
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sound_generation);
        new PlayAudioTask().execute();
    }

    class PlayAudioTask extends AsyncTask<Void, Integer, Boolean> {
        private AudioTrack track;
        protected Boolean doInBackground(Void... params) {
            Log.d(TAG, "PlayAudioTask doInBackground start");
            short[] buffer = new short[1024];
            int sampleRateInHz = 44100;
            int channelConfig = AudioFormat.CHANNEL_CONFIGURATION_MONO;
            int audioFormat = AudioFormat.ENCODING_PCM_16BIT;
            int minBufferSize = AudioTrack.getMinBufferSize(sampleRateInHz, channelConfig, audioFormat);
            this.track = new AudioTrack(
                    AudioManager.STREAM_MUSIC,
                    sampleRateInHz,
                    channelConfig,
                    audioFormat,
                    minBufferSize,
                    AudioTrack.MODE_STREAM);


            float samples[] = new float[1024];

            TextView statusTextView = (TextView) findViewById(R.id.statusTextView);
            statusTextView.setText("Playing");
            Log.d(TAG, "PlayAudioTask this.track.play");
            this.track.play();

            while (true) {

                SeekBar frequencySeekBar = (SeekBar) findViewById(R.id.frequencySeekBar);
                int frequency = frequencySeekBar.getProgress();
                Log.d(TAG, "PlayAudioTask starting loop frequency:" + frequency);
                float increment = (float)(2*Math.PI) * frequency / sampleRateInHz;
                float angle = 0;
                // TODO: Multiple sin waves with different frequencies and different phases overlapped
                // Each frequency should die off after being started
                // TRAIN: to recreate the sounds it hears using these sin waves
                // in hopes this neural net will do better than a FFT
                for (int i = 0; i < samples.length; i++) {
                    samples[i] = (float) Math.sin(angle);
                    buffer[i] = (short) (samples[i] * Short.MAX_VALUE);
                    angle += increment;
                }
                Log.d(TAG, "PlayAudioTask writing to buffer");
                this.track.write(buffer, 0, samples.length);
            }
            // statusTextView.setText("Finished");
        }
    }
}

