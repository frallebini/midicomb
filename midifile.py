from __future__ import annotations

import copy

from mido import MidiFile, MidiTrack


class MidiFile_(MidiFile):

    def __init__(self, filename: str | None = None) -> None:
        super().__init__(filename)
        
    @classmethod
    def merge(cls, midis: list[MidiFile_]) -> MidiFile_:
        merged = cls()
        merged.tracks = [track for midi in midis for track in midi.tracks]
        return merged

    def get_track_time(self) -> int:
        if not self.tracks:
            return 0
        times = []
        for track in self.tracks:
            times.append(0)
            for message in track:
                times[-1] += message.time
        assert len(set(times)) == 1
        return times[0]

    def shift(self, time: int) -> MidiFile_:
        shifted = copy.deepcopy(self)
        for track in shifted.tracks:
            for message in track:
                if message.type == 'program_change':
                    message.time += time
        return shifted
