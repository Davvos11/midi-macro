import importlib
import importlib.util
import _thread
from threading import Thread

import PySimpleGUI as sg
from queue import Queue

from midi_macro import midi


class MidiMacro(Thread):
    def __init__(self, function_path: str, gui=True) -> None:
        super().__init__()
        self.gui = gui
        self.function_path = function_path

        if self.gui:
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
        spec = importlib.util.spec_from_file_location("functions", self.function_path)
        functions = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(functions)

        # Main loop
        k = None
        q = Queue()
        self.midi_device.set_queue(q)
        try:
            while True:
                print('Starting...')
                # Start midi thread (except on the first loop)
                if k is not None:
                    self.midi_device = midi.Midi(self.midi_io_ids[0], self.midi_io_ids[1], q)
                # Import functions
                functions.Functions(self.midi_device)

                while True:
                    # Wait for keypress or click
                    k = self.main_gui(q) if self.gui else input()
                    if k == 'r':
                        self.midi_device.close()
                        importlib.reload(functions)
                        break
        except KeyboardInterrupt:
            if self.midi_device is not None:
                self.midi_device.close()

    def main_gui(self, queue: Queue) -> chr:
        def pad(n: int):
            return sg.Button(str(n), button_color=('white', 'black'), size=(8, 5), key='pad' + str(n))

        def knob(n: int):
            return sg.Slider(range=(0, 128), default_value=10, orientation='v', size=(4, 30), key='knob' + str(n))

        col1 = [[pad(i) for i in range(5, 9)],
                [pad(i) for i in range(1, 5)]]
        col2 = [[knob(i) for i in range(1, 5)],
                [knob(i) for i in range(5, 9)]]
        layout = [[sg.Column(col1), sg.Column(col2)],
                  [sg.Button('Reload'), sg.Button('Exit')]]

        window = sg.Window('Midi Macro', layout)
        window.finalize()

        def update_on_midi():
            while True:
                me = queue.get()
                if me[0] == 1:
                    if me[1] == midi.Midi.Type.CC:
                        window['knob' + str(me[2])].update(me[3])
                    elif me[1] == midi.Midi.Type.NOTE_ON:
                        window['pad' + str(me[2] - 35)].update(button_color=('black', 'white'))
                    elif me[1] == midi.Midi.Type.NOTE_OFF:
                        window['pad' + str(me[2] - 35)].update(button_color=('white', 'black'))

        _thread.start_new_thread(update_on_midi, ())

        while True:
            event, values = window.read()

            if event in (None, 'Exit'):
                if self.midi_device is not None:
                    self.midi_device.close()
                exit(1)
            elif event == 'Reload':
                window.close()
                return 'r' if event == 'Reload' else ''
