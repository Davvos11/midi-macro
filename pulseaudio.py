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

    def mute_default_output(self, mute: bool = None) -> None:
        default_output = 0
        # TODO get actual default
        if mute is None:
            mute = not self.pulse.sink_info(default_output).mute

        if mute:
            self.pulse.sink_mute(default_output, True)
        else:
            self.pulse.sink_mute(default_output, False)

    def mute_default_input(self, mute: bool = None) -> None:
        default_input = 1
        if mute is None:
            mute = not self.pulse.source_info(default_input).mute

        if mute:
            self.pulse.source_mute(default_input, True)
        else:
            self.pulse.source_mute(default_input, False)
