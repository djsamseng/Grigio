package com.example.jade;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;

public class MainActivity extends AppCompatActivity {
    public static final String INTENT_URL_KEY = "com.example.jade.URL";
    public static final String INTENT_ROOM_KEY = "com.example.jade.ROOM";
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        //onConnectButtonPress(null);
    }

    public void onConnectButtonPress(View view) {
        Intent intent = new Intent(this, JadeControllerActivity.class);
        EditText editText = (EditText) findViewById(R.id.editTextTextPersonName);
        String message = editText.getText().toString();
        intent.putExtra(INTENT_URL_KEY, message);
        intent.putExtra(INTENT_ROOM_KEY, "foo");
        startActivity(intent);
    }

    public void onSoundGenerationButtonPress(View view) {
        Intent intent = new Intent(this, SoundGenerationActivity.class);
        startActivity(intent);
    }
}