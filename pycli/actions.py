import cv2
import heapq
import time
from abc import abstractmethod
from typing import Union

class Action():
    def __init__(self, desc) -> None:
        self.desc = desc

    @abstractmethod
    def step(self) -> Union[None, float]:
        '''
        is_done = False
        if is_done:
            return None
        next_interval = 0.1
        return next_interval
        '''
        pass

class CheckPhoneSightAction(Action):
    def __init__(self, desc, webrtc_manager) -> None:
        super().__init__(desc)
        self.webrtc_manager = webrtc_manager
    
    def step(self):
        frame = self.webrtc_manager.last_video_frame
        cv2.imshow("Phone sight", frame)
        cv2.waitKey(5)
        next_interval = 0.1
        return next_interval

class CheckPhoneAudioAction(Action):
    def __init__(self, desc, webrtc_manager) -> None:
        super().__init__(desc)
        self.webrtc_manager = webrtc_manager

    def step(self):
        frame = self.webrtc_manager.last_audio_frame
        self.webrtc_manager.speek("hey")
        next_interval = 3
        return next_interval

class ActionScheduler():
    def __init__(self) -> None:
        self.actions_scheduled = []

    def check_time(self) -> "list[Action]":
        now = time.time()
        itr = 0
        for _ in range(len(self.actions_scheduled)):
            (t, action) = self.actions_scheduled[itr]
            if t > now:
                break
            itr += 1
        actions = []
        for _ in range(itr):
            actions.append(heapq.heappop(self.actions_scheduled)[1])
        return actions

    def schedule_action(self, t: float, action: Action) -> None:
        heapq.heappush(self.actions_scheduled, (t, action))