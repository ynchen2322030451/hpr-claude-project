#!/bin/bash
# pull_posterior_results.sh
# 从服务器拉取全部 4 个模型的后验推断结果

SERVER="tjzs@100.68.18.55"
REMOTE_BASE="/home/tjzs/Documents/fenics_data/hpr_surrogate/hpr-claude-project/code/0310/experiments_0404/experiments/posterior"
LOCAL_BASE="/Users/yinuo/Projects/hpr-claude-project/code/0310/experiments_0404/experiments/posterior"

for MODEL in baseline data-mono phy-mono data-mono-ineq; do
    echo "=== 拉取 $MODEL ==="
    mkdir -p "$LOCAL_BASE/$MODEL"
    scp "$SERVER:$REMOTE_BASE/$MODEL/benchmark_summary.csv"    "$LOCAL_BASE/$MODEL/"
    scp "$SERVER:$REMOTE_BASE/$MODEL/feasible_region.csv"      "$LOCAL_BASE/$MODEL/"
    scp "$SERVER:$REMOTE_BASE/$MODEL/posterior_manifest.json"  "$LOCAL_BASE/$MODEL/"
    scp "$SERVER:$REMOTE_BASE/$MODEL/benchmark_case_meta.json" "$LOCAL_BASE/$MODEL/" 2>/dev/null || true
    scp "$SERVER:$REMOTE_BASE/$MODEL/"*.log                    "$LOCAL_BASE/$MODEL/" 2>/dev/null || true
    echo "    done"
done

echo "=== 全部完成 ==="
