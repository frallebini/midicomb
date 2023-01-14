import itertools
from collections import defaultdict, namedtuple
from datetime import datetime
from pathlib import Path

from ortools.sat.python import cp_model

from commudset import DSET
from commufile import merge


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        super().__init__()
        self.__variables = variables

    def on_solution_callback(self):
        for v in self.__variables:
            print(f'{v}={self.Value(v)}')
        print()


bpm = 130
key = 'aminor'
time_signature = '4/4'
num_measures = 8
genre = 'newage'
rhythm = 'standard'
chord_progression = 'Am-F-C-G-Am-F-C-G'
debug = True

now = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
Path(f'out/{now}').mkdir(parents=True)

role_to_midis = DSET.sample_midis(
    bpm, 
    key, 
    time_signature, 
    num_measures, 
    genre, 
    rhythm, 
    chord_progression,
    now)

role_to_durations = {role: [midi.duration for midi in midis] for role, midis in role_to_midis.items()}
horizon = sum(duration for durations in role_to_durations.values() for duration in durations)
model = cp_model.CpModel()

Track = namedtuple('Track', 'start end interval is_present')
role_to_tracks = defaultdict(list)
role_to_tracks_opt = defaultdict(list)
role_to_intervals = defaultdict(list)
role_to_repeats = defaultdict(list)

for role, durations in role_to_durations.items():
    for i, duration in enumerate(durations):
        suffix = f'{role}_{i}'
        
        start = model.NewIntVar(0, horizon, f'start_{suffix}')
        end = model.NewIntVar(0, horizon, f'end_{suffix}')
        is_present = model.NewBoolVar(f'is_present_{suffix}')
        interval = model.NewIntervalVar(start, duration, end, f'interval_{suffix}')

        start_opt = model.NewIntVar(0, horizon, f'start_opt_{suffix}')
        end_opt = model.NewIntVar(0, horizon, f'end_opt_{suffix}')
        is_present_opt = model.NewBoolVar(f'is_present_opt_{suffix}')
        interval_opt = model.NewOptionalIntervalVar(
            start_opt, duration, end_opt, 
            is_present_opt, f'interval_opt_{suffix}')

        role_to_tracks[role].append(Track(start, end, interval, is_present))
        role_to_tracks_opt[role].append(Track(start_opt, end_opt, interval_opt, is_present_opt))

        role_to_intervals[role].append(interval)
        role_to_intervals[role].append(interval_opt)

        role_to_repeats[role].append(is_present_opt)

        model.Add(is_present == 1)  # play at least one sample for each track role
        if role == 'riff':
            model.Add(is_present_opt == 0)  # do not repeat riffs

tracks = \
    [track for tracks in role_to_tracks.values() for track in tracks] + \
    [track for tracks in role_to_tracks_opt.values() for track in tracks]
intervals = [interval for intervals in role_to_intervals.values() for interval in intervals]
repeats = [repeat for repeats in role_to_repeats.values() for repeat in repeats]

# samples with same track role do not overlap
for role in role_to_intervals.keys():
    model.AddNoOverlap(role_to_intervals[role])

# play no more than x samples at the same time, where x depends on the track role
role_to_demand = {
    'main_melody': 3,
    'sub_melody': 3,
    'riff': 3,
    'accompaniment': 2,
    'pad': 1,
    'bass': 1
}
demands = [role_to_demand[role] for role, intervals in role_to_intervals.items() for _ in intervals]
model.AddCumulative(intervals, demands, 6)

# if two samples overlap, make them start at the same time
TrackPairInfo = namedtuple('TrackPairInfo', 't1_before_t2 t2_before_t1 overlap')
pairs_to_info = {}
track_to_overlaps = defaultdict(list)
for t1, t2 in itertools.combinations(tracks, 2):
    name1 = t1.start.Name().replace('start_', '')
    name2 = t2.start.Name().replace('start_', '')
    
    t1_before_t2 = model.NewBoolVar(f'{name1}_before_{name2}')
    t2_before_t1 = model.NewBoolVar(f'{name2}_before_{name1}')
    overlap = model.NewBoolVar(f'overlap_{name1}_{name2}')
    
    model.Add(t1.end <= t2.start).OnlyEnforceIf(t1_before_t2)
    model.Add(t1.end > t2.start).OnlyEnforceIf(t1_before_t2.Not())
    model.Add(t2.end <= t1.start).OnlyEnforceIf(t2_before_t1)
    model.Add(t2.end > t1.start).OnlyEnforceIf(t2_before_t1.Not())

    model.AddBoolOr([t1_before_t2, t2_before_t1, t1.is_present.Not(), t2.is_present.Not()]).OnlyEnforceIf(overlap.Not())
    model.AddBoolAnd([t1_before_t2.Not(), t2_before_t1.Not(), t1.is_present, t2.is_present]).OnlyEnforceIf(overlap)
    model.Add(t1.start == t2.start).OnlyEnforceIf(overlap)

    pairs_to_info[t1, t2] = TrackPairInfo(t1_before_t2, t2_before_t1, overlap)
    track_to_overlaps[t1].append(overlap)
    track_to_overlaps[t2].append(overlap)

# if a sample is played on its own, leave some silence before it begins and after it ends
# (it sounds more dramatic and less out of place)
alones = []
for track in tracks:
    alone = model.NewBoolVar(f'alone_{track.start.Name().replace("start_", "")}')
    model.AddBoolAnd([var.Not() for var in track_to_overlaps[track]]).OnlyEnforceIf(alone)
    model.AddBoolOr(track_to_overlaps[track]).OnlyEnforceIf(alone.Not())

    for (t1, t2), info in pairs_to_info.items():
        if t1 is track or t2 is track:
            model.Add(t2.start >= t1.end + 4000).OnlyEnforceIf([info.t1_before_t2, alone])
            model.Add(t1.start >= t2.end + 4000).OnlyEnforceIf([info.t2_before_t1, alone])
            
    alones.append(alone)

# repeat half of the samples
model.Add(sum(repeats) == len(repeats)//2)

makespan = model.NewIntVar(0, horizon, 'makespan')
model.AddMaxEquality(makespan, [track.end for track in tracks])
model.Minimize(makespan)

solver = cp_model.CpSolver()
printer = SolutionPrinter(
    [track.is_present for track in tracks] +
    [track.start for track in tracks] + 
    [track.end for track in tracks] + 
    alones + [makespan])
status = solver.Solve(model, printer if debug else None)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    shifted_midis = []
    for role, midis in role_to_midis.items():
        for i, midi in enumerate(midis):
            shifted_midis.append(midi.shift(solver.Value(role_to_tracks[role][i].start)))
            if solver.Value(role_to_repeats[role][i]):
                shifted_midis.append(midi.shift(solver.Value(role_to_tracks_opt[role][i].start)))
    merged = merge(shifted_midis)
    merged.save(f'out/{now}/merged.mid')

elif status == cp_model.INFEASIBLE:
    print(f'No solution found: the problem was proven infeasible')
elif status == cp_model.MODEL_INVALID:
    print('No solution found: invalid model')
else:
    print('No solution found: the solver was stopped before reaching an endpoint')
