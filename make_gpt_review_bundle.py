"""
打包用于 GPT 审阅的文件。
结构：
  gpt_review_package/
    01_paper/          论文草稿 + LaTeX + PDF
    02_code_core/      主要实验代码
    03_results_csv/    paper_*.csv / paper_*.json（canonical 结果）
    04_figures_svg/    fig*_v1.svg（主图）
    05_project_docs/   项目文档 / CLAUDE.md

输出：gpt_review_package.zip
"""
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path("/Users/yinuo/Projects/hpr-claude-project")
OUT_DIR = ROOT / "_gpt_review_tmp"
BUNDLE_NAME = ROOT / "gpt_review_package.zip"

# ── 清理旧临时目录 ──────────────────────────────────────────────
if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
OUT_DIR.mkdir()

# ── 定义要打包的文件 ────────────────────────────────────────────

def cp(src: Path, dst_dir: Path):
    """Copy src to dst_dir, creating dirs as needed."""
    if not src.exists():
        print(f"  [SKIP-notfound] {src}")
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst_dir / src.name)
    print(f"  [OK] {src.relative_to(ROOT)} -> {dst_dir.relative_to(OUT_DIR)}/")

def cp_tree(src_dir: Path, dst_dir: Path, exts=None, exclude_patterns=None):
    """Recursively copy a directory, optionally filtering by extension."""
    if not src_dir.exists():
        print(f"  [SKIP-notfound-dir] {src_dir}")
        return
    for f in sorted(src_dir.rglob("*")):
        if f.is_dir():
            continue
        if "__pycache__" in str(f) or ".pyc" in f.name:
            continue
        if exclude_patterns and any(p in str(f) for p in exclude_patterns):
            continue
        if exts and f.suffix not in exts:
            continue
        rel = f.relative_to(src_dir)
        dest = dst_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
    print(f"  [OK-tree] {src_dir.relative_to(ROOT)} -> {dst_dir.relative_to(OUT_DIR)}/")

# ────────────────────────────────────────────────────────────────
# 01_paper
# ────────────────────────────────────────────────────────────────
P01 = OUT_DIR / "01_paper"

cp(ROOT / "draft_paper_v2.txt", P01)
cp(ROOT / "sn-article-template" / "sn-article.tex", P01)
cp(ROOT / "sn-article-template" / "sn-article.bbl", P01)
cp(ROOT / "sn-article-template" / "sn-bibliography.bib", P01)
cp(ROOT / "sn-article-template" / "sn-article.pdf", P01)
cp(ROOT / "HPR_surrogate_paper_draft.docx", P01)

# ────────────────────────────────────────────────────────────────
# 02_code_core  (主要实验代码，不含模型权重/大二进制)
# ────────────────────────────────────────────────────────────────
P02 = OUT_DIR / "02_code_core"
CODE = ROOT / "code" / "0310"
EXP04 = CODE / "experiments_0404" / "code"

# config
for f in ["paper_experiment_config.py", "model_registry_0404.py",
          "manifest_utils_0404.py", "run_0404.py"]:
    cp(CODE / f, P02 / "top_level")

# 0404 experiment code (full subtree, .py only)
cp_tree(EXP04, P02 / "experiments_0404_code", exts={".py", ".md"})

# ────────────────────────────────────────────────────────────────
# 03_results_csv  (paper_* canonical summaries from experiments_phys_levels)
# ────────────────────────────────────────────────────────────────
P03 = OUT_DIR / "03_results_csv"
PHL = CODE / "experiments_phys_levels"

# paper_* CSV/JSON from experiments_phys_levels root (not _legacy_ or subdirs)
for f in sorted(PHL.glob("paper_*.csv")) + sorted(PHL.glob("paper_*.json")):
    cp(f, P03 / "phys_levels_canonical")

# fixed surrogate eval results
FIXED_BASE  = PHL / "fixed_surrogate_fixed_base"
FIXED_LVL2  = PHL / "fixed_surrogate_fixed_level2"
FIXED_SPLIT = PHL / "fixed_split"
for d, label in [(FIXED_BASE, "fixed_base"), (FIXED_LVL2, "fixed_level2"), (FIXED_SPLIT, "fixed_split")]:
    cp_tree(d, P03 / f"canonical_{label}", exts={".csv", ".json"})

# 0404 experiment result CSVs (sensitivity, risk, posterior_inference)
EXP04R = CODE / "experiments_0404" / "experiments"
for subdir in ["sensitivity", "risk_propagation", "posterior_inference", "posterior"]:
    d = EXP04R / subdir
    if d.exists():
        cp_tree(d, P03 / f"exp0404_{subdir}",
                exts={".csv", ".json"},
                exclude_patterns=["figures"])

# ────────────────────────────────────────────────────────────────
# 04_figures_svg  (v1 版本主图 SVG；附录 SVG)
# ────────────────────────────────────────────────────────────────
P04 = OUT_DIR / "04_figures_svg"
FIG = ROOT / "figures" / "draft"
for f in sorted(FIG.glob("*_v1.svg")):
    cp(f, P04)
# appendix figures (no v1 suffix)
for f in sorted(FIG.glob("figA*.svg")):
    cp(f, P04 / "appendix")
# also include .txt description files
for f in sorted(FIG.glob("*.txt")):
    cp(f, P04 / "descriptions")

# ────────────────────────────────────────────────────────────────
# 05_project_docs
# ────────────────────────────────────────────────────────────────
P05 = OUT_DIR / "05_project_docs"
cp(ROOT / "CLAUDE.md", P05)
cp(ROOT / "NEXT_STEPS.md", P05)
cp(ROOT / "PROJECT_LOG.md", P05)
cp_tree(CODE / "experiments_0404" / "docs", P05 / "0404_docs", exts={".md", ".txt"})

# ────────────────────────────────────────────────────────────────
# README
# ────────────────────────────────────────────────────────────────
readme = OUT_DIR / "README.txt"
readme.write_text("""\
HPR Surrogate Paper — GPT Review Bundle
========================================
Generated: 2026-04-09

STRUCTURE
---------
01_paper/          论文草稿（txt双语草稿、LaTeX源码、bib、PDF、docx）
02_code_core/      主要实验代码（config、run_0404、experiments_0404所有.py）
03_results_csv/    Canonical结果CSV/JSON，分三组：
                     phys_levels_canonical/  paper_*主结果（旧pipeline）
                     canonical_fixed_*/      fixed_surrogate canonical模型评估
                     exp0404_*/              0404新框架实验结果
04_figures_svg/    主图v1版本SVG + 附录图SVG + 图说明.txt
05_project_docs/   CLAUDE.md、NEXT_STEPS、PROJECT_LOG、0404文档

KEY NOTES FOR REVIEWER
----------------------
- PRIMARY SURROGATE: fixed_surrogate_fixed_level2 (Level 2 / phy-mono / data-mono)
- BASELINE:          fixed_surrogate_fixed_base   (Level 0 / baseline)
- DATASET:           fixed_split/ (n_total=2900, seed=2026)
- PAPER THRESHOLD:   131 MPa (SS316 yield at operating temp)
- SOBOL STATUS:      ⚠ Paper currently uses old phys_levels numbers (k_ref,SS316=0.529).
                     0404 server results (exp0404_sensitivity/) show E_intercept dominant.
                     Numbers need reconciliation before submission.
- POSTERIOR STATUS:  ⚠ Paper says 20 cases / 0.40-0.53 acceptance / >=220 MPa extreme.
                     0404 results show 18 cases / 0.77-0.85 acceptance / 133-194 MPa.
                     Numbers need reconciliation before submission.
""", encoding="utf-8")

# ────────────────────────────────────────────────────────────────
# 打包成 zip
# ────────────────────────────────────────────────────────────────
if BUNDLE_NAME.exists():
    BUNDLE_NAME.unlink()

with zipfile.ZipFile(BUNDLE_NAME, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(OUT_DIR.rglob("*")):
        if f.is_dir():
            continue
        arcname = "gpt_review_package/" + str(f.relative_to(OUT_DIR))
        zf.write(f, arcname)

# 清理临时目录
shutil.rmtree(OUT_DIR)

size_mb = BUNDLE_NAME.stat().st_size / 1024 / 1024
print(f"\n✓ Bundle saved: {BUNDLE_NAME}")
print(f"  Size: {size_mb:.1f} MB")

# 打印内容清单
print("\n=== Bundle contents ===")
with zipfile.ZipFile(BUNDLE_NAME) as zf:
    for name in sorted(zf.namelist()):
        info = zf.getinfo(name)
        print(f"  {name}  ({info.file_size/1024:.0f} KB)")
