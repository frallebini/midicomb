from datetime import datetime
from pathlib import Path

from hesiod import hcfg, hmain

from commudset import DSET
from midicomb import MidiComb


@hmain(base_cfg_dir='cfg/base', run_cfg_file='cfg/generate.yaml', create_out_dir=False)
def main() -> None:
    now = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    Path(f'out/{now}').mkdir(parents=True)

    role_to_midis = DSET.sample_midis(
        hcfg('bpm', int), 
        hcfg('key', str), 
        hcfg('time_signature', str), 
        hcfg('num_measures', int), 
        hcfg('genre', str), 
        hcfg('rhythm', str), 
        hcfg('chord_progression', str),
        now)

    MidiComb(role_to_midis, now).solve()

if __name__ == "__main__":
    main()
