
from inputs import get_gamepad
import multiprocessing

throttle = 255//2
joystick_right = 1020/2
joystick_down = 1020/2
joystick_pan_right = 90
joystick_pan_down = 90
def get_joystick_data():
    global throttle
    global joystick_right
    global joystick_down
    global joystick_pan_right
    global joystick_pan_down

    events = get_gamepad()
    THROTTLE = "ABS_Z" # Forward is 0, toward me is 255
    JOYSTICK_RIGHT = "ABS_X" # Right is 1020, Left is 0
    JOYSTICK_DOWN = "ABS_Y" # Towards me is 1020, Forward is 0
    JOYSTICK_PAN_RIGHT = "ABS_HAT0X"
    JOYSTICK_PAN_DOWN = "ABS_HAT0Y"
    JOYSTICK_PAN_MULT = 10
    
    if len(events) == 1 and events[0].code == "SYN_REPORT":
        return

    for evt in events:
        if evt.code == THROTTLE:
            throttle = 255//2 - evt.state
        elif evt.code == JOYSTICK_RIGHT:
            joystick_right = evt.state
        elif evt.code == JOYSTICK_DOWN:
            joystick_down = evt.state
        elif evt.code == JOYSTICK_PAN_RIGHT:
            if evt.state == -1 or evt.state == 1:
                joystick_pan_right += evt.state * JOYSTICK_PAN_MULT
        elif evt.code == JOYSTICK_PAN_DOWN:
            if evt.state == -1 or evt.state == 1:
                joystick_pan_down += evt.state * JOYSTICK_PAN_MULT
    
    left_motor = 0
    right_motor = 0
    right_motor = throttle + int(throttle * (1020/2 - joystick_right) / 1020)
    left_motor = throttle + int(throttle * (joystick_right - 1020/2) / 1020)
    data = {
        "left": left_motor,
        "right": right_motor,
        "pan_right": joystick_pan_right,
        "pan_down": joystick_pan_down
    }
    return data
    
def get_joystick_p2(joystick_queue):
    while True:
        joystick_data = get_joystick_data()
        joystick_queue.put(joystick_data)

class JoystickManager():
    def __init__(self) -> None:
        self.joystick_queue = multiprocessing.Queue()
        self.p = multiprocessing.Process(target=get_joystick_p2, args=(self.joystick_queue,))
        self.p.start()

    def tick(self):
        joystick_data = None
        while not self.joystick_queue.empty():
            temp_data = self.joystick_queue.get_nowait()
            if temp_data is not None:
                joystick_data = temp_data
        return joystick_data
        