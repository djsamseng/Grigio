package com.example.jade;

import androidx.annotation.ContentView;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.graphics.Rect;
import android.hardware.Camera;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.FrameLayout;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class CameraFocusActivity extends AppCompatActivity {
    private static String TAG = "CameraFocusActivity";
    private Camera mCamera;
    private CameraPreview mCameraPreview;
    private FrameLayout mFrameLayout;
    private String mFocusMode = Camera.Parameters.FOCUS_MODE_AUTO;
    private boolean rotate90 = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera_focus);
        mFrameLayout = (FrameLayout) findViewById(R.id.camera_preview);
        initCamera();
    }

    @Override
    public boolean onTouchEvent(MotionEvent evt) {
        int x = (int) evt.getX();
        int y = (int) evt.getY();
        if (evt.getAction() == MotionEvent.ACTION_UP) {
            Log.d(TAG, "X:" + x + " Y:" + y);
            double width = mFrameLayout.getWidth();
            double height = mFrameLayout.getHeight();
            int cameraX = (int)(((double)x / width) * 2000 - 1000);
            int cameraY = (int)(((double)y / height) * 2000 - 1000);
            if (rotate90) {
                if (cameraX < 0 && cameraY < 0) {
                    cameraY *= -1;
                }
                else if (cameraX < 0 && cameraY > 0) {
                    cameraX *= -1;
                }
                else if (cameraX > 0 && cameraY < 0) {
                    cameraX *= -1;
                }
                else if (cameraX > 0 && cameraY > 0) {
                    cameraY *= -1;
                }
            }
            focusCamera(cameraX, cameraY);
        }
        return false;
    }

    private void initCamera() {
        mCamera = Camera.open(0);
        Camera.CameraInfo info = new Camera.CameraInfo();
        Camera.getCameraInfo(0, info);
        Camera.Parameters params = mCamera.getParameters();

        // Need to rotate touch position too!
        if (rotate90) {
            mCamera.setDisplayOrientation(90);
        }
        mCamera.setParameters(params);

        mCameraPreview = new CameraPreview(this, mCamera);

        mFrameLayout.addView(mCameraPreview);
    }

    private void focusCamera(int x, int y) {
        Camera.Parameters params = mCamera.getParameters();
        Log.d(TAG, "Current focusMode=" + mFocusMode);
        if (params.getMaxNumMeteringAreas() > 0) {
            Log.d(TAG, "METERING AREAS!");
        }
        if (params.getMaxNumFocusAreas() > 0) {
            List<Camera.Area> focusAreas = new ArrayList<Camera.Area>();
            int radius = 100;
            if (x - radius < -1000) {
                x = -1000 + radius;
            }
            if (y - radius < -1000) {
                y = -1000 + radius;
            }
            if (x + radius > 1000) {
                x = 1000 - radius;
            }
            if (y + radius > 1000) {
                y = 1000 - radius;
            }
            Log.d(TAG, "Focus left=" + (x-radius) + " Focus top=" + (y-radius));
            Rect area1 = new Rect(x-radius, y-radius, x+radius, y+radius);
            focusAreas.add(new Camera.Area(area1, 1000));
            params.setFocusAreas(focusAreas);
        }
        try {
            mCamera.setParameters(params);
        }
        catch (Exception e) {
            Log.d(TAG, "Failed to set Parameters:" + e.getMessage());
        }
        try {
            mCamera.autoFocus(this::onAutoFocus);
        }
        catch (Exception e) {
            Log.d(TAG, "Failed to autoFocus:" + e.getMessage());
        }
    }

    public void onAutoFocus(boolean success, Camera camera) {
        Log.d(TAG, "onAutoFocus success=" + success);
    }
}

class CameraPreview extends SurfaceView implements SurfaceHolder.Callback {
    private static String TAG = "CameraPreview";
    private SurfaceHolder mHolder;
    private Camera mCamera;
    public CameraPreview(Context context, Camera camera) {
        super(context);
        mCamera = camera;
        mHolder = getHolder();
        mHolder.addCallback(this);
        mHolder.setType(SurfaceHolder.SURFACE_TYPE_PUSH_BUFFERS);
    }

    public void surfaceCreated(SurfaceHolder holder) {
        try {
            mCamera.setPreviewDisplay(holder);
            mCamera.startPreview();
            Log.d(TAG, "surfaceCreated");
        }
        catch (IOException e) {
            Log.d(TAG, "Error setting preview:" + e.getMessage());
        }
    }

    public void surfaceDestroyed(SurfaceHolder holder) {
        Log.d(TAG, "Surface destroyed");
    }

    public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) {
        if (mHolder.getSurface() == null) {
            Log.d(TAG, "Surface is null");
            return;
        }
        try {
            mCamera.stopPreview();
        }
        catch (Exception e) {
            Log.d(TAG, "Error stopping preview:" + e.getMessage());
        }

        try {
            mCamera.setPreviewDisplay(mHolder);
            mCamera.startPreview();
            Log.d(TAG, "surfaceChanged");
        }
        catch (Exception e) {
            Log.d(TAG, "Error starting camera preview surfaceChanged:" + e.getMessage());
        }
    }
}