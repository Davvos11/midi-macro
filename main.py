import atexit
import importlib

import midi
import functions

# List midi devices
devices = midi.get_devices()
# Ask user to choose a device
midi_id = int(input("Choose a midi device: "))

# Get input and output ids based on the user provided id
midi_io_ids = midi.get_id_pair(midi_id)

midi_device = None

# Main loop
try:
    while True:
        print('Starting...')
        # Start midi thread
        midi_device = midi.Midi(midi_io_ids[0], midi_io_ids[1])
        # Import functions
        functions.Functions(midi_device)

        while True:
            # Wait for keypress
            k = input()
            if k == 'r':
                midi_device.close()
                importlib.reload(functions)
                break
except KeyboardInterrupt:
    if midi_device is not None:
        midi_device.close()
