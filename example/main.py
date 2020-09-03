from queue import Queue
from threading import Thread

import PySimpleGUI as sg

from midi_macro import MidiMacro, midi
from example import functions

enableGui = False


class Gui:
    def __init__(self, queue: Queue) -> chr:
        super().__init__()

        def pad(n: int):
            return sg.Button(str(n), button_color=('white', 'black'), size=(8, 5), key='pad' + str(n))

        def knob(n: int):
            return sg.Slider(range=(0, 128), default_value=10, orientation='v', size=(4, 30), key='knob' + str(n))

        sg.theme('DarkBlack')
        sg.SetOptions(window_location=(100, 100))
        col1 = [[pad(i) for i in range(5, 9)],
                [pad(i) for i in range(1, 5)]]
        col2 = [[knob(i) for i in range(1, 5)],
                [knob(i) for i in range(5, 9)]]
        layout = [[sg.Column(col1), sg.Column(col2)],
                  [sg.Button('Exit')]]

        self.window = sg.Window('Midi Macro', layout)
        self.window.finalize()
        self.midi_thread = midi_thread = self.MidiThread(self.window, queue)

    class MidiThread(Thread):
        def __init__(self, window, queue):
            super().__init__()
            self.window = window
            self.queue = queue

        def run(self):
            try:
                while True:
                    me = self.queue.get()
                    if me[0] == 1:
                        if me[1] == midi.Midi.Type.CC:
                            self.window['knob' + str(me[2])].update(me[3])
                        elif me[1] == midi.Midi.Type.NOTE_ON:
                            self.window['pad' + str(me[2] - 35)].update(button_color=('black', 'white'))
                        elif me[1] == midi.Midi.Type.NOTE_OFF:
                            self.window['pad' + str(me[2] - 35)].update(button_color=('white', 'black'))
            except KeyboardInterrupt:
                pass

    def run(self) -> None:

        try:
            self.midi_thread.daemon = True
            self.midi_thread.start()
            while True:
                event, values = self.window.read()

                if event in (None, 'Exit'):
                    self.window.close()
                    break
        except KeyboardInterrupt:
            self.window.close()


if __name__ == "__main__":
    queue = Queue()
    m = MidiMacro(functions.Functions, queue, enableGui)
    m.start()

    if enableGui:
        Gui(queue).run()
    else:
        input('Enter to exit')
    m.close()
