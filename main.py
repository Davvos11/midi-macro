import importlib

import midi
import functions

# Create midi object
midi_device = midi.Midi('tui')

# Get input and output ids so we can recreate the object later
midi_io_ids = midi_device.get_io_ids()

# Main loop
try:
    while True:
        print('Starting...')
        # Start midi thread
        midi_device = midi.Midi('tui', midi_io_ids[0], midi_io_ids[1])
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
