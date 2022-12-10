from __future__ import annotations

from mido import MidiFile, MidiTrack


class MidiFile_(MidiFile):

    def __init__(self, filename: str | None = None):
        super().__init__(filename)

    def merge(self, other: MidiFile_) -> MidiFile_:
        merged = MidiFile_()
        merged.tracks = self.tracks + other.tracks
        return merged

    def concat(self, other: MidiFile_) -> MidiFile_:
        concatd = MidiFile_()
        time = self.get_track_time(self)
        other_shftd = self.shift(other, time)
        concatd.tracks = self.tracks + other_shftd.tracks
        return concatd

    @staticmethod
    def get_track_time(mid: MidiFile_) -> int:
        if not mid.tracks:
            return 0
        times = []
        for track in mid.tracks:
            times.append(0)
            for message in track:
                times[-1] += message.time
        assert len(set(times)) == 1
        return times[0]

    @classmethod
    def shift(cls, mid: MidiFile_, time: int) -> MidiFile_:
        shifted = cls.clone(mid)
        for track in shifted.tracks:
            for message in track:
                if message.type == 'program_change':
                    message.time += time
        return shifted

    @classmethod
    def clone(cls, mid: MidiFile_) -> MidiFile_:
        cloned = cls()
        for track in mid.tracks:
            cloned.tracks.append(MidiTrack())
            for message in track:
                cloned.tracks[-1].append(message)
        return cloned
