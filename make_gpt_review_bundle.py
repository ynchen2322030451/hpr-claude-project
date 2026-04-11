"""
打包用于 GPT 审阅的文件。
结构：
  gpt_review_package/
    01_paper/          论文草稿 + LaTeX + bib + PDF
    02_code_core/      主要实验代码（config + 0404 framework）
    03_results_csv/    Canonical 结果 CSV/JSON（0404 三条流水线 + phys_levels 兼容）
    04_figures/        主图全版本 SVG + 附录 SVG + 图描述 txt
    05_project_docs/   CLAUDE.md / NEXT_STEPS / PROJECT_LOG / 0404 docs
    06_references/     参考文献 PDF

输出：gpt_review_package.zip

更新日志：
  2026-04-09  初版
  2026-04-11  v2: 增加 risk_propagation_0410、posterior/（非空目录）、
              全版本主图（v1+v2+v3）、参考文献 PDF、更新 README 数字
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
    count = 0
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
        count += 1
    print(f"  [OK-tree] {src_dir.relative_to(ROOT)} -> {dst_dir.relative_to(OUT_DIR)}/ ({count} files)")

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

# figure generation script
cp(ROOT / "figures" / "draft" / "make_figures.py", P02)

# ────────────────────────────────────────────────────────────────
# 03_results_csv  (canonical summaries — 0404 pipeline is primary)
# ────────────────────────────────────────────────────────────────
P03 = OUT_DIR / "03_results_csv"
PHL = CODE / "experiments_phys_levels"

# paper_* CSV/JSON from experiments_phys_levels root (compatibility)
for f in sorted(PHL.glob("paper_*.csv")) + sorted(PHL.glob("paper_*.json")):
    cp(f, P03 / "phys_levels_compat")

# fixed surrogate eval results
FIXED_BASE  = PHL / "fixed_surrogate_fixed_base"
FIXED_LVL2  = PHL / "fixed_surrogate_fixed_level2"
FIXED_SPLIT = PHL / "fixed_split"
for d, label in [(FIXED_BASE, "fixed_base"), (FIXED_LVL2, "fixed_level2"),
                 (FIXED_SPLIT, "fixed_split")]:
    cp_tree(d, P03 / f"canonical_{label}", exts={".csv", ".json"})

# 0404 experiment result CSVs
EXP04R = CODE / "experiments_0404" / "experiments"
for subdir in ["sensitivity", "risk_propagation", "risk_propagation_0410",
               "posterior", "posterior_inference",
               "computational_speedup", "generalization", "physics_consistency"]:
    d = EXP04R / subdir
    if d.exists():
        cp_tree(d, P03 / f"exp0404_{subdir}",
                exts={".csv", ".json"},
                exclude_patterns=["figures", "__pycache__"])

# ────────────────────────────────────────────────────────────────
# 04_figures  (all versions SVG + appendix SVG + descriptions)
# ────────────────────────────────────────────────────────────────
P04 = OUT_DIR / "04_figures"
FIG = ROOT / "figures" / "draft"

# main figures: all versions (v1, v2, v3)
for f in sorted(FIG.glob("fig[1-5]_*.svg")):
    cp(f, P04 / "main")

# appendix figures
for f in sorted(FIG.glob("figA*.svg")):
    cp(f, P04 / "appendix")

# description files
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
# 06_references  (参考文献 PDF，供审稿者核实引用)
# ────────────────────────────────────────────────────────────────
P06 = OUT_DIR / "06_references"
REF_DIR = ROOT / "参考文献"
if REF_DIR.exists():
    cp_tree(REF_DIR, P06, exts={".pdf"})

# ────────────────────────────────────────────────────────────────
# README
# ────────────────────────────────────────────────────────────────
readme = OUT_DIR / "README.txt"
readme.write_text("""\
HPR Surrogate Paper — GPT Review Bundle (v2)
=============================================
Generated: 2026-04-11

STRUCTURE
---------
01_paper/          论文草稿（txt 双语草稿 v2、LaTeX 源码、bib、PDF、docx）
02_code_core/      主要实验代码（config、run_0404、experiments_0404 .py + make_figures.py）
03_results_csv/    Canonical 结果 CSV/JSON:
                     phys_levels_compat/    旧 pipeline paper_* 兼容输出
                     canonical_fixed_*/     fixed_surrogate 模型评估
                     exp0404_sensitivity/   Sobol + Spearman + PRCC（per model）
                     exp0404_risk_propagation/       前向 UQ（per model, σ_k sweep）
                     exp0404_risk_propagation_0410/  mu-only canonical summary
                     exp0404_posterior/     MCMC 后验（benchmark_summary + feasible_region）
04_figures/        主图全版本 SVG（v1/v2/v3）+ 附录 SVG + 图描述 txt
05_project_docs/   CLAUDE.md、NEXT_STEPS、PROJECT_LOG、0404 文档
06_references/     参考文献 PDF（核动力工程、RPHA2025、Energy2025）

KEY FACTS
---------
- PRIMARY MODEL:  data-mono-ineq (heteroscedastic MLP + monotonicity + inequality)
- BASELINE:       baseline (unconstrained heteroscedastic MLP)
- DATASET:        fixed_split/ (n_total=2900, seed=2026, train/val/test=2030/435/435)
- THRESHOLD:      131 MPa (SS316 yield at ~700°C operating temp)

CANONICAL NUMBERS (data-mono-ineq, 0404 framework)
---------------------------------------------------
Accuracy:   stress R²=0.941, RMSE=7.38 MPa, NLL=0.319
Forward UQ: stress mean=162.6 MPa (mu-only, 1σ), std=30.6 MPa
            keff mean=1.1036, std=846 pcm (0.000846)
            stress reduction from coupling: ~42 MPa
            P(σ>131|prior, 1σ)=0.849 (mu-only)
Sobol:      stress: E_intercept S₁=0.586 [0.584,0.588], α_base S₁=0.169
            keff:   α_base S₁=0.771 [0.770,0.772], α_slope S₁=0.198
Posterior:  18 cases, 4 calibrated params, acceptance 0.49-0.59
            high-stress (133-194 MPa): P(σ>131|obs)=0.60-1.0

⚠ KNOWN ISSUES (pre-submission)
--------------------------------
1. draft_paper_v2.txt numbers partially inconsistent with 0404 canonical:
   - Draft says R²=0.929 / stress mean=153 / E_intercept S₁=0.598
   - Canonical says R²=0.941 / stress mean=162.6 / E_intercept S₁=0.586
   → Numbers may come from phy-mono or old phys_levels; need systematic reconciliation.
2. sn-article.tex is STALE — still reflects pre-0410 draft structure and numbers.
3. phy-mono-ineq (author's preferred final model) NOT YET TRAINED.
   All current results are from data-mono-ineq.
4. FigA8 training curves is a PLACEHOLDER — needs real training data.
5. Missing bib entries: Zhang2024 NSE, Chen2025 核动力工程, Chen2025 RPHA, Jansen estimator.
6. Table 1 prior bounds not verified against RPHA PPT.
7. Fig 5C (E_intercept–α_base joint posterior density) not yet created.
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
