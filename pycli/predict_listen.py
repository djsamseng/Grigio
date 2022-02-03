import numpy as np
import pyaudio
import time
import torch

FORMAT = pyaudio.paFloat32
CHUNK = 1024 * 2
CHANNELS = 2
RATE = 44100

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using {} device".format(device))

class CircularNeuralNetwork(torch.nn.Module):
    def __init__(self, num_inputs, num_outputs, num_state) -> None:
        super(CircularNeuralNetwork, self).__init__()
        self.flatten = torch.nn.Flatten()
        num_in = num_inputs + num_state
        num_out = num_outputs + num_state
        hidden_height = 200
        hidden_depth = 200
        layers = []
        for i in range(hidden_depth):
            layers.append(torch.nn.Linear(hidden_height, hidden_height))
            layers.append(torch.nn.ReLU())
        
        self.linear_relu_stack = torch.nn.Sequential(
            torch.nn.Linear(num_in, hidden_height),
            torch.nn.ReLU(),
            *layers,
            torch.nn.Linear(hidden_height, num_out),
            torch.nn.Sigmoid()
        )
    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

NUM_INPUTS = CHUNK * CHANNELS
NUM_STATE = 150
NUM_OUTPUTS = CHUNK * CHANNELS
def create_model():
    num_inputs = NUM_INPUTS
    num_outputs = NUM_OUTPUTS
    num_state = NUM_STATE
    model_x = torch.rand((1, num_state + num_inputs))
    model = CircularNeuralNetwork(
        num_inputs=num_inputs,
        num_outputs=num_outputs,
        num_state=num_state).to(device)
    print("Created model with num_parameters:", len([p for p in model.parameters()]))
    loss_fn = torch.nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=100)
    model.train()
    return model, loss_fn, optimizer

model, loss_fn, optimizer = create_model()

last_audio_data = None
last_state = torch.zeros((1, NUM_STATE))
def stream_callback(data, frame_count, time_info, status):
    global last_audio_data
    data_np = np.frombuffer(data, np.float32)
    data_np = data_np.reshape((CHUNK, 2))
    if last_audio_data is not None:
        model_x = torch.zeros((1, NUM_STATE + NUM_INPUTS))
        model_x[1, :NUM_STATE] = last_state[1, :NUM_STATE]
        model_x[1, NUM_STATE:NUM_STATE+NUM_INPUTS] = last_audio_data
        pred = model(model_x)
        print("Pred:", pred)
    last_audio_data = data_np
    

    data_np_out = np.zeros_like(data_np)
    data = data_np_out.reshape((CHUNK * CHANNELS,)).tostring()
    return (data, pyaudio.paContinue)


def listen_main():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        frames_per_buffer=CHUNK,
        input=True,
        output=True,
        stream_callback=stream_callback
    )
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.00001)

def main():
    listen_main()

if __name__ == "__main__":
    main()