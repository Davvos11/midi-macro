import atexit
import midi

# List devices:
devices = midi.get_devices()
for i, device in enumerate(devices):
    print(str(i) + ": " + device[0].decode() + " " + device[1].decode() + ", " + ("input" if device[2] else "") +
          ("output" if device[3] else "") + ", " + ("in use" if device[4] else "not in use"))
# Ask user to choose a device
midi_id = int(input("Choose a midi device: "))

# Get input and output ids based on the user provided id
midi_input_id = [i for i, device in enumerate(devices) if device[1] == devices[midi_id][1] and device[2]][0]
midi_output_id = [i for i, device in enumerate(devices) if device[1] == devices[midi_id][1] and device[3]][0]

# Start midi thread
midi = midi.Midi(midi_input_id, midi_output_id)


def on_exit():
    midi.close()


# Register function to run on exit
atexit.register(on_exit)
