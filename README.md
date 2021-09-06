# Grigio

A companion for Pinot

## Requirements
- Ubuntu 20.04.3 LTS 64-bit Nvidia RTX 3090 
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

### Server
```bash
$ cd server && yarn install
```

## Run

### Server
```bash
$ cd server && yarn build && yarn start
```
