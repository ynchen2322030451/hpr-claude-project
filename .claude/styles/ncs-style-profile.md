# Nature Computational Science — 写作风格规范

## 期刊定位
NCS 发表计算方法与数据驱动方法的原创研究，读者覆盖计算科学、工程、物理、生物等多个领域的专家。
**核心要求**：方法有普适性，叙事以问题和结论为中心，不追求文学性，只追求精确性。

---

## 句子与段落

**句子**
- 每句话只做一件事：陈述事实、给出结论、或提出解释
- 主句放前，条件/背景放后
- 避免嵌套从句超过两层
- 技术术语第一次出现时给全称，之后可简写

**段落**
- 每段第一句是主题句（what），最后一句是意义句（so what）
- 中间提供支撑（evidence / mechanism）
- 不在同一段混合：背景 + 结果 + 解释 + 意义

**长度**
- Abstract: ≤200 words（NCS hard limit）
- Introduction: 4-6 paragraphs
- Methods: 按模块分小节，不写散文
- Results 每个小节: 2-4 paragraphs
- Discussion: 4-6 paragraphs

---

## 用词规范

**动词强度**
| 过强（避免） | 推荐替换 |
|-------------|---------|
| demonstrates, proves, confirms | suggests, indicates, is consistent with |
| shows that X causes Y | shows that X is associated with Y |
| validates | is validated against / compared with |
| revolutionary, unprecedented | （删去，用具体数字代替） |

**结构词**
- 不用 "In this paper, we..." 开头
- 不用 "It is worth noting that..."
- 不用 "As can be seen from Figure X..."
- 直接写结论："X increases by Y% when Z (Fig. X)."

**学术克制**
- 不宣称"首次"除非有文献对比支撑
- 不用 "robust" 除非有统计证明
- 不用 "comprehensive" 形容自己的分析
- 比较性语言必须指明对比基准

---

## 时态与语态

| 位置 | 时态 | 语态 |
|------|------|------|
| Methods（描述本文方法） | 过去时 | 主动或被动均可 |
| Results（报告发现） | 过去时 | 主动 |
| Discussion（解释意义） | 现在时 | 主动 |
| Introduction（背景） | 现在时（已知事实）/ 过去时（他人工作） | 均可 |
| Abstract | 过去时（本文工作）+ 现在时（结论） | 均可 |

---

## Results 与 Discussion 分离

**Results 只写**：
- 观察到什么（数字、比较、趋势）
- 与什么基准相比
- 统计显著性（如适用）

**Results 不写**：
- 为什么（机制解释→Discussion）
- 意味着什么（意义→Discussion）
- 与其他工作的关系（→Discussion）

---

## 图表叙事

- 图题（caption）：先说结论，再说实验条件
  - ✗ "Figure 3. Comparison of two models."
  - ✓ "Figure 3. Physics-regularized model reduces stress-prediction uncertainty relative to the baseline. (a)-(b) show..."
- 正文引用图：先说结论，括号内引图
  - ✓ "Stress exceedance probability increases monotonically with perturbation magnitude (Fig. 2a)."
  - ✗ "Fig. 2a shows the stress exceedance probability."

---

## 本项目特定术语表

| 代码字段 | 论文术语（英文） | 备注 |
|---------|---------------|------|
| iteration2_max_global_stress | second-iteration maximum global stress (σ_max) | 主文全称 |
| iteration2_keff | second-iteration effective multiplication factor (k_eff) | |
| iteration1_* | first-iteration * | |
| Level 0 / baseline | baseline probabilistic surrogate | |
| Level 2 / data-mono | physics-regularized probabilistic surrogate | |
| HPR | heat-pipe-cooled reactor | 首次出现给全称 |
| HF simulation | high-fidelity coupled simulation | |
| NLL | negative log-likelihood | 方法节定义后可简写 |
| PICP90 | 90% prediction interval coverage probability | |
| split_meta | frozen dataset partition | 不出现在论文 |

---

## 禁止词清单

绝对禁止（任何位置）：
- "hallucinate", "AI thinks", "as an AI"
- 自我指涉句 "In this study, we will..."（用 "We" + 过去时）
- "obviously", "clearly", "of course", "needless to say"
- 编造引用（未确认的参考文献必须标 【待核实】）
