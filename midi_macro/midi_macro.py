from threading import Thread

import PySimpleGUI as sg
from queue import Queue

from midi_macro import midi


class MidiMacro(Thread):
    def __init__(self, functions: type, queue=Queue(), gui=False) -> None:
        super().__init__()
        self.functions = functions
        self.queue = queue
        self.midi_device = None
        self.first_run = True

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
            self.midi_in = ids[0]
            self.midi_out = ids[1]
            self.start_midi(ids[0], ids[1])
        else:
            self.start_midi()

    def start_midi(self, input_id: int = None, output_id: int = None, queue: Queue = None):
        # Initialise and start Midi thread
        self.midi_device = midi.Midi(input_id, output_id, queue)

        def wait_for_thread():
            # Wait until it finishes
            self.midi_device.join()
            # Restart if needed
            if self.midi_device.try_to_reconnect:
                print("\nTrying to reconnect...")
                ids = self.midi_device.wait_for_reconnect()
                self.start_midi(ids[0], ids[1], queue)

        if not self.first_run:
            print("Reconnected\nEnter to exit")
            self.run()
        self.first_run = False

        waiter = Thread(target=wait_for_thread)
        waiter.start()

    def run(self) -> None:
        functions = self.functions

        self.midi_device.set_queue(self.queue)
        # Import functions
        functions(self.midi_device)

    def close(self):
        self.midi_device.close()
