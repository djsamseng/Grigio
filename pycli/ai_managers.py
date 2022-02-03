
import heapq
import numpy as np
import time

import actions

def search_memory(audio, memory=[], model=None):
    encoded = model(audio)
    found = []
    for (t0, encoded_mem, raw_mem) in memory:
        if np.abs(encoded_mem - encoded) < 0.01:
            found.append((t0, encoded_mem, raw_mem))
    t1 = time.time()
    heapq.heappush(memory, (t1, encoded, audio))
    return found

def reencode_memory(memory, model):
    model.train() # Model is brand new and can better correlate
    new_memory = []
    for (t0, old_encoded_mem, raw_mem) in memory:
        new_encoded = model(raw_mem)
        heapq.heappush(new_memory, (t0, new_encoded, raw_mem))
    return new_memory

class MainAI():
    def __init__(self, socketio_manager, webrtc_manager) -> None:
        self.socketio_manager = socketio_manager
        self.webrtc_manager = webrtc_manager
        self.action_scheduler = actions.ActionScheduler()
        check_phone_sight = actions.CheckPhoneSightAction("Check phone sight", webrtc_manager)
        t1 = time.time() + 0.1
        self.action_scheduler.schedule_action(t1, check_phone_sight)
        check_phone_audio = actions.CheckPhoneAudioAction("Check phone audio", webrtc_manager)
        t1 = time.time() + 0.1
        self.action_scheduler.schedule_action(t1, check_phone_audio)

    def tick(self) -> None:
        self.check_time()

    def check_time(self) -> None:
        actions = self.action_scheduler.check_time()
        for a in actions:
            print("Processing action:", a.desc)
            next_iterval = a.step()
            if next_iterval is not None:
                t1 = time.time() + next_iterval
                self.action_scheduler.schedule_action(t1, a)
