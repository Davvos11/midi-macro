import pulsectl


class PulseControl:
    def __init__(self, name: str = "Python control"):
        self.pulse = pulsectl.Pulse(name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pulse.close()

    def get_stream_list(self) -> [pulsectl.PulseSinkInfo]:
        return self.pulse.sink_input_list()

    def get_stream(self, name: str) -> pulsectl.PulseSinkInfo:
        for stream in self.get_stream_list():
            if stream.name == name:
                return stream

    def set_stream_volume(self, name: str, level: float) -> None:
        stream = self.get_stream(name)
        if stream is not None:
            self.pulse.volume_set_all_chans(stream, level)
