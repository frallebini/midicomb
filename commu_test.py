from mido import MidiFile, MidiTrack, merge_tracks


instrument_to_program = {
    'string_ensemble': 48,
    'acoustic_piano': 0,
    'string_violin': 40
}


def move_meta(mid: MidiFile) -> None:
    assert len(mid.tracks) == 2
    assert [msg.is_meta for msg in mid.tracks[0]]
    mid.tracks = [merge_tracks(mid.tracks)]


def set_program(mid: MidiFile, program: int) -> None:
    for track in mid.tracks:
        for message in track:
            if message.type == 'program_change':
                message.program = program


def set_channel(mid: MidiFile, channel: int) -> None:
    for track in mid.tracks:
        for message in track:
            if message.type == 'program_change' or message.type == 'note_on':
                message.channel = channel


def set_name(mid: MidiFile, name: str) -> None:
    mid.tracks[0].name = name         


def get_total_time(mid: MidiFile) -> int:
    time = 0
    for track in mid.tracks:
        for message in track:
            time += message.time
    return time


def shift(mid: MidiFile, time: int) -> None:
    for track in mid.tracks:
        for message in track:
            if message.type == 'program_change':
                message.time += time


def clone(mid: MidiFile) -> MidiFile:
    cloned = MidiFile()
    for track in mid.tracks:
        cloned.tracks.append(MidiTrack())
        for message in track:
            cloned.tracks[-1].append(message)
    return cloned


mid1 = MidiFile('dataset/commu_midi/train/raw/commu00001.mid')
move_meta(mid1)
set_program(mid1, instrument_to_program['string_ensemble'])
set_name(mid1, 'main_melody')

mid2 = MidiFile('dataset/commu_midi/train/raw/commu00002.mid')
move_meta(mid2)
set_program(mid2, instrument_to_program['acoustic_piano'])
set_channel(mid2, 1)
set_name(mid2, 'accompaniment')

mid3 = MidiFile('dataset/commu_midi/train/raw/commu00003.mid')
move_meta(mid3)
set_program(mid3, instrument_to_program['string_violin'])
set_channel(mid3, 2)
set_name(mid3, 'riff')

time1 = get_total_time(mid1)
time2 = get_total_time(mid2)

assert time1 == time2
shift(mid3, time1)

merged_mid = MidiFile()
merged_mid.tracks = mid1.tracks + mid2.tracks + mid3.tracks
merged_mid.save('merged.mid')
# with open('merged.txt', 'w') as f:
#     f.write(str(merged_mid))
