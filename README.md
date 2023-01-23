# MidiComb

## Setup
1. Clone the repo and `cd` into its directory
    ```
    $ git clone https://github.com/frallebini/midicomb.git
    $ cd midicomb
    ```
1. Create a virtual environment and install the required packages
    ```
    $ python venv .venv
    $ source .venv/bin/activate
    $ pip install -r requirements.txt
    ```
1. Unzip the dataset ([source](https://github.com/POZAlabs/ComMU-code/tree/master/dataset))
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
    └── commu_midi.tar
    ```

## Run
Run [`generate.py`](generate.py) with its required arguments, e.g.
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

Once the program successfully terminates, you will find an [`out`](out) directory with the following structure
```
out
└── <date>_<time>
    ├── metadata.yaml
    └── tune.mid
```
where `metadata.yaml` contains the arguments you passed to `generate.py` and `tune.mid` is the generated midi file.