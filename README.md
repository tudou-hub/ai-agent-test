# AI Agent Benchmark - 游戏攻略助手评测体系

一个针对AI Agent的多维度评测框架，覆盖检索质量、生成质量、意图识别、工具调用、安全压测等核心指标。

## 项目背景

本项目是一个**AI测试专家求职作品**，旨在展示：

- 如何为AI系统设计科学的评测体系
- 如何构建覆盖多场景的测试数据集
- 如何实现评测流程自动化
- 如何探索AI在测试领域的应用

## 项目结构

```
ai-agent-benchmark/
├── config/                    # 配置文件
│   └── settings.yaml          # 模型、评测参数配置
│
├── target_system/             # 被测对象：游戏攻略Agent
│   ├── knowledge/             # 知识库
│   │   └── stardew_valley.txt
│   ├── tools.py               # Agent工具定义
│   └── agent.py               # Agent实现
│
├── test_data/                 # 测试数据集（核心产出）
│   ├── schema.md              # 测试用例设计说明
│   ├── basic_qa.json          # 正面问题
│   ├── intent_test.json       # 意图分类测试
│   ├── edge_cases.json        # 边界问题
│   ├── no_answer.json         # 无答案问题
│   ├── time_sensitive.json    # 时间敏感问题
│   └── security_test.json     # 安全压测
│
├── evaluator/                 # 评测引擎
│   ├── metrics/               # 各维度评测指标
│   │   ├── retrieval.py       # 检索质量
│   │   ├── generation.py      # 生成质量
│   │   ├── intent.py          # 意图识别
│   │   ├── agent.py           # Agent决策
│   │   └── security.py        # 安全性
│   ├── judge.py               # LLM-as-Judge
│   ├── scorer.py              # 综合打分
│   └── report.py              # 报告生成
│
├── ai_test_ai/                # AI辅助测试探索
│   ├── case_generator.py      # AI生成测试用例
│   └── defect_predictor.py    # AI缺陷预测
│
├── run_benchmark.py           # 一键回归脚本
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行评测

```bash
python run_benchmark.py
```

### 3. 查看报告

评测完成后，报告会生成在 `reports/` 目录下。

## 评测指标体系

| 维度 | 指标 | JD对应 |
|------|------|--------|
| 检索质量 | 命中率、MRR | RAG效果评估 |
| 生成质量 | ROUGE-L、覆盖率、幻觉率 | 准确率、召回率、幻觉率 |
| 意图识别 | 分类准确率 | 意图识别率 |
| Agent决策 | 工具选择、任务完成度 | 工具调用、决策合理性 |
| 安全性 | 攻击成功率、防御成功率 | Prompt注入、指引漂移压测 |

## 测试数据设计

测试数据覆盖5类场景：

1. **正面问题**：有明确攻略答案的问题
2. **边界问题**：模糊描述、需推理的问题
3. **无答案问题**：超出知识库范围，测试拒答能力
4. **时间敏感问题**：版本更新相关，测试知识时效
5. **安全压测**：Prompt注入、越狱攻击

## JD指标映射

本项目直接命中以下JD要求：

| JD要求 | 项目实现 |
|--------|----------|
| 建立评估模型(Benchmark) | 5维度评测指标体系 |
| 准确率、召回率、幻觉率 | generation.py |
| 意图识别率 | intent.py |
| 工具调用、决策合理性 | agent.py |
| Prompt注入、指引漂移压测 | security.py + security_test.json |
| 测试工具设计与开发 | run_benchmark.py 一键回归 |
| 数据集构建 | test_data/ 精标注数据集 |
| AI生成测试用例 | case_generator.py |
| 智能测试报告生成 | report.py |

## 扩展使用

### 添加新的测试用例

在 `test_data/` 目录下添加JSON文件，格式参考 `schema.md`。

### 接入真实LLM

设置环境变量：
```bash
export OPENAI_API_KEY=your_api_key
```

修改 `config/settings.yaml` 中的模型配置。

## 许可证

MIT License
