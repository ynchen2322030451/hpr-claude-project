#!/usr/bin/env python3
"""Parse `paper_speed_benchmark_detailed.json` into canonical speed numbers.

The detailed benchmark JSON contains
  - 3 high-fidelity (OpenMC + FEniCS) runs whose `returncode` is 1 because of
    a known MPI_FINALIZE teardown bug; the scientific computation completes
    successfully and prints `every thing is done, and use time is X sec` on
    the final line of stdout
  - 5 neural-surrogate runs of `run_speedup_benchmark.py`, each emitting a
    JSON blob with `single_sample_latency_sec` and
    `per_sample_batch_latency_sec`
  - `comparison.hf_mean_sec` is `null` because the summary statistic filters
    on returncode

This script ignores returncode, extracts the real HF `use time`, averages the
three runs to obtain the canonical HF baseline, averages surrogate latencies
across five runs, and recomputes every speedup against the real baseline.
The embedded `high_fidelity_seconds_per_case: 3600` field inside each surrogate
stdout is a hand-written placeholder and is explicitly NOT used.
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IN_PATH  = ROOT / "results" / "speed" / "paper_speed_benchmark_detailed.json"
OUT_PATH = ROOT / "results" / "speed" / "hf_runtime_final.json"

USE_TIME_RE = re.compile(r"use time is\s+([\d.]+)\s*sec")


def extract_hf_use_times(hf_runs):
    out = []
    for r in hf_runs:
        m = USE_TIME_RE.search(r["stdout"])
        if not m:
            raise RuntimeError(f"run {r['run_id']} missing 'use time' line")
        out.append({
            "run_id":          r["run_id"],
            "returncode":      r["returncode"],
            "wall_clock_sec":  r["wall_clock_sec"],
            "use_time_sec":    float(m.group(1)),
        })
    return out


def extract_ns_latencies(ns_runs):
    out = []
    for r in ns_runs:
        s = r["stdout"]
        i, j = s.find("{"), s.rfind("}")
        if i < 0 or j <= i:
            raise RuntimeError(f"run {r['run_id']} has no JSON blob in stdout")
        obj = json.loads(s[i:j + 1])
        out.append({
            "run_id":                     r["run_id"],
            "wall_clock_sec":             r["wall_clock_sec"],
            "single_sample_latency_sec":  obj["single_sample_latency_sec"],
            "per_sample_batch_latency_sec": obj["per_sample_batch_latency_sec"],
            "batch_size":                 obj.get("batch_size"),
            "device":                     obj.get("device"),
            "embedded_hf_placeholder_sec": obj.get("high_fidelity_seconds_per_case"),
        })
    return out


def main() -> None:
    with open(IN_PATH) as f:
        d = json.load(f)

    hf_runs = extract_hf_use_times(d["high_fidelity"]["runs"])
    ns_runs = extract_ns_latencies(d["neural_surrogate"]["runs"])

    hf_use_time = [r["use_time_sec"]   for r in hf_runs]
    hf_wall     = [r["wall_clock_sec"] for r in hf_runs]

    single_lat = [r["single_sample_latency_sec"]     for r in ns_runs]
    batch_lat  = [r["per_sample_batch_latency_sec"]  for r in ns_runs]
    ns_wall    = [r["wall_clock_sec"]                for r in ns_runs]

    hf_mean      = statistics.mean(hf_use_time)
    hf_wall_mean = statistics.mean(hf_wall)
    single_mean  = statistics.mean(single_lat)
    batch_mean   = statistics.mean(batch_lat)
    ns_wall_mean = statistics.mean(ns_wall)

    out = {
        "source":        str(IN_PATH.relative_to(ROOT)),
        "compiled_by":   "0411/code/postproc/parse_speed_benchmark.py",
        "compiled_on":   "2026-04-11",
        "hardware":      d["meta"].get("system", {}),
        "notes": [
            "HF returncode is 1 for all 3 runs because of a known MPI_FINALIZE "
            "teardown bug; all 3 runs completed their scientific computation and "
            "printed a final 'use time X sec' line. 'use time' is the authoritative "
            "baseline; wall clock is reported for reference only.",
            "The field `high_fidelity_seconds_per_case: 3600` embedded in each "
            "neural-surrogate stdout is a hand-written placeholder and is NOT used "
            "here. All speedups reported in this file are recomputed against the "
            "real measured HF baseline.",
        ],
        "hf": {
            "n_runs":                 len(hf_runs),
            "use_time_sec_per_run":   hf_use_time,
            "wall_clock_sec_per_run": hf_wall,
            "use_time_mean_sec":      hf_mean,
            "use_time_std_sec":       statistics.stdev(hf_use_time) if len(hf_use_time) > 1 else 0.0,
            "wall_clock_mean_sec":    hf_wall_mean,
            "teardown_overhead_sec":  hf_wall_mean - hf_mean,
            "runs":                   hf_runs,
            "canonical_sec":          round(hf_mean),
        },
        "surrogate": {
            "n_runs":                           len(ns_runs),
            "single_sample_latency_sec_mean":   single_mean,
            "single_sample_latency_sec_std":    statistics.stdev(single_lat),
            "per_sample_batch_latency_sec_mean": batch_mean,
            "per_sample_batch_latency_sec_std": statistics.stdev(batch_lat),
            "end_to_end_script_mean_sec":       ns_wall_mean,
            "end_to_end_script_std_sec":        statistics.stdev(ns_wall),
            "batch_size":                       ns_runs[0]["batch_size"],
            "device":                           ns_runs[0]["device"],
            "runs":                             ns_runs,
        },
        "speedups_vs_hf_usetime": {
            "single_sample_GPU":  hf_mean / single_mean,
            "batched_per_sample": hf_mean / batch_mean,
            "end_to_end_script":  hf_mean / ns_wall_mean,
        },
    }

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"HF use-time per run    : {hf_use_time}")
    print(f"HF use-time mean (canon): {hf_mean:.2f} s  (rounded {round(hf_mean)} s)")
    print(f"HF wall-clock mean      : {hf_wall_mean:.2f} s  "
          f"(teardown {hf_wall_mean - hf_mean:+.2f} s)")
    print(f"Surrogate single-sample : {single_mean:.4e} s  "
          f"(speedup {hf_mean / single_mean:.3e})")
    print(f"Surrogate batched       : {batch_mean:.4e} s  "
          f"(speedup {hf_mean / batch_mean:.3e})")
    print(f"Surrogate end-to-end    : {ns_wall_mean:.3f} s  "
          f"(speedup {hf_mean / ns_wall_mean:.1f})")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
