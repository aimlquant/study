#!/usr/bin/env python3
"""Check AAC/video packet timing, not silence or browser playback continuity."""
import argparse
from fractions import Fraction
import json
import math
import subprocess
import sys
import tempfile

MAX_PACKETS = 1_000_000
EPSILON = 1e-6  # ffprobe duration_time/pts_time are printed to microseconds.


def check_timing(streams, packets):
    selected = {}
    for kind in ('video', 'audio'):
        matches = [s for s in streams if s.get('codec_type') == kind]
        if len(matches) != 1:
            raise ValueError(f'exactly one {kind} stream is required')
        selected[kind] = matches[0]
    if selected['audio'].get('codec_name') != 'aac':
        raise ValueError('only AAC audio is supported by this timing contract')
    fps = float(Fraction(selected['video'].get('avg_frame_rate', '0/1')))
    rate = int(selected['audio']['sample_rate'])
    if not math.isfinite(fps) or fps <= 0 or rate <= 0:
        raise ValueError('invalid frame or sample rate')
    summaries = {}
    errors = []
    for kind, stream in selected.items():
        samples = sorted(packets.get(stream['index'], []))
        if len(samples) < 2:
            raise ValueError(f'not enough {kind} packets')
        if any(not math.isfinite(t) or not math.isfinite(d) or d <= 0 for t, d in samples):
            raise ValueError(f'invalid {kind} packet timing')
        gaps = []
        for (t, d), (next_t, _) in zip(samples, samples[1:]):
            delta = next_t - t
            limit = 1.5 * d if kind == 'audio' else 0.5
            if delta <= 0 or delta > limit + EPSILON:
                gaps.append((delta, limit))
        if gaps:
            errors.append(f'{kind}_pts_gap')
        summaries[kind] = dict(first=samples[0][0], end=max(t+d for t, d in samples),
                               packets=len(samples), gap_count=len(gaps),
                               max_pts_interval=max(b[0]-a[0] for a, b in zip(samples, samples[1:])))
    tolerance = max(1 / fps, 1024 / rate)
    start_diff = abs(summaries['video']['first'] - summaries['audio']['first'])
    end_diff = abs(summaries['video']['end'] - summaries['audio']['end'])
    if start_diff > tolerance + EPSILON:
        errors.append('start_mismatch')
    if end_diff > 2 * tolerance + EPSILON:
        errors.append('end_mismatch')
    return dict(file_timing_pass=not errors, errors=errors, start_diff=start_diff,
                end_diff=end_diff, start_limit=tolerance, end_limit=2*tolerance,
                streams=summaries, playback_verified=False, silence_checked=False)


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', path],
                            capture_output=True, text=True, timeout=30, check=True)
    streams = json.loads(result.stdout)['streams']
    # Spool output on disk, avoiding an unbounded subprocess capture in memory.
    with tempfile.TemporaryFile(mode='w+t') as output:
        subprocess.run(['ffprobe', '-v', 'error', '-show_packets', '-show_entries',
                        'packet=stream_index,pts_time,duration_time', '-of',
                        'compact=p=0:nk=0', path], stdout=output, stderr=subprocess.DEVNULL,
                       timeout=120, check=True)
        output.seek(0)
        packets = {}
        for count, line in enumerate(output, 1):
            if count > MAX_PACKETS:
                raise ValueError('packet limit exceeded; split the input for inspection')
            if not line.strip():
                continue
            fields = dict(part.split('=', 1) for part in line.strip().split('|') if '=' in part)
            if 'stream_index' not in fields:
                continue
            index = int(fields['stream_index'])
            packets.setdefault(index, []).append((float(fields['pts_time']), float(fields['duration_time'])))
    return check_timing(streams, packets)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video')
    args = parser.parse_args()
    try:
        result = probe(args.video)
    except (ValueError, KeyError, ZeroDivisionError, OSError, subprocess.SubprocessError):
        # Avoid echoing private media paths or ffprobe command lines.
        print(json.dumps(dict(file_timing_pass=False, errors=['probe_or_timing_invalid'],
                              playback_verified=False, silence_checked=False)))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['file_timing_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
