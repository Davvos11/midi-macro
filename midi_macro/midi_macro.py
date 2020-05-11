import PySimpleGUI as sg
from queue import Queue

from midi_macro import midi


class MidiMacro:
    def __init__(self, functions: type, queue=Queue(), gui=False) -> None:
        self.functions = functions
        self.queue = queue

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
            sg.SetOptions(window_location=(100, 100))
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
            self.midi_device = midi.Midi(ids[0], ids[1])
        else:
            self.midi_device = midi.Midi()

        # Get input and output ids so we can recreate the object later
        self.midi_io_ids = self.midi_device.get_io_ids()

    def run(self) -> None:
        functions = self.functions

        self.midi_device.set_queue(self.queue)
        # Import functions
        functions(self.midi_device)

    def close(self):
        self.midi_device.close()
