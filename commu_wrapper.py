from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import yaml
from tqdm import tqdm

from commu.midi_generator.generate_pipeline import MidiGenerationPipeline
from commu_dset import DSET
from commu_file import CommuFile


def make_midis(
        bpm: int,
        key: str,
        time_signature: str,
        num_measures: int,
        genre: str,
        rhythm: str,
        chord_progression: str,
        timestamp: str) -> Dict[str, List[CommuFile]]:
    with open('cfg/inference.yaml') as f:
        cfg = yaml.safe_load(f)

    role_to_midis = defaultdict(list)
     
    for role in tqdm(DSET.get_track_roles()):

        pipeline = MidiGenerationPipeline({'checkpoint_dir': 'ckpt/best.pt'})

        inference_cfg = pipeline.model_initialize_task.inference_cfg
        model = pipeline.model_initialize_task.execute()
    
        min_v, max_v = DSET.sample_min_max_velocity(role)
        instrument = DSET.sample_instrument(role)
        encoded_meta = pipeline.preprocess_task.excecute({
            'track_role': role,

            'bpm': bpm,
            'audio_key': key,
            'time_signature': time_signature,
            'num_measures': num_measures,
            'genre': genre,
            'rhythm': rhythm,
            'chord_progression': DSET.unfold(chord_progression),
            
            'pitch_range': DSET.sample_pitch_range(role),
            'inst': instrument,
            'min_velocity': min_v,
            'max_velocity': max_v,
            
            'top_k': cfg['top_k'],
            'temperature': cfg['temperature'],
            
            'output_dir': f'out/{timestamp}',
            'num_generate': 1})
        input_data = pipeline.preprocess_task.input_data
        meta_info_len = pipeline.preprocess_task.get_meta_info_length()

        pipeline.inference_task(model=model, input_data=input_data, inference_cfg=inference_cfg)
        sequences = pipeline.inference_task.execute(encoded_meta)

        pipeline.postprocess_task(input_data=input_data)
        pipeline.postprocess_task.execute(sequences=sequences, meta_info_len=meta_info_len)

        filepath = f'out/{timestamp}/{role}.mid'
        role_to_midis[role].append(CommuFile(filepath, role, instrument))
        Path(filepath).unlink()

    return role_to_midis
