import importlib
import PySimpleGUI as sg

import midi
import functions

gui = True
# gui = False

if gui:
    # Create list to display:
    devices = midi.get_devices()
    device_list = []
    for i, device in enumerate(devices):
        device_list.append((str(i), device[0].decode() + " " + device[1].decode() + ", " +
                            ("input" if device[2] else "") + ("output" if device[3] else "") + ", " +
                            ("in use" if device[4] else "not in use")))

    # Create window:
    sg.theme('DarkBlack')
    layout = [[sg.Text('Choose a midi device')],
              [sg.Listbox(values=device_list, size=(40, 6), key='-LIST-', enable_events=True)],
              [sg.Button('Cancel')]]
    window = sg.Window('Midi Macro', layout)

    event, values = window.read()
    if event in (None, 'Cancel'):
        exit(0)

    window.close()

    # Create midi object
    ids = midi.get_id_pair(int(values['-LIST-'][0][0]))
    midi_device = midi.Midi(ids[0], ids[1])
else:
    midi_device = midi.Midi()

# Get input and output ids so we can recreate the object later
midi_io_ids = midi_device.get_io_ids()


# noinspection PyShadowingNames
def main_gui() -> chr:
    layout = [[sg.Button('Reload'), sg.Button('Exit')]]
    window = sg.Window('Midi Macro', layout)
    event, values = window.read()
    if event in (None, 'Exit'):
        if midi_device is not None:
            midi_device.close()
        exit(1)

    window.close()
    return 'r' if event == 'Reload' else ''


# Main loop
k = None
try:
    while True:
        print('Starting...')
        # Start midi thread (except on the first loop)
        if k is not None:
            midi_device = midi.Midi(midi_io_ids[0], midi_io_ids[1])
        # Import functions
        functions.Functions(midi_device)

        while True:
            # Wait for keypress or click
            k = main_gui() if gui else input()
            if k == 'r':
                midi_device.close()
                importlib.reload(functions)
                break
except KeyboardInterrupt:
    if midi_device is not None:
        midi_device.close()
