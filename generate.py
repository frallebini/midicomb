from commudset import DSET
from commufile import CommuFile


bpm = 130
key = 'aminor'
time_signature = '4/4'
num_measures = 8
genre = 'newage'
rhythm = 'standard'
chord_progression = 'Am-F-C-G-Am-F-C-G'

for track_role in DSET.get_track_roles():
    try:
        sample = DSET.sample(
            track_role, 
            bpm, 
            key, 
            time_signature, 
            num_measures, 
            genre, 
            rhythm, 
            chord_progression)
    except: 
        continue
    midi = CommuFile(
        sample.id.item(), 
        sample.split.item(), 
        sample.track_role.item(), 
        sample.instrument.item())
    print(midi.get_track_time())
    midi.save(f'out/{sample.track_role.item()}.mid')
