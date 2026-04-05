import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/yinuo/Projects/hpr-claude-project/code/0310")

CODE_OUT = ROOT / "upload_bundle_code_0404.txt"
RESULT_OUT = ROOT / "upload_bundle_results_0404.txt"


# ============================================================
# 1. 代码与文档：精选主线
# ============================================================

CODE_GROUPS = {
    "A_0404_core_framework": [
        "experiments_0404/code/run_0404.py",
        "experiments_0404/code/_path_setup.py",
        "experiments_0404/code/SERVER_SETUP.md",
        "experiments_0404/code/config/experiment_config_0404.py",
        "experiments_0404/code/config/model_registry_0404.py",
        "experiments_0404/code/config/manifest_utils_0404.py",
    ],
    "B_0404_training_and_eval": [
        "experiments_0404/code/training/run_train_0404.py",
        "experiments_0404/code/evaluation/run_eval_0404.py",
    ],
    "C_0404_experiments": [
        "experiments_0404/code/experiments/run_risk_propagation_0404.py",
        "experiments_0404/code/experiments/run_sensitivity_0404.py",
        "experiments_0404/code/experiments/run_posterior_0404.py",
        "experiments_0404/code/experiments/run_generalization_0404.py",
        "experiments_0404/code/experiments/run_physics_consistency_0404.py",
    ],
    "D_0404_figures_and_docs": [
        "experiments_0404/code/figures/run_figures_0404.py",
        "experiments_0404/docs/STATUS_MATRIX_0404.md",
        "experiments_0404/docs/RESULT_LINEAGE_AUDIT.md",
        "experiments_0404/docs/0404_refactor_summary.md",
        "experiments_0404/docs/AN_completeness_audit.md",
        "experiments_0404/docs/physics_prior_design.md",
        "experiments_0404/docs/repeated_split_rationale.md",
        "experiments_0404/docs/sensitivity_methods_comparison.md",
        "experiments_0404/docs/todo_list.md",
        "experiments_0404/docs/open_questions.md",
        "experiments_0404/docs/issue_tracker.md",
    ],
    "E_legacy_core_reference": [
        "paper_experiment_config.py",
        "run_phys_levels_main.py",
        "run_train_fixed_surrogates.py",
        "run_forward_uq_analysis.py",
        "run_sobol_analysis.py",
        "run_safety_threshold_analysis.py",
        "run_inverse_benchmark_fixed_surrogate.py",
        "run_inverse_diagnostics.py",
        "run_prior_posterior_contraction_summary.py",
        "run_compare_fixed_models.py",
        "run_posterior_hf_validation.py",
        "run_extreme_scenario_benchmark.py",
    ],
}

CODE_PURPOSE = {
    "experiments_0404/code/run_0404.py": "0404 新框架总控入口。",
    "experiments_0404/code/_path_setup.py": "0404 路径与导入组织。",
    "experiments_0404/code/SERVER_SETUP.md": "服务器环境配置说明。",
    "experiments_0404/code/config/experiment_config_0404.py": "0404 实验总配置。",
    "experiments_0404/code/config/model_registry_0404.py": "0404 模型注册表定义。",
    "experiments_0404/code/config/manifest_utils_0404.py": "0404 manifest/运行记录工具。",
    "experiments_0404/code/training/run_train_0404.py": "0404 统一训练主脚本。",
    "experiments_0404/code/evaluation/run_eval_0404.py": "0404 统一评估主脚本。",
    "experiments_0404/code/experiments/run_risk_propagation_0404.py": "0404 风险传播/扰动实验。",
    "experiments_0404/code/experiments/run_sensitivity_0404.py": "0404 敏感性分析主脚本。",
    "experiments_0404/code/experiments/run_posterior_0404.py": "0404 逆问题/后验实验主脚本。",
    "experiments_0404/code/experiments/run_generalization_0404.py": "0404 泛化/OOD类实验。",
    "experiments_0404/code/experiments/run_physics_consistency_0404.py": "0404 物理一致性/偏导数相关实验。",
    "experiments_0404/code/figures/run_figures_0404.py": "0404 图表统一生成脚本。",
    "experiments_0404/docs/STATUS_MATRIX_0404.md": "STATUS_MATRIX_0404（新建）：按四级标注所有模块的验证状态。",
    "experiments_0404/docs/RESULT_LINEAGE_AUDIT.md": "RESULT_LINEAGE_AUDIT（新建）：记录 R² 异常根因及数据作废/修正结论。",
    "experiments_0404/docs/0404_refactor_summary.md": "0404 重构总说明。",
    "experiments_0404/docs/AN_completeness_audit.md": "完整性审计文档。",
    "experiments_0404/docs/physics_prior_design.md": "物理先验与loss设计说明。",
    "experiments_0404/docs/repeated_split_rationale.md": "重复划分方案说明。",
    "experiments_0404/docs/sensitivity_methods_comparison.md": "敏感性分析方法比较说明。",
    "experiments_0404/docs/todo_list.md": "待办清单。",
    "experiments_0404/docs/open_questions.md": "待确认问题。",
    "experiments_0404/docs/issue_tracker.md": "当前问题追踪。",
    "paper_experiment_config.py": "旧主线实验配置。",
    "run_phys_levels_main.py": "旧主线训练与评估核心代码。",
    "run_train_fixed_surrogates.py": "fixed split 基线/正则模型统一训练脚本。",
    "run_forward_uq_analysis.py": "旧主线正向传播脚本。",
    "run_sobol_analysis.py": "旧主线 Sobol 脚本。",
    "run_safety_threshold_analysis.py": "旧主线阈值风险脚本。",
    "run_inverse_benchmark_fixed_surrogate.py": "旧主线 inverse benchmark。",
    "run_inverse_diagnostics.py": "旧主线 inverse 诊断。",
    "run_prior_posterior_contraction_summary.py": "旧主线 posterior contraction 汇总。",
    "run_compare_fixed_models.py": "fixed 模型比较脚本。",
    "run_posterior_hf_validation.py": "HF posterior validation 脚本。",
    "run_extreme_scenario_benchmark.py": "极端高应力 case 的 inverse benchmark。",
}


# ============================================================
# 2. 结果：精选主线
# ============================================================

RESULT_GROUPS = {
    "A_0404_registry_and_docs": [
        "experiments_0404/0404_model_registry.csv",
        "experiments_0404/0404_experiment_registry.csv",
        "experiments_0404/docs/STATUS_MATRIX_0404.md",
        "experiments_0404/docs/RESULT_LINEAGE_AUDIT.md",
        "experiments_0404/docs/0404_refactor_summary.md",
        "experiments_0404/docs/AN_completeness_audit.md",
        "experiments_0404/docs/physics_prior_design.md",
        "experiments_0404/docs/repeated_split_rationale.md",
        "experiments_0404/docs/sensitivity_methods_comparison.md",
        "experiments_0404/docs/todo_list.md",
        "experiments_0404/docs/open_questions.md",
        "experiments_0404/docs/issue_tracker.md",
    ],
    "B_legacy_model_performance": [
        "experiments_phys_levels/paper_metrics_table.csv",
        "experiments_phys_levels/paper_fixed_model_compare_summary.csv",
        "experiments_phys_levels/paper_fixed_model_compare_primary.csv",
        "experiments_phys_levels/paper_fixed_model_compare_per_output.csv",
        "experiments_phys_levels/paper_focus_metrics_level0.csv",
        "experiments_phys_levels/paper_focus_metrics_level2.csv",
        "experiments_phys_levels/paper_metrics_per_dim_level0.csv",
        "experiments_phys_levels/paper_metrics_per_dim_level2.csv",
    ],
    "C_legacy_forward_risk_sensitivity": [
        "experiments_phys_levels/paper_forward_uq_summary.csv",
        "experiments_phys_levels/paper_safety_threshold_summary.csv",
        "experiments_phys_levels/paper_sobol_results.csv",
        "experiments_phys_levels/paper_sobol_results_with_ci.csv",
        "experiments_phys_levels/paper_sobol_methods_ready_summary.csv",
        "experiments_phys_levels/paper_sobol_results_ready_top_factors.csv",
        "experiments_phys_levels/dataset_sensitivity_top3.csv",
        "experiments_phys_levels/dataset_sensitivity_spearman.csv",
    ],
    "D_legacy_inverse_and_validation": [
        "experiments_phys_levels/paper_inverse_full_vs_reduced_summary.csv",
        "experiments_phys_levels/paper_inverse_full_vs_reduced_parameter_table.csv",
        "experiments_phys_levels/paper_inverse_full_vs_reduced_observable_table.csv",
        "experiments_phys_levels/paper_extreme_stress_posterior_summary.csv",
        "experiments_phys_levels/paper_extreme_stress_parameter_recovery.csv",
        "experiments_phys_levels/paper_extreme_stress_risk_assessment.csv",
        "experiments_phys_levels/paper_posterior_hf_validation_summary_reduced_maintext.csv",
        "experiments_phys_levels/paper_posterior_hf_validation_per_output_reduced_maintext.csv",
    ],
    "E_legacy_ood_speed_misc": [
        "experiments_phys_levels/paper_ood_results.csv",
        "experiments_phys_levels/paper_ood_multi_feature_summary.csv",
        "experiments_phys_levels/paper_speedup_benchmark.json",
        "experiments_phys_levels/paper_speed_benchmark_detailed.json",
        "experiments_phys_levels/paper_extreme_stress_meta.json",
        "experiments_phys_levels/paper_ood_meta.json",
        "experiments_phys_levels/paper_ood_multi_feature_meta.json",
    ],
}

RESULT_PURPOSE = {
    "experiments_0404/0404_model_registry.csv": "0404 模型注册表。",
    "experiments_0404/0404_experiment_registry.csv": "0404 实验注册表。",
    "experiments_0404/docs/STATUS_MATRIX_0404.md": "STATUS_MATRIX_0404（新建）：按四级标注所有模块的验证状态。",
    "experiments_0404/docs/RESULT_LINEAGE_AUDIT.md": "RESULT_LINEAGE_AUDIT（新建）：记录 R² 异常根因及数据作废/修正结论。",
    "experiments_0404/docs/0404_refactor_summary.md": "0404 重构总说明。",
    "experiments_0404/docs/AN_completeness_audit.md": "完整性审计。",
    "experiments_0404/docs/physics_prior_design.md": "物理先验设计说明。",
    "experiments_0404/docs/repeated_split_rationale.md": "重复划分说明。",
    "experiments_0404/docs/sensitivity_methods_comparison.md": "敏感性方法比较文档。",
    "experiments_0404/docs/todo_list.md": "待办事项。",
    "experiments_0404/docs/open_questions.md": "待确认问题。",
    "experiments_0404/docs/issue_tracker.md": "当前问题。",
    "experiments_phys_levels/paper_metrics_table.csv": "旧主线模型性能总表。",
    "experiments_phys_levels/paper_fixed_model_compare_summary.csv": "fixed 模型总体对比。",
    "experiments_phys_levels/paper_fixed_model_compare_primary.csv": "fixed 模型主输出对比。",
    "experiments_phys_levels/paper_fixed_model_compare_per_output.csv": "fixed 模型逐输出对比。",
    "experiments_phys_levels/paper_focus_metrics_level0.csv": "baseline 主输出性能。",
    "experiments_phys_levels/paper_focus_metrics_level2.csv": "regularized 主输出性能。",
    "experiments_phys_levels/paper_metrics_per_dim_level0.csv": "baseline 逐输出性能。",
    "experiments_phys_levels/paper_metrics_per_dim_level2.csv": "regularized 逐输出性能。",
    "experiments_phys_levels/paper_forward_uq_summary.csv": "正向传播总表。",
    "experiments_phys_levels/paper_safety_threshold_summary.csv": "阈值风险结果。",
    "experiments_phys_levels/paper_sobol_results.csv": "Sobol 原始主结果。",
    "experiments_phys_levels/paper_sobol_results_with_ci.csv": "Sobol+CI 结果。",
    "experiments_phys_levels/paper_sobol_methods_ready_summary.csv": "Sobol methods-ready 汇总。",
    "experiments_phys_levels/paper_sobol_results_ready_top_factors.csv": "Sobol top factor 摘要。",
    "experiments_phys_levels/dataset_sensitivity_top3.csv": "数据集 Spearman top3。",
    "experiments_phys_levels/dataset_sensitivity_spearman.csv": "数据集 Spearman 全表。",
    "experiments_phys_levels/paper_inverse_full_vs_reduced_summary.csv": "full vs reduced inverse 总体比较。",
    "experiments_phys_levels/paper_inverse_full_vs_reduced_parameter_table.csv": "参数恢复比较。",
    "experiments_phys_levels/paper_inverse_full_vs_reduced_observable_table.csv": "观测拟合比较。",
    "experiments_phys_levels/paper_extreme_stress_posterior_summary.csv": "极端应力 inverse 总结。",
    "experiments_phys_levels/paper_extreme_stress_parameter_recovery.csv": "极端应力参数恢复。",
    "experiments_phys_levels/paper_extreme_stress_risk_assessment.csv": "极端应力风险评估。",
    "experiments_phys_levels/paper_posterior_hf_validation_summary_reduced_maintext.csv": "HF posterior validation 总表。",
    "experiments_phys_levels/paper_posterior_hf_validation_per_output_reduced_maintext.csv": "HF posterior validation 逐输出表。",
    "experiments_phys_levels/paper_ood_results.csv": "OOD 总表。",
    "experiments_phys_levels/paper_ood_multi_feature_summary.csv": "多特征 OOD 总表。",
    "experiments_phys_levels/paper_speedup_benchmark.json": "速度提升基准。",
    "experiments_phys_levels/paper_speed_benchmark_detailed.json": "详细速度基准。",
    "experiments_phys_levels/paper_extreme_stress_meta.json": "极端应力实验元信息。",
    "experiments_phys_levels/paper_ood_meta.json": "OOD 元信息。",
    "experiments_phys_levels/paper_ood_multi_feature_meta.json": "多特征 OOD 元信息。",
}


def read_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def file_size_kb(path: Path) -> str:
    if not path.exists():
        return "N/A"
    return f"{path.stat().st_size / 1024:.1f} KB"


def build_bundle(out_file: Path, title: str, file_groups: dict, purpose_map: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append(f"{title}\n")
    lines.append("=" * 120 + "\n")
    lines.append(f"生成时间: {now}\n")
    lines.append(f"项目根目录: {ROOT}\n\n")

    lines.append("【目录索引】\n")
    for group, files in file_groups.items():
        lines.append(f"\n- {group}\n")
        for rel in files:
            lines.append(f"    * {rel} -- {purpose_map.get(rel, '待补充说明')}\n")
    lines.append("\n\n")

    for group, files in file_groups.items():
        lines.append("=" * 120 + "\n")
        lines.append(f"[分组] {group}\n")
        lines.append("=" * 120 + "\n\n")

        for rel in files:
            path = ROOT / rel
            exists = path.exists()

            lines.append("#" * 120 + "\n")
            lines.append(f"文件: {rel}\n")
            lines.append(f"用途: {purpose_map.get(rel, '待补充说明')}\n")
            lines.append(f"存在: {'是' if exists else '否'}\n")
            lines.append(f"大小: {file_size_kb(path)}\n")
            lines.append("-" * 120 + "\n")

            if exists:
                try:
                    lines.append(read_text_file(path))
                except Exception as e:
                    lines.append(f"[读取失败] {e}\n")
            else:
                lines.append("[文件不存在]\n")

            lines.append("\n\n")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"[DONE] 已生成: {out_file}")


def main():
    build_bundle(
        out_file=CODE_OUT,
        title="0310 项目代码与文档汇总（0404精选版）",
        file_groups=CODE_GROUPS,
        purpose_map=CODE_PURPOSE,
    )

    build_bundle(
        out_file=RESULT_OUT,
        title="0310 项目关键结果汇总（0404精选版）",
        file_groups=RESULT_GROUPS,
        purpose_map=RESULT_PURPOSE,
    )


if __name__ == "__main__":
    main()