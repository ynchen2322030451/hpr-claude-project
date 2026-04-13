# CURRENT_FREEZE_STATE

## 当前阶段
0411 重构冻结前审计阶段

## 当前目标
- 先做 unfinished-items audit
- 先核 source，再决定是否重跑
- 后续真正用于论文的内容统一收口到 code/0411/
- 主稿统一为 0411_v3

## 当前主工作区
- code/0411/
- code/0411/results/
- code/0411/figures/
- code/0411/tables/
- code/0411/manuscript/0411_v3/

## 当前结果源优先级
1. 0411/results 下的 canonical csv/json/log
2. 主文表格
3. 正文
4. 图注
5. 图内手写数字
6. 摘要

## 当前高优先级核验
1. posterior validation：nearest-neighbour vs true HF rerun
2. speed baseline：真实 HF runtime 是否采用 2266 s
3. keff forward-UQ 叙事删除与改写
4. Fig A8 是否由 training_history 直接重画
5. Fig 1 geometry 正式图源补充

## 当前 publication-facing 命名
- 方法机制：physics-consistent monotonicity and inequality constraints
- 模型简称：constraint-regularized surrogate
- internal label：data-mono-ineq（仅可保留在 source note / artifact path）

## 当前禁止事项
- 不得先改正文再核 source
- 不得先删 placeholder 再判断是否真没完成
- 不得把旧 PDF / 旧图注 / 旧摘要当结果源
- 不得继续把 0310 旧目录当作最终稿直接引用路径
