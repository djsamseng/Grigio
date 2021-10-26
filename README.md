# Grigio

A companion for Pinot

## Requirements
- Ubuntu 20.04.3 LTS 64-bit Nvidia RTX 3090
- Webcam
- Total Wireless LG K31 Rebel Prepaid Smartphone
  - [Best Buy](https://www.bestbuy.com/site/total-wireless-lg-k31-rebel-prepaid/6444063.p?skuId=6444063&ref=212&loc=1&ref=212&loc=1&gclid=Cj0KCQjw-NaJBhDsARIsAAja6dPbySg3K3DWoG9a5rCGf3GOqX3ntnJa2rwmFQ7xNhtysT7ztk1mUa8aAorpEALw_wcB&gclsrc=aw.ds)
- Arduino Nano 33 Iot
  - [Amazon](https://www.amazon.com/dp/B07VW9TSKD?psc=1&ref=ppx_yo2_dt_b_product_details)
- BETU MG996R Servo Motor (11x)
  - [Amazon 5 pack](https://www.amazon.com/gp/product/B094VW8NYT/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
- Bolsen 2 DOF Short Pan and Tilt Servos Bracket Sensor Mount Kit (5x)
  - [Amazon 2 pack](https://www.amazon.com/gp/product/B07HQB95VY/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
- Aideepen ROT3U 6DOF Aluminium Robotic Arm Kit Silver Mechanical Robotic Clamp Claw for Arduino Without Servo
  - [Amazon](https://www.amazon.com/gp/product/B01NBBBE21/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
- Professional Metal Robot Arm/Gripper/Mechanical Claw/Clamp/Clip with High Torque Servo, RC Robotic Part Educational DIY for Arduino/Raspberry Pie, Science STEAM Maker Platform (Black)
  - [Amazon](https://www.amazon.com/gp/product/B08WPZ9FGW/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
- Steel brace with M4 screws and bolts
  - [Amazon](https://www.amazon.com/dp/B07KVY3HJP?psc=1&ref=ppx_yo2_dt_b_product_details)
- M2 screws and bolts (about 20x each)
- 22 AWG wire
  - [Amazon](https://www.amazon.com/dp/B083DN5R61?psc=1&ref=ppx_yo2_dt_b_product_details)

### Tools
- Dowell 10-22 AWG Wire Strippers
  - [Amazon](https://www.amazon.com/dp/B06X9875Z7?psc=1&ref=ppx_yo2_dt_b_product_details)
- Teenitor Solder Sucker
  - [Amazon](https://www.amazon.com/dp/B0739LXQ6N?psc=1&ref=ppx_yo2_dt_b_product_details)
- Kaiweets Digital Multimeter
  - [Amazon](https://www.amazon.com/dp/B08CX9W7G3?psc=1&ref=ppx_yo2_dt_b_product_details)
- Kungber DC Power Supply 30V 10A
  - [Amazon](https://www.amazon.com/dp/B08DJ1FDXV?psc=1&ref=ppx_yo2_dt_b_product_details)
- Weller SP80NUS 80-Watts LED Soldering Iron 
  - [Amazon](https://www.amazon.com/dp/B00B3SG796?psc=1&ref=ppx_yo2_dt_b_product_details)

## Installation

Note that socket.io versions need to be compatible. Here we use JS Socket.IO 4.x, python-socketio 5.x, and python-engineio 4.x

### server
```bash
$ cd server && yarn install
```

### Client
```bash
$ cd client && yarn install
```

### pycli
```bash
$ cd pycli
$ apt-get install python3-pyaudio portaudio19-dev # pyaudio dependencies
$ python -m venv env
$ source ./env/bin/activate
$ pip install -r requirements.txt
```

### android
- Install the Android 11.0 (R) API 30 SDK from Android Studio, Tools, SDK Manager
- The first time running the app will likely fail. Go into setting on the phone, Apps, Permission manager, Camera, Jade, See all Jade permissions, and grant Camera, Microphone and Storage permissions.

### Audio files
- [Text to voice generator](https://ttsmp3.com/) - Matthew voice
- `ffmpeg -i input.mp3 output.wav` and save into the pycli folder

### raspberry pi
- [Setup instructions](https://www.sigmdel.ca/michel/ha/rpi/streaming_en.html)
```bash
$ sudo apt-get install cmake libjpeg8-dev
$ wget https://github.com/jacksonliam/mjpg-streamer/archive/master.zip
$ unzip master.zip
$ cd mjpeg-streamer-master/mjpg-streamer-experimental
$ make
$ sudo make install

## Run

### server
```bash
$ cd server && yarn build && yarn start
```

### client
```bash
$ cd client && yarn start
```
http://localhost:3000

### pycli
```bash
$ python3 main.py # python 3.8.10
$ pkill -9 python3 # sometimes needed to fully close and unlock the camera
```

### android
- Connect the android phone, unlock the phone and trust the computer and select the phone in android studio (LGE LGL355DL) and run

### raspberry pi
```bash
$ /usr/local/bin/mjpg_streamer -i "/usr/local/lib/mjpg-streamer/input_uvc.so -d /dev/video0 -n -f 10 -r 1280x720" -o "/usr/local/lib/mjpg-streamer/output_http.so -p 8085 -w /usr/local/share/mjpg-streamer/www"
```
- Go to http://192.168.1.73:8085/stream.html
```bash
$ /usr/local/bin/mjpg_streamer -i "/usr/local/lib/mjpg-streamer/input_uvc.so -d /dev/video2 -n -f 10 -r 1280x720" -o "/usr/local/lib/mjpg-streamer/output_http.so -p 8086 -w /usr/local/share/mjpg-streamer/www"
```
- Go to http://192.168.1.73:8086/stream.html
