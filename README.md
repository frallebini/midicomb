# MidiComb

MidiComb is a program born as an extension of Hyun et al., 2022 ([paper](https://arxiv.org/abs/2211.09385) | [code](https://github.com/POZAlabs/ComMU-code)) and aimed at tackling the *combinatorial music generation* task. 

See the [project page](https://frallebini.github.io/midicomb-demo) for more information.

## Setup

1. Clone the repo and `cd` into its directory
    ```
    $ git clone https://github.com/frallebini/midicomb.git
    $ cd midicomb
    ```

1. Create a virtual environment and install the required packages
    ```
    $ python -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r requirements.txt
    ```
    Note: the code has been tested with Python `3.8.5`

1. Unzip the dataset
    ```
    $ tar -xvf dataset/commu_midi.tar -C dataset/
    ```
    The resulting directory structure should be
    ```
    dataset
    ├── commu_meta.csv
    ├── commu_midi
    │   ├── train
    │   │   └── raw
    │   │       └── midifiles(.mid)
    │   └── val
    │       └── raw
    │           └── midifiles(.mid)
    ├── commu_midi.tar
    └── README.md
    ```

## Run

Run `generate.py` with its required arguments, e.g.
```
$ python generate.py \
--bpm 130 \
--key aminor \
--time_signature 4/4 \
--num_measures 8 \
--genre newage \
--rhythm standard \
--chord_progression Am-F-C-G-Am-F-C-G
```
You can find a list of legal values for each argument [here](cfg/metadata.yaml).

The above command produces a musical composition by combining samples from the dataset. If you instead want to combine new, generated samples, just add the `--generate_samples` flag, e.g.
```
$ python generate.py \
--bpm 130 \
--key aminor \
--time_signature 4/4 \
--num_measures 8 \
--genre newage \
--rhythm standard \
--chord_progression Am-F-C-G-Am-F-C-G \
--generate_samples
```

Once the program successfully terminates, you will find an `out` directory with the following structure
```
out
└── <date>_<time>
    ├── metadata.yaml
    └── tune.mid
```
where `metadata.yaml` contains the arguments of the corresponding run of `generate.py` and `tune.mid` is the generated MIDI file.