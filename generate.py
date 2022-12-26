from commudset import DSET


bpm = 130
key = 'aminor'
time_signature = '4/4'
num_measures = 8
genre = 'newage'
rhythm = 'standard'
chord_progression = 'Am-F-C-G-Am-F-C-G'

midis = DSET.get_samples(
    bpm, 
    key, 
    time_signature, 
    num_measures, 
    genre, 
    rhythm, 
    chord_progression)
