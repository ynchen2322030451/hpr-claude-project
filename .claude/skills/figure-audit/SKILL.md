---
name: figure-audit
description: Audit whether figures are consistent with saved result files and manuscript claims.
---

Use this skill when validating figure freshness, figure-text consistency, and plotting provenance.

Workflow:
1. Read plotting script and required input file list.
2. Verify each figure’s source CSV.
3. Report whether the requested update is:
   - data change
   - plotting change
   - caption/text change
4. If only plotting changed, do not rerun model training or forward UQ.
5. If figure numbers conflict with manuscript text, report all mismatches explicitly.

Required outputs:
- source files used
- whether figure is stale
- whether manuscript numbers match figure source
- whether the figure belongs in main text or appendix

Writing rules:
- 不要自动假设图表中的数值是最新的，必须根据 source file 核对。
- 如果 figure 依赖的 csv 比正文更新，必须明确提示正文可能过期。
- 如果主文和附录图的边界不清，优先建议将稳健性补充图移至附录。