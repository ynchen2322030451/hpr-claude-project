from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import os
from datetime import datetime

# ============================================================
# Curated upload bundle maker for hpr-claude-project
# ============================================================

PROJECT_ROOT = Path.home() / "Projects" / "hpr-claude-project"
OUT_DIR = PROJECT_ROOT / "_upload_bundles"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def add_file(zf: ZipFile, src: Path, arcname: str, manifest: list):
    if not src.exists():
        manifest.append({
            "type": "missing_file",
            "source": str(src),
            "arcname": arcname,
        })
        return

    # macOS .rtfd 等 bundle may be directories
    if src.is_dir():
        manifest.append({
            "type": "dir_passed_as_file",
            "source": str(src),
            "arcname": arcname,
            "note": "treated as directory bundle automatically",
        })
        for p in sorted(src.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(src)
            sub_arcname = str(Path(arcname) / rel)
            zf.write(p, arcname=sub_arcname)
            manifest.append({
                "type": "file",
                "source": str(p),
                "arcname": sub_arcname,
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
        return

    zf.write(src, arcname=arcname)
    manifest.append({
        "type": "file",
        "source": str(src),
        "arcname": arcname,
        "size_bytes": src.stat().st_size,
        "sha256": sha256_file(src),
    })
    
def add_dir(
    zf: ZipFile,
    src_dir: Path,
    arc_prefix: str,
    manifest: list,
    exclude_dirs=None,
    exclude_suffixes=None,
    exclude_names=None,
):
    exclude_dirs = set(exclude_dirs or [])
    exclude_suffixes = set(exclude_suffixes or [])
    exclude_names = set(exclude_names or [])

    if not src_dir.exists():
        manifest.append({
            "type": "missing_dir",
            "source": str(src_dir),
            "arc_prefix": arc_prefix,
        })
        return

    for p in sorted(src_dir.rglob("*")):
        if p.is_dir():
            if p.name in exclude_dirs:
                continue
            # skip traversal by filtering below in file stage
            continue

        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.name in exclude_names:
            continue
        if p.suffix in exclude_suffixes:
            continue

        rel = p.relative_to(src_dir)
        arcname = str(Path(arc_prefix) / rel)
        add_file(zf, p, arcname, manifest)

def make_zip(zip_name: str, items: list, readme_lines: list):
    zip_path = OUT_DIR / zip_name
    manifest = []
    readme_name = "README_bundle.txt"

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        # add bundle README
        readme_content = "\n".join(readme_lines) + "\n"
        zf.writestr(readme_name, readme_content)
        manifest.append({
            "type": "virtual_file",
            "arcname": readme_name,
            "content_preview": readme_lines[:8],
        })

        for item in items:
            kind = item["kind"]
            if kind == "file":
                add_file(
                    zf,
                    PROJECT_ROOT / item["path"],
                    item.get("arcname", item["path"]),
                    manifest
                )
            elif kind == "dir":
                add_dir(
                    zf,
                    PROJECT_ROOT / item["path"],
                    item.get("arc_prefix", item["path"]),
                    manifest,
                    exclude_dirs=item.get("exclude_dirs", []),
                    exclude_suffixes=item.get("exclude_suffixes", []),
                    exclude_names=item.get("exclude_names", []),
                )
            else:
                raise ValueError(f"Unknown item kind: {kind}")

        # add manifest json
        meta = {
            "bundle_name": zip_name,
            "created_at": datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT),
            "n_entries": len(manifest),
            "entries": manifest,
        }
        zf.writestr("MANIFEST.json", json.dumps(meta, indent=2, ensure_ascii=False))

    print(f"[DONE] {zip_path}")
    return zip_path


# ------------------------------------------------------------
# Bundle 1: docs
# ------------------------------------------------------------

docs_items = [
    {"kind": "file", "path": "CLAUDE.md"},
    {"kind": "file", "path": "NEXT_STEPS.md"},
    {"kind": "file", "path": "PROJECT_LOG.md"},
    {"kind": "file", "path": "draft_paper_v2.txt"},
    {"kind": "file", "path": "论文0323.docx"},
    {"kind": "file", "path": "论文0323.pdf"},
    {"kind": "file", "path": "论文0402.docx"},
    {"kind": "dir",
    "path": "Probabilistic neural surrogates for uncertainty-to-risk analysis in coupled multi-physics systems- application to a heat-pipe-cooled reactor.rtfd",
    "arc_prefix": "Probabilistic neural surrogates for uncertainty-to-risk analysis in coupled multi-physics systems- application to a heat-pipe-cooled reactor.rtfd"},
]

docs_readme = [
    "Bundle: upload_bundle_docs.zip",
    "Purpose: paper drafts, project notes, and workflow guidance.",
    "Recommended to upload first when continuing writing/review tasks.",
]

# ------------------------------------------------------------
# Bundle 2: core code
# ------------------------------------------------------------

core_code_items = [
    {"kind": "file", "path": "code/0310/paper_experiment_config.py"},
    {"kind": "file", "path": "code/0310/run_phys_levels_main.py"},
    {"kind": "file", "path": "code/0310/run_phys_levels_main_remain_delta.py"},
    {"kind": "file", "path": "code/0310/run_train_fixed_surrogates.py"},
    {"kind": "file", "path": "code/0310/run_calibration_benchmark.py"},
    {"kind": "file", "path": "code/0310/run_posterior_hf_validation.py"},
    {"kind": "file", "path": "code/0310/run_compare_fixed_models.py"},
    {"kind": "file", "path": "code/0310/run_sobol_analysis.py"},
    {"kind": "file", "path": "code/0310/run_sobol_ci_methods_summary.py"},
    {"kind": "file", "path": "code/0310/run_dataset_sensitivity_analysis.py"},
    {"kind": "file", "path": "code/0310/new_run_forward_uq_analysis.py"},
    {"kind": "file", "path": "code/0310/run_safety_threshold_analysis.py"},
    {"kind": "file", "path": "code/0310/run_inverse_full_vs_reduced_compare.py"},
    {"kind": "file", "path": "code/0310/run_prior_posterior_contraction_summary.py"},
    {"kind": "file", "path": "code/0310/run_export_2d_feasible_region.py"},
    {"kind": "file", "path": "code/0310/run_extreme_scenario_benchmark.py"},
    {"kind": "file", "path": "code/0310/run_ood_multi_feature.py"},
    {"kind": "file", "path": "code/0310/run_speedup_benchmark.py"},
    {"kind": "file", "path": "code/0310/run_practical_speed_benchmark.py"},
    {"kind": "file", "path": "code/0310/plot_forward_uq_and_sobol_figures.py"},
    {"kind": "file", "path": "code/0310/plot_inverse_figures.py"},
    {"kind": "file", "path": "code/0310/plot_2d_inverse_feasible_region_final.py"},
    {"kind": "file", "path": "code/0310/bundle_code_to_txt.py"},
    {"kind": "file", "path": "code/0310/bundle_results_to_txt.py"},
    {"kind": "file", "path": "code/0310/upload_bundle_code.txt"},
    {"kind": "file", "path": "code/0310/upload_bundle_results.txt"},
]

core_code_readme = [
    "Bundle: upload_bundle_code_core.zip",
    "Purpose: canonical 0310 code path for training, UQ, Sobol, inverse, OOD, speed, and plotting.",
    "Excludes __pycache__ and legacy archive directories by design.",
]

# ------------------------------------------------------------
# Bundle 3: core results
# ------------------------------------------------------------

core_results_items = [
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/fixed_split", "arc_prefix": "experiments_phys_levels/fixed_split"},
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/fixed_surrogate_fixed_base", "arc_prefix": "experiments_phys_levels/fixed_surrogate_fixed_base"},
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/fixed_surrogate_fixed_level2", "arc_prefix": "experiments_phys_levels/fixed_surrogate_fixed_level2"},

    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_metrics_table.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_fixed_model_compare_summary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_fixed_model_compare_per_output.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_fixed_model_compare_primary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_forward_uq_summary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_safety_threshold_summary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_sobol_results_with_ci.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_sobol_methods_ready_summary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_sobol_results_ready_top_factors.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_inverse_full_vs_reduced_summary.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_speed_benchmark_detailed.json"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_ood_results.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_posterior_hf_validation_summary_reduced_maintext.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_posterior_hf_validation_per_output_reduced_maintext.csv"},
    {"kind": "file", "path": "code/0310/experiments_phys_levels/paper_posterior_hf_validation_meta_reduced_maintext.json"},
]

core_results_readme = [
    "Bundle: upload_bundle_results_core.zip",
    "Purpose: canonical fixed artifacts and main paper-ready summaries.",
    "This is the most important results bundle for downstream interpretation.",
]

# ------------------------------------------------------------
# Bundle 4: figures
# ------------------------------------------------------------

fig_items = [
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/paper_forward_figures_final", "arc_prefix": "experiments_phys_levels/paper_forward_figures_final"},
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/paper_inverse_figures_final", "arc_prefix": "experiments_phys_levels/paper_inverse_figures_final"},
    {"kind": "dir", "path": "code/0310/experiments_phys_levels/paper_inverse_2d_figures_final", "arc_prefix": "experiments_phys_levels/paper_inverse_2d_figures_final"},
]

fig_readme = [
    "Bundle: upload_bundle_figures_core.zip",
    "Purpose: main paper figures only, not all intermediate plotting outputs.",
]

# ------------------------------------------------------------
# Bundle 5: light data
# ------------------------------------------------------------

light_data_items = [
    {"kind": "file", "path": "code/txt_extract/dataset_v3.csv"},
    {"kind": "file", "path": "code/txt_extract/extracted_data.csv_data_documentation.txt"},
    {"kind": "file", "path": "code/txt_extract/extracted_data.csv_material_properties.csv"},
]

light_data_readme = [
    "Bundle: upload_bundle_data_light.zip",
    "Purpose: essential structured data needed to understand the surrogate dataset.",
    "Does not include the full raw printout archive.",
]

# ------------------------------------------------------------
# Optional heavy inverse bundle
# ------------------------------------------------------------

heavy_inverse_items = [
    {
        "kind": "dir",
        "path": "code/0310/experiments_phys_levels/benchmark_case",
        "arc_prefix": "experiments_phys_levels/benchmark_case",
        "exclude_dirs": [],
        "exclude_suffixes": [],
        "exclude_names": [],
    },
]

heavy_inverse_readme = [
    "Bundle: upload_bundle_inverse_heavy.zip",
    "Purpose: full posterior/prior/predictive benchmark case files.",
    "This bundle can be large. Upload only if detailed inverse-case diagnostics are needed.",
]

# ------------------------------------------------------------
# Build all
# ------------------------------------------------------------

def main():
    made = []
    made.append(make_zip("upload_bundle_docs.zip", docs_items, docs_readme))
    made.append(make_zip("upload_bundle_code_core.zip", core_code_items, core_code_readme))
    made.append(make_zip("upload_bundle_results_core.zip", core_results_items, core_results_readme))
    made.append(make_zip("upload_bundle_figures_core.zip", fig_items, fig_readme))
    made.append(make_zip("upload_bundle_data_light.zip", light_data_items, light_data_readme))

    # Optional heavy pack:
    make_heavy = True
    if make_heavy:
        made.append(make_zip("upload_bundle_inverse_heavy.zip", heavy_inverse_items, heavy_inverse_readme))

    summary = {
        "created_at": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "bundles": [str(p) for p in made],
    }
    with (OUT_DIR / "bundle_index.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n[DONE] All bundles created.")
    print("Output directory:", OUT_DIR)
    for p in made:
        print(" -", p)

if __name__ == "__main__":
    main()