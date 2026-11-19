# 19 Reranker 模型测评：RAG 效果

> **核心结论**
>
> 1. Reranker 是“重排序任务/模型”的统称，Cross-Encoder 是实现 Reranker 的常见架构，二者不是互斥选项。
> 2. 在 GooAQ 的同一组两阶段排序评测中，Jina Reranker v2 multilingual 和 BGE Reranker v2-M3 的 nDCG@10 分别为 **74.9**、**73.6**，高于 MiniLM Cross-Encoder 基线的 **69.6**，绝对提升 **5.3**、**4.0 个百分点**。
> 3. 在 FiQA 端到端 RAG 实验中，LLM Reranker（GPT-4o-mini）在固定 HyPE 召回策略下，答案正确性、忠实度和相关性均高于 BGE、MiniLM 两个 Cross-Encoder Reranker；提升幅度为 **1.7～3.8 个百分点**。
>
> 以上均为公开论文/模型评测数据，不是 DevFlow 本地实测结果。所有指标统一保留一位小数。

## 1. 概念边界：Reranker 与 Cross-Encoder

- **Rerank（重排序）**：检索流程中的第二阶段，对第一阶段召回的候选文档重新打分和排序。
- **Reranker**：执行重排序的模型或组件。
- **Cross-Encoder**：一种常见的 Reranker 模型架构，将 Query 与 Document 联合输入模型，直接预测相关性分数。
- **LLM Reranker**：使用生成式大语言模型判断 Query 与候选文档的相关性，可以通过 pointwise、pairwise 或 listwise 方式排序。

因此，“Reranker 和 Cross-Encoder 谁更好”不是严谨的分类对比。合理的比较方式有两种：

1. **模型对模型**：例如 Jina Reranker v2、BGE Reranker v2-M3，与 MiniLM Cross-Encoder 基线比较。
2. **架构对架构**：传统 Cross-Encoder Reranker，与 GPT-4o-mini 这类 LLM Reranker 比较。

Hugging Face 的 Sentence Transformers 教程明确将 Reranker Model 称为 Cross-Encoder，并说明其通常用于快速召回后的 Top-K 精排。

参考：[Training and Finetuning Reranker Models with Sentence Transformers](https://huggingface.co/blog/train-reranker)。

## 2. 实验一：两款 Reranker 模型对比 MiniLM Cross-Encoder

### 2.1 实验来源与设置

来源：Hugging Face《Training and Finetuning Reranker Models with Sentence Transformers》中的 GooAQ Reranking Evaluation。

| 实验项 | 设置 |
|---|---|
| 数据集 | GooAQ |
| 评测 Query 数量 | 1,000 |
| 第一阶段召回 | 每个 Query 召回 Top 30 |
| 候选来源 | static-retrieval-mrl-en-v1 |
| 排序指标 | nDCG@10 |
| 评测方式 | realistic two-stage：只重排召回器实际返回的候选，不强行补入未召回的正样本 |

这里将 `cross-encoder/ms-marco-MiniLM-L6-v2` 作为传统 Cross-Encoder 基线，比较两款更强的候选 Reranker：

- `BAAI/bge-reranker-v2-m3`
- `jinaai/jina-reranker-v2-base-multilingual`

### 2.2 评测结果

<text></text>

| 模型 | 参数量 | nDCG@10 | 相比 MiniLM 基线 |
|---|---:|---:|---:|
| MiniLM Cross-Encoder（基线） | 22.7M | 69.6 | — |
| BGE Reranker v2-M3 | 568M | 73.6 | **+4.0 个百分点（+5.8%）** |
| Jina Reranker v2 multilingual | 278M | 74.9 | **+5.3 个百分点（+7.6%）** |

注：nDCG@10 按百分制展示。百分点是两个百分制指标的直接差值；括号内为相对提升率，即“差值 ÷ 基线”。

### 2.3 结果解读

1. **Jina Reranker v2 multilingual**：nDCG@10 为 74.9，相比 MiniLM 的 69.6 提升 5.3 个百分点，相对提升 7.6%。
2. **BGE Reranker v2-M3**：nDCG@10 为 73.6，相比 MiniLM 提升 4.0 个百分点，相对提升 5.8%。
3. 在该 GooAQ 英文评测中，Jina 的 nDCG@10 比 BGE 高 1.3 个百分点；BGE 参数量更大，并不意味着它在此数据集上一定更好。
4. 这组结果证明的是“两个具体 Reranker 模型优于 MiniLM 这个 Cross-Encoder 基线”，**不能证明它们优于 Cross-Encoder 架构**。Jina、BGE 本身也属于 Cross-Encoder 风格的 Reranker。

注意：GooAQ 是英文问答数据，不能把该结果直接当成中文 DevFlow 知识库的实测收益。

来源：[Hugging Face 原文及完整评测表](https://huggingface.co/blog/train-reranker)。

## 3. 实验二：LLM Reranker 对比两个 Cross-Encoder Reranker 的 RAG 效果

### 3.1 论文与实验设置

论文：*Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs*。

作者：Harun Elkiran、Jawad Rasheed。

发表：Discover Computing，2026 年 5 月 9 日。

论文：[Springer Nature 官方页面](https://link.springer.com/article/10.1007/s10791-026-10156-3)，[DOI](https://doi.org/10.1007/s10791-026-10156-3)。

实验使用 FiQA 金融问答数据集，约 57,000 个 passage，选取 600 个 Query。Embedding 固定为 `text-embedding-3-large`，生成模型固定为 `GPT-4o-mini`，比较 BGE Cross-Encoder、MiniLM Cross-Encoder 和 GPT-4o-mini LLM Reranker。

为了尽量控制变量，以下只比较同一个 HyPE 召回策略下的三种 Reranker 结果：

| 实验项 | 设置 |
|---|---|
| 数据集 | FiQA |
| Query 数量 | 600 |
| 语料规模 | 约 57,000 passages |
| Chunk Size / Overlap | 1,000 / 200 tokens |
| Embedding | text-embedding-3-large |
| 第一阶段召回 | Top 10 |
| 精排后上下文 | Top 10 |
| 生成模型 | GPT-4o-mini |
| 固定召回策略 | HyPE |

### 3.2 RAG 生成质量：GPT-4o-mini LLM Reranker 对比 BGE / MiniLM

<text></text>

| 指标 | GPT-4o-mini LLM Reranker | BGE Cross-Encoder | 提升 | MiniLM Cross-Encoder | 提升 |
|---|---:|---:|---:|---:|---:|
| Answer Correctness | **80.1** | 77.9 | **+2.2 个百分点** | 76.4 | **+3.8 个百分点** |
| Faithfulness | **87.8** | 86.0 | **+1.8 个百分点** | 85.0 | **+2.7 个百分点** |
| Answer Relevance | **92.7** | 91.0 | **+1.7 个百分点** | 90.3 | **+2.4 个百分点** |

所有指标统一转换为百分制并保留一位小数。提升值为 GPT-4o-mini 与对应 Cross-Encoder 的绝对差值，不是相对百分比。

### 3.3 MRR 与响应时间

- 论文报告：9 组 Retriever-Reranker 配置中，只有 **HyPE + GPT-4o-mini** 获得正向 MRR gain，增益为 **3.9 个百分点**（原始增量为 0.039）。
- 这表示该组合不只改善下游生成质量，也改善了相关文档在排序列表中的位置；但不能把该数值解释成 GPT-4o-mini 相对某一个 Cross-Encoder 的精确 MRR 差值。
- 平均端到端响应时间如下：

| HyPE + Reranker | 平均端到端响应时间 |
|---|---:|
| GPT-4o-mini LLM Reranker | 3.6 秒 |
| BGE Cross-Encoder | 4.4 秒 |
| MiniLM Cross-Encoder | 2.7 秒 |

这里的延迟包含检索、重排和生成，不是单独的 Reranker 推理耗时。该实验中 GPT-4o-mini 比 BGE 组合快，但比 MiniLM 组合慢；因此不能简单概括为“LLM Reranker 一定更快”。论文也指出 LLM Reranker 的成本更高。

### 3.4 结果解读

1. 在固定 HyPE 召回和 GPT-4o-mini 生成模型的条件下，LLM Reranker 的三个下游质量指标均高于 BGE 和 MiniLM。
2. 对比 BGE，LLM Reranker 的正确性、忠实度、相关性分别提升 2.2、1.8、1.7 个百分点。
3. 对比 MiniLM，分别提升 3.8、2.7、2.4 个百分点。
4. MiniLM 的平均端到端延迟最低；LLM Reranker 的质量优势伴随更高成本，实际选型需要权衡质量、延迟与费用。
5. 该论文只使用 FiQA 金融领域数据集，且 Ground Truth Answer 经过人工监督生成，作者也明确指出跨领域泛化能力仍需更多实验验证。

来源：[Springer 论文实验设置、Tables 2–5 和结论](https://link.springer.com/article/10.1007/s10791-026-10156-3)。

## 4. 两组实验的综合结论

| 比较目标 | 对比对象 | 核心指标 | 结果 |
|---|---|---|---|
| 模型级排序效果 | BGE v2-M3 vs MiniLM Cross-Encoder | nDCG@10 | +4.0 个百分点 |
| 模型级排序效果 | Jina v2 multilingual vs MiniLM Cross-Encoder | nDCG@10 | +5.3 个百分点 |
| RAG 答案质量 | GPT-4o-mini LLM Reranker vs BGE Cross-Encoder | Correctness / Faithfulness / Relevance | +2.2 / +1.8 / +1.7 个百分点 |
| RAG 答案质量 | GPT-4o-mini LLM Reranker vs MiniLM Cross-Encoder | Correctness / Faithfulness / Relevance | +3.8 / +2.7 / +2.4 个百分点 |

**最终结论：**

- 如果比较具体的模型，Jina v2 和 BGE v2-M3 在 GooAQ 的 nDCG@10 上优于 MiniLM Cross-Encoder 基线。
- 如果比较模型架构，FiQA 实验显示 LLM Reranker（GPT-4o-mini）在答案正确性、忠实度和相关性上优于 BGE、MiniLM Cross-Encoder，但存在成本和延迟权衡。
- 不能把“某个 Reranker 模型优于 MiniLM”泛化为“Reranker 优于 Cross-Encoder”，因为 Cross-Encoder 本身就是 Reranker 的常见实现架构。

## 5. 对 DevFlow RAG 的适配与验证方案

### 5.1 当前项目实现

核对 DevFlow 源码后，当前实现如下：

1. 第一阶段采用向量与关键词混合召回，合并候选后进入重排。
2. 知识库默认 Reranker Provider 为 `qwen_api`，模型为 `qwen3-rerank`。
3. Qwen Rerank API 调用失败时，回退到本地启发式重排。
4. 启发式重排会综合基础融合分、向量分、关键词分、Query 词项覆盖率、标题/路径匹配、新鲜度等特征。
5. 因此，项目当前不是“默认使用 MiniLM Cross-Encoder”；不能把公开论文中的 MiniLM 指标写成 DevFlow 已实测指标。

源码入口：

- [Reranker 模型目录与 Qwen API 调用](../backend/app/services/rag/knowledge_base.py)
- [本地启发式重排实现](../backend/app/services/rag/rerank.py)
- [知识库默认模型配置](../backend/app/db/models.py)
- [RAG 检索与重排流程说明](1%20知识库切分与向量入库.md)

### 5.2 建议的 DevFlow 对照组

| 组别 | 模型 / 策略 | 作用 |
|---|---|---|
| A | 不启用 Rerank | 检索基线 |
| B | 当前 Qwen3-Rerank | 项目现有默认方案 |
| C | BGE Reranker v2-M3 | 开源多语言 Cross-Encoder 候选 |
| D | Jina Reranker v2 multilingual | 开源多语言 Cross-Encoder 候选 |
| E | MiniLM Cross-Encoder | 轻量 Cross-Encoder 对照基线 |
| F（可选） | GPT-4o-mini LLM Reranker | 高质量、较高成本的架构对照组 |

### 5.3 控制变量与评价指标

为避免把召回质量、重排质量和生成模型差异混为一谈，建议：

1. 固定同一批 Query、知识库文档、Chunk 切分结果和人工标注的相关文档。
2. 固定 Embedding 模型、第一阶段召回策略和候选集合；所有 Reranker 接收完全相同的候选文档。
3. 固定候选数量与最终 Top-K，例如候选 Top 24、最终上下文 Top 3。
4. 固定生成模型、System Prompt、上下文预算和答案评测器。
5. 每组重复运行，记录模型调用失败、回退比例、费用和延迟。

| 指标层 | 指标 | 目的 |
|---|---|---|
| 候选召回 | Recall@24 | 衡量第一阶段是否召回了正确证据 |
| 排序质量 | MRR@3、nDCG@10、Precision@3 | 衡量正确证据是否排到前面 |
| 上下文质量 | Context Precision、Context Recall | 衡量最终传给生成模型的上下文质量 |
| 答案质量 | Faithfulness、Answer Correctness、Answer Relevance | 衡量答案是否忠实、正确且相关 |
| 系统效率 | Rerank P50/P95、端到端 P50/P95、单次成本 | 衡量生产环境的延迟与成本 |

**关键注意：** Reranker 只能重新排列第一阶段已经召回的候选，无法凭空找回候选集合之外的文档。因此，Recall@24 应单独衡量第一阶段召回能力；Reranker 的主要优化目标应放在最终 Top-K 的排序质量上。

### 5.4 项目落地建议

- 当前优先保留 Qwen3-Rerank 作为现有线上基准，避免只根据其他数据集的公开分数替换模型。
- 将 BGE v2-M3 和 Jina v2 multilingual 作为两个开源候选模型，先在同一 DevFlow Query 集上离线比较。
- 如果业务更重视复杂语义判断和最终答案正确性，再增加 LLM Reranker 对照组。
- 最终选择依据应是 DevFlow 自己的 nDCG@10、MRR@3、Faithfulness、Correctness、P95 延迟和单次成本，而不是单个公开榜单。

## 6. 参考资料

1. Hugging Face，*Training and Finetuning Reranker Models with Sentence Transformers*：<https://huggingface.co/blog/train-reranker>。
2. Elkiran, H. & Rasheed, J. (2026)，*Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs*，Discover Computing：<https://doi.org/10.1007/s10791-026-10156-3>。
3. BAAI，BGE Reranker v2-M3 模型卡：<https://huggingface.co/BAAI/bge-reranker-v2-m3>。
4. Jina AI，Jina Reranker v2 multilingual 模型卡：<https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual>。
