import asyncio

import connection_managers
import joystick_managers

from numba import cuda

async def main():
    joystick_manager = joystick_managers.JoystickManager()
    webrtc_manager = connection_managers.WebRTCManager()
    socketio_manager = connection_managers.SocketIOManager(
        webrtc_manager, 
        joystick_manager=joystick_manager
    )
    await socketio_manager.connect_sio()
    while True:
        await socketio_manager.tick(sleep_interval=0.001)

async def close():
    await asyncio.sleep(0.1)

def rank0():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            main()
        )
    except KeyboardInterrupt as e:
        print("Keyboard Interrupt")
    finally:
        print("Cleaning up")
        loop.run_until_complete(
            close()
        )

        print("Exiting")

if __name__ == "__main__":
    rank0()
