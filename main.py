import atexit
import time

import pulseaudio
import midi

# Init:
devices = midi.get_devices()
for i, device in enumerate(devices):
    print(str(i) + ": " + device[0].decode() + " " + device[1].decode() + ", " + ("input" if device[2] else "") +
          ("output" if device[3] else "") + ", " + ("in use" if device[4] else "not in use"))
midi_id = int(input("Choose a midi device: "))

midi_input_id = [i for i, device in enumerate(devices) if device[1] == devices[midi_id][1] and device[2]][0]
midi_output_id = [i for i, device in enumerate(devices) if device[1] == devices[midi_id][1] and device[3]][0]

midi = midi.Midi(midi_input_id, midi_output_id)
midi.start()


def on_note(args: tuple):
    print(args)


midi.add_event(on_note, 1, midi.Type.NOTE_ON)

time.sleep(3)
print('removing')

midi.remove_event(1, midi.Type.NOTE_ON)


def on_exit():
    midi.close()


atexit.register(on_exit)
