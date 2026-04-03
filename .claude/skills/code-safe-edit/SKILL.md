---
name: code-safe-edit
# Code Safe Edit Skill

description: use this skill whenever creating modifying or reviewing python code in this project
---
The goal is to produce code that is:
- compatible with the current project structure
- minimally invasive
- reproducible
- directly runnable
- unlikely to corrupt canonical results

---

## Step 1: Read before writing

Before changing code, read all of the following:

1. the file to edit
2. the project config file(s):
   - paper_experiment_config.py
   - CLAUDE.md
   - NEXT_STEPS.md
3. directly imported modules
4. downstream consumer scripts
5. if relevant, existing output files or split metadata

Do not skip this step.

---

## Step 2: Build a compatibility checklist

Explicitly identify:

- input columns
- output columns
- tensor dimensions
- iter1 / iter2 alignment assumptions
- config keys used
- expected checkpoint paths
- expected scaler paths
- expected split paths
- output filenames
- output directories
- whether outputs are canonical or compatibility-only
- whether the script depends on fixed split or on an on-the-fly split
- whether rerun may overwrite existing results

If any item is unclear, mark:
【待核实】

---

## Step 3: Prefer minimal diffs

Default policy:
- reuse existing helper functions
- reuse existing config paths
- preserve naming conventions
- keep old behavior unless the user explicitly wants a behavior change
- avoid rewriting whole files when a small patch is enough

Do not introduce:
- duplicate pipelines
- parallel config systems
- silent path changes
- incompatible output naming

---

## Step 4: Validate before declaring success

At minimum verify:

1. syntax passes
2. imported names exist
3. config names exist
4. index / shape logic is consistent
5. output filenames are explicit
6. overwrite risk is stated

For shape-sensitive scientific code, also check:
- whether iter1 and iter2 dimensions match
- whether DELTA_PAIRS is needed instead of naive subtraction
- whether current dataset size matches frozen split metadata

---

## Step 5: Always report in this structure

### What changed
- concise summary of code edits

### Files read
- config, dependency, and downstream files used for compatibility inference

### Inputs
- required inputs for running the script

### Outputs
- files and directories written

### Overwrite risk
- explicit warning or confirmation

### Run command
- exact runnable command

### Remaining uncertainty
- mark as 【待核实】 if anything was not verified

---

## Project-specific rules

### Canonical artifacts
Prefer these as the primary truth source:
- fixed_surrogate_fixed_base/
- fixed_surrogate_fixed_level2/
- fixed_split/

### Compatibility-only outputs
Treat these as legacy compatibility outputs unless user says otherwise:
- OUT_DIR/metrics_level*.json
- OUT_DIR/test_predictions_level*.json
- OUT_DIR/paper_metrics_table.csv

### Split consistency
If:
- split_meta n_total != current dataset length
or
- split_meta csv_path does not match current dataset
then stop and report mismatch.
Do not continue.

### Iteration pairing
If iter1 and iter2 output dimensions differ:
- do not use naive vector subtraction
- use explicit DELTA_PAIRS or equivalent mapping

### Benchmark consistency
If posterior benchmark files depend on a fixed split:
- verify split consistency before validation
- do not silently mix old benchmark files with new split/model
- note: benchmark cases come from the calibration pool (split["X_cal"]),
  NOT from the surrogate test split (fixed_split/test_indices.csv)

### Rerun isolation
When rerunning historical scripts:
- prefer new OUT_DIR
or
- tagged output filenames
or
- archived old results first

Never recommend rerunning into the same directory without warning.
