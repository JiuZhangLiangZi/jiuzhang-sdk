<div align="center">
  <a href="#">
    <img src="./imgs/jiuzhang-logo.png" alt="九章量子" height="200">
  </a>
<h1>⚛️jiuzhang-sdk</h1>

</div>
<div align="center">

[![Stars](https://img.shields.io/github/stars/JiuZhangLiangZi/jiuzhang-sdk?style=flat&label=%F0%9F%8C%9F%20stars&labelColor=ff4f4f&color=ff8383)](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/stargazers)
[![Forks](https://img.shields.io/github/forks/JiuZhangLiangZi/jiuzhang-sdk?style=flat&label=%F0%9F%8F%85%20forks&labelColor=800080&color=912CEE)](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/forks)
[![Release](https://img.shields.io/pypi/v/jiuzhang-sdk?style=flat&label=%F0%9F%9A%80%20release&labelColor=008B8B&color=00CCCC)](https://pypi.org/project/jiuzhang-sdk/)
[![Python version](https://img.shields.io/badge/Python-%3E%3D3.12-528bdf?style=flat&logo=python&logoColor=white&labelColor=2155a3)](https://pypi.org/project/jiuzhang-sdk/)
[![Repository activity](https://img.shields.io/github/last-commit/JiuZhangLiangZi/jiuzhang-sdk/main?style=flat&label=%F0%9F%95%92%20updated&labelColor=b45309&color=f59e0b)](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/commits/main)
[![License](https://img.shields.io/badge/License-MIT-34D058?style=flat&label=%F0%9F%93%84%20license&labelColor=22863A)](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/blob/main/LICENSE)
[![Community](https://img.shields.io/badge/Community-%E4%B9%9D%E7%AB%A0%E9%87%8F%E5%AD%90-0FB5EB?style=flat&labelColor=235389)](https://github.com/JiuZhangLiangZi)

**云平台 GBS 实验 · 本地数学与采样 · 五类算法案例**

[简体中文](./README.md) · [English](./README_EN.md)
</div>

九章云平台 Python SDK，是基于九章光量子计算原型的 Python 开发工具包，支持在 Python 脚本或 Jupyter Notebook 中提交 GBS 实验任务、查询任务结果，并提供本地 GBS 数学、采样、IR 序列化与应用实验工具。
## 🚀 能力概览

`jiuzhang-sdk` 提供三类核心能力：

| 能力 | 是否访问九章云平台 | 结果来源 | 适用场景 |
| --- | --- | --- | --- |
| 云平台 GBS 任务 | 是 | 九章云平台执行任务并返回结果 | 提交真实/平台侧 GBS 实验，获取任务状态、采样结果和分布曲线 |
| 本地 GBS 采样与数学工具 | 否 | SDK 本地数值后端生成 | 教学、算法原型、本地验证、Notebook 示例 |
| 本地应用实验 | 否 | SDK 本地应用接口生成 | 手写数字识别、密集子图、图同构、分子对接、分子振动谱 |

云平台 GBS 任务由九章云平台执行；Python 脚本或 Jupyter Notebook 负责发起请求、轮询状态和读取结果。

本地 GBS 采样完全在本机运行，不经过云平台；采样结果由 SDK 本地数值后端根据输入矩阵和采样参数生成。

本地应用实验同样不经过云平台；结果由 SDK 本地任务模块根据示例数据、矩阵参数和算法参数计算得到。

## 📦 安装

使用 Python 3.12 环境安装或更新正式版（项目元数据要求 Python >= 3.12）：

```bash
pip install -U jiuzhang-sdk
```

默认安装已经包含云平台任务提交、本地 GBS 数学与采样、本地 Program 序列化能力，以及本地应用实验依赖。

Jupyter Notebook 中建议同时安装：

```bash
pip install jupyterlab matplotlib
```

## 🔐 工作台凭证准备

首次调用云平台任务前，需要在九章云平台工作台准备三个信息。

### 1. 获取 `api_key`

`api_key` 是云平台鉴权凭证。进入工作台后，在 API Key 或开发者凭证页面创建或重置密钥。

SDK 会把该值写入请求头：

```text
X-Jiuzhang-API-Key: <api_key>
```

建议通过环境变量保存，避免写入代码仓库：

```bash
export JIUZHANG_API_KEY="your-api-key"
```

Windows PowerShell：

```powershell
$env:JIUZHANG_API_KEY="your-api-key"
```

### 2. 获取 `project_id`

`project_id` 是云平台项目 ID，用于把任务归属到指定项目。进入工作台的项目列表或项目详情页，复制项目 ID 或实验编号。

示例：

```text
EXP-demo-project
```

环境变量：

```bash
export JIUZHANG_PROJECT_ID="EXP-demo-project"
```

### 3. 获取 `quantum_computer_id`

`quantum_computer_id` 是云平台设备编码。进入工作台的设备或量子计算机列表，复制可用设备编码。

示例：

```text
PH_QC_04
```

环境变量：

```bash
export JIUZHANG_QUANTUM_COMPUTER_ID="PH_QC_04"
```

## ☁️ 云平台 GBS 任务完整流程

云平台任务推荐按以下流程组织：

```text
初始化客户端 -> 构造实验参数 -> 复杂度预估 -> 提交实验 -> 获取结果 -> 释放资源
```

### 1. 初始化客户端

```python
from jiuzhang import CloudClient

client = CloudClient(
    base_url="https://cloud.jiuzhangqt.com/api/v1",
    api_key="your-api-key",
    timeout=30.0,
)
```

也可以从环境变量创建：

```python
from jiuzhang import CloudClient

client = CloudClient.from_env()
```

### 2. 构造实验参数

```python
from jiuzhang import GBSParams

params = GBSParams(
    project_id="EXP-demo-project",
    quantum_computer_id="PH_QC_04",
    mt=500,
    pump_energy_nj=4.6,
    squeezing_param=0.35,
    task_name="GBS experiment",
)
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `project_id` | 云平台项目 ID，任务归属项目，必填 |
| `quantum_computer_id` | 云平台设备编码，必填 |
| `mt` | 泵浦脉冲时序数 `M_t`，当前 SDK 校验范围为 `1..500` |
| `pump_energy_nj` | 泵浦能量，单位 nJ |
| `squeezing_param` | 压缩参数，可选 |
| `task_name` | 任务名称，便于工作台展示和检索 |

常用派生量：

```python
print(params.input_mode_count())   # 3 * mt
print(params.output_mode_count())  # 9 * (mt + 80)
```

### 3. 复杂度预估

```python
estimate = client.estimate_runtime(
    quantum_computer_id=params.quantum_computer_id,
    mt_value=params.mt,
    pump_energy_nj=params.pump_energy_nj,
)

print(estimate)
```

复杂度预估用于提交前查看任务的经典模拟复杂度或平台侧预估信息。不同平台版本的返回字段可能略有差异，SDK 会保留原始响应字典。

### 4. 提交实验

```python
task = client.submit_task(
    project_id=params.project_id,
    task_name=params.task_name,
    quantum_computer_id=params.quantum_computer_id,
    mt_value=params.mt,
    pump_energy_nj=params.pump_energy_nj,
    squeezing_param=params.squeezing_param,
)

task_id = task["data"]["task_id"]
print("task_id:", task_id)
```

### 5. 获取结果

```python
from jiuzhang import parse_gbs_result

raw_result = client.get_result(task_id)  # 单次查询；未结束时继续轮询
result = parse_gbs_result(raw_result)

print(result.status_name)
print(result.sample_count)
print(result.experimental_distribution)
```

`GBSResult` 常用字段：

| 字段或属性 | 含义 |
| --- | --- |
| `task_id` | 云平台任务 ID |
| `status_name` | 标准化任务状态，如 `SUCCESS`、`FAILED`、`RUNNING` |
| `sample_count` | 采样总数 |
| `result_map_points` | 平台返回的分布曲线点位 |
| `experimental_distribution` | 实验采样分布曲线 |
| `ground_truth_distribution` | 参考分布曲线 |
| `download_url` | 原始结果下载地址 |
| `raw` | 原始响应 |

### 6. 释放资源

```python
client.close()
```

也可以使用一键方法完成预估、提交、轮询和解析：

```python
client = CloudClient(
    base_url="https://cloud.jiuzhangqt.com/api/v1", api_key="your-api-key"
)
try:
    result = client.run_gbs(params, poll_interval=2.0, timeout=300.0)
finally:
    client.close()
print(result.status_name)
```

## 📓 中英文实验案例

完整 SDK 流程：[sdk_usage.ipynb](./usage/sdk_usage.ipynb)

案例保存在 `usage/` 中，包含已运行的图表和输出；打开即可查看，重新执行会更新结果。云平台部分需要工作台凭证，本地算法部分无需云平台凭证。

| 案例 | 中文版 | 英文版 |
| --- | --- | --- |
| 稠密子图搜索实验 | [中文](./usage/%E7%A8%A0%E5%AF%86%E5%AD%90%E5%9B%BE%E6%90%9C%E7%B4%A2%E5%AE%9E%E9%AA%8C/dense_subgraph_zh.ipynb) | [English](./usage/%E7%A8%A0%E5%AF%86%E5%AD%90%E5%9B%BE%E6%90%9C%E7%B4%A2%E5%AE%9E%E9%AA%8C/dense_subgraph_en.ipynb) |
| 图同构实验 | [中文](./usage/%E5%9B%BE%E5%90%8C%E6%9E%84%E5%AE%9E%E9%AA%8C/graph_isomorphism_zh.ipynb) | [English](./usage/%E5%9B%BE%E5%90%8C%E6%9E%84%E5%AE%9E%E9%AA%8C/graph_isomorphism_en.ipynb) |
| 基于 GBS-RVFL 与 GBS-ELM 的 MNIST 手写数字识别教程 | [中文](./usage/%E5%9F%BA%E4%BA%8E%20GBS-RVFL%20%E4%B8%8E%20GBS-ELM%20%E7%9A%84%20MNIST%20%E6%89%8B%E5%86%99%E6%95%B0%E5%AD%97%E8%AF%86%E5%88%AB%E6%95%99%E7%A8%8B/mnist_recognition_zh.ipynb) | [English](./usage/%E5%9F%BA%E4%BA%8E%20GBS-RVFL%20%E4%B8%8E%20GBS-ELM%20%E7%9A%84%20MNIST%20%E6%89%8B%E5%86%99%E6%95%B0%E5%AD%97%E8%AF%86%E5%88%AB%E6%95%99%E7%A8%8B/mnist_recognition_en.ipynb) |
| 分子对接图搜索实验 | [中文](./usage/%E5%88%86%E5%AD%90%E5%AF%B9%E6%8E%A5%E5%9B%BE%E6%90%9C%E7%B4%A2%E5%AE%9E%E9%AA%8C/molecular_docking_zh.ipynb) | [English](./usage/%E5%88%86%E5%AD%90%E5%AF%B9%E6%8E%A5%E5%9B%BE%E6%90%9C%E7%B4%A2%E5%AE%9E%E9%AA%8C/molecular_docking_en.ipynb) |
| 分子振动光谱实验 | [中文](./usage/%E5%88%86%E5%AD%90%E6%8C%AF%E5%8A%A8%E5%85%89%E8%B0%B1%E5%AE%9E%E9%AA%8C/molecular_vibronic_spectra_zh.ipynb) | [English](./usage/%E5%88%86%E5%AD%90%E6%8C%AF%E5%8A%A8%E5%85%89%E8%B0%B1%E5%AE%9E%E9%AA%8C/molecular_vibronic_spectra_en.ipynb) |

下载或克隆整个仓库后，在案例所属目录打开 Notebook，保留同目录的 `.npy` 数据文件。内置数据与预先保存的样本用于本地教学和分析，不代表新提交的云平台实验结果。

## 🧮 本地 GBS 采样

本地 GBS 采样不访问九章云平台，也不会返回平台任务 ID。结果由 SDK 在本机根据邻接矩阵和采样参数计算生成。

安装：

```bash
pip install jiuzhang-sdk
```

示例：

```python
from jiuzhang.local.gbs import (
    random_adjacency_matrix,
    sample_gbs,
    samples_to_distribution,
)

graph = random_adjacency_matrix(8, scale=0.16, seed=7)
samples = sample_gbs(
    graph,
    shots=24,
    mean_photon_count=1.0,
    detector="pnr",
    cutoff=4,
    max_photons=12,
    seed=123,
)

distribution = samples_to_distribution(samples)
print(distribution)
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `modes` | 邻接矩阵维度，也对应本地 GBS 模式数 |
| `scale` | 随机边权缩放系数 |
| `shots` | 本地采样次数 |
| `mean_photon_count` | 目标平均光子数 |
| `detector` | 探测器模型，`pnr` 表示光子数分辨探测，`threshold` 表示阈值探测 |
| `cutoff` | 单模式光子数截断，仅 `pnr` 使用 |
| `max_photons` | 总光子数上限 |
| `seed` | 随机种子，用于复现结果 |

适用场景：

- 本地算法原型验证。
- Notebook 教学演示。
- 采样结果分布统计。
- 与云平台结果进行轻量对照。

## 🧩 本地数学与 IR 工具

```python
from jiuzhang.local.gbs import (
    GBSProgram,
    dumps_ir,
    hafnian,
    loop_hafnian,
    threshold_probability,
    to_blackbird,
    to_xir,
    torontonian,
)
```

常用方法：

| 方法 | 作用 |
| --- | --- |
| `hafnian(matrix)` | 计算 Hafnian |
| `loop_hafnian(matrix)` | 计算 loop Hafnian |
| `torontonian(matrix)` | 计算 Torontonian |
| `threshold_probability(mean, covariance, pattern)` | 计算阈值探测概率 |
| `GBSProgram(modes)` | 构造本地 GBS Program |
| `dumps_ir(program)` | 序列化为 JSON IR |
| `to_blackbird(program)` | 序列化为本地程序文本 |
| `to_xir(program)` | 序列化为 XIR 文本 |

本地程序序列化所需依赖已包含在默认安装中。

## 🧠 本地手写数字识别任务

本地手写数字识别任务用于在 Python 或 Jupyter 环境中演示 GBS-RVFL / GBS-ELM 风格的分类流程。该任务不提交到云平台，也不需要云平台凭证。

一行运行完整任务：

```python
from jiuzhang.local.mnist import run_mnist_recognition

result = run_mnist_recognition(
    train_size=1200,
    test_size=300,
    source="digits",
    n_components=32,
    feature_count=256,
    combine=True,
    random_state=7,
)

print(result.train)
print(result.accuracy)
print(result.confusion_matrix)
```

手动训练与预测：

```python
from jiuzhang.local.mnist import GBSMNISTClassifier, load_mnist_data

dataset = load_mnist_data(train_size=1200, test_size=300, source="digits")
classifier = GBSMNISTClassifier(n_components=32, feature_count=256)

classifier.fit(dataset.train_data, dataset.train_labels, combine=True)
predictions = classifier.predict(dataset.test_data)
evaluation = classifier.evaluate(dataset.test_data, dataset.test_labels, reuse=True)

print(predictions[:20])
print(evaluation["accuracy"])
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `source` | 数据来源，`digits` 使用本地内置手写数字数据，`openml` 使用 MNIST 784 数据集 |
| `train_size` | 训练样本数量 |
| `test_size` | 测试样本数量 |
| `n_components` | PCA 保留的主成分数量 |
| `feature_count` | 本地 GBS 风格特征数量，对应原示例中的 `IndexNumber` |
| `combine` | `True` 表示 GBS-RVFL，拼接原始输入特征；`False` 表示 GBS-ELM |
| `regularization` | 输出层岭回归正则强度 |
| `random_state` | 随机种子，用于复现实验 |

## 🧪 本地应用实验

四个图和分子类实验已经封装在 `jiuzhang.local.applications` 中，示例 Notebook 只需要调用 SDK 方法。

```python
from jiuzhang.local.applications import (
    load_planted_dense_graph,
    greedy_dense_subgraph,
    load_mutag_graphs,
    load_tace_as_graph,
    load_formic_acid,
)

adjacency = load_planted_dense_graph()
dense_result = greedy_dense_subgraph(adjacency, size=8)

mutag_graphs = load_mutag_graphs()
docking_graph = load_tace_as_graph()
molecule = load_formic_acid()
```

常用方法：

| 方法 | 作用 |
| --- | --- |
| `load_planted_dense_graph()` | 加载密集子图示例图 |
| `greedy_dense_subgraph(...)` / `random_dense_search(...)` / `simulated_annealing_dense_search(...)` | 搜索固定节点数的密集子图 |
| `sample_database_search(...)` | 使用本地采样数据库增强密集子图搜索 |
| `load_mutag_graphs()` / `load_graph_samples(...)` | 加载图同构示例图和采样数据 |
| `event_feature_vector_from_samples(...)` / `train_linear_graph_classifier(...)` | 生成图事件特征并训练线性分类器 |
| `load_tace_as_graph()` / `load_phat_graph()` | 加载分子对接图示例 |
| `postselect_subgraphs(...)` / `clique_shrink(...)` / `clique_search(...)` | 从采样候选中提取团结构 |
| `load_formic_acid()` / `vibronic_parameters(...)` / `sample_vibronic_spectrum(...)` | 加载分子数据、构造参数并生成振动谱样本 |

## 🛠️ 开发与测试

在 `code/` 目录执行：

```bash
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## 🗂️ SDK 方法索引

以下列出当前云平台与本地模块的公开接口；带 `...` 的调用省略了上文已说明的参数。`size` 为候选节点数，`iterations` 为搜索预算，`shots` 为采样次数。

### 云平台任务

导入位置：`jiuzhang`

| 接口 / 调用 | 用途与参数 |
| --- | --- |
| `CloudClient.from_env() / from_settings(settings)` | 从环境变量或 Settings 创建客户端 |
| `CloudClient.estimate_runtime(...) / estimate_gbs(params)` | 按设备、时序数和泵浦能量预估复杂度 |
| `CloudClient.submit_task(...) / submit_gbs(params)` | 提交任务；project_id 必填，request_id 标识请求 |
| `CloudClient.get_result(task_id)` | 单次查询；未完成时需继续轮询 |
| `CloudClient.run_experiment(...) / run_gbs(params, poll_interval=2, timeout=300)` | 预估、提交并轮询；分别返回响应字典和 GBSResult |
| `CloudClient.close()` | 关闭 HTTP 连接；建议在 finally 中调用 |
| `GBSParams.validate() / to_cloud_payload() / summary()` | 校验参数、生成请求参数和摘要 |
| `GBSParams.input_mode_count() / output_mode_count()` | 计算输入和输出模式数 |
| `parse_gbs_result(raw_result)` | 解析任务状态、样本数、分布曲线与下载地址 |

### 本地数学、采样与程序

导入位置：`jiuzhang.local.gbs`

| 接口 / 调用 | 用途与参数 |
| --- | --- |
| `hafnian(matrix) / loop_hafnian(matrix) / torontonian(matrix)` | 计算矩阵组合量；适用于 GBS 概率计算 |
| `threshold_probability(mean, covariance, pattern)` | 由均值、协方差和点击模式计算阈值探测概率 |
| `random_adjacency_matrix(modes, scale=0.16, seed=7)` | 生成指定模式数、边权尺度的对称邻接矩阵 |
| `sample_gbs(adjacency, shots=24, mean_photon_count=1.0, detector="pnr")` | 本机生成样本；detector 可选 pnr 或 threshold |
| `samples_to_distribution(samples)` | 将二维样本数组转换为模式到经验概率的字典 |
| `GBSProgram(modes, name="experiment")` | 创建不可变的本地程序描述 |
| `GBSProgram.squeezing(values) / edge(mode_a, mode_b, weight)` | 添加各模式压缩参数或图边，返回新程序 |
| `GBSProgram.measure_fock(shots=1000) / measure_threshold(shots=1000)` | 添加光子数分辨或阈值测量描述 |
| `GBSProgram.to_dict() / dumps_ir(program, format="json")` | 导出字典或 JSON、Blackbird、XIR 文本 |
| `loads_ir(payload)` | 读取 JSON IR，返回字典；不返回可执行程序 |
| `to_blackbird(program) / to_xir(program)` | 导出相应文本格式 |

### 手写数字识别

导入位置：`jiuzhang.local.mnist`

| 接口 / 调用 | 用途与参数 |
| --- | --- |
| `load_mnist_data(train_size=1200, test_size=300, source="digits", random_state=7)` | 加载并划分数据；digits 离线可用，openml 需联网下载 MNIST |
| `GBSMNISTClassifier(n_components=32, feature_count=256, random_state=7)` | 配置 PCA 维数、特征数量与随机种子；GBSClassifier 为别名 |
| `GBSMNISTClassifier.fit(data, targets, combine=True)` | 训练；combine=True 拼接输入特征，False 仅使用映射特征 |
| `GBSMNISTClassifier.predict(data) / evaluate(data, targets)` | 预测标签或返回准确率等评价结果 |
| `confusion_matrix(y_true, y_pred)` | 由真实标签和预测标签计算混淆矩阵 |
| `run_mnist_recognition(...)` | 运行数据加载、训练、预测与评估完整流程 |
| `GBSMNISTResult.to_dict()` | 导出实验结果字典；HandwrittenDigitsData 保存训练与测试数据 |

### 图与分子应用

导入位置：`jiuzhang.local.applications`

| 接口 / 调用 | 用途与参数 |
| --- | --- |
| `to_networkx_graph(adjacency) / graph_density(adjacency, nodes=None) / draw_graph(adjacency)` | 转换图对象、计算密度、绘制图；nodes 为节点索引 |
| `load_planted_dense_graph() / load_sample_database(path)` | 加载示例邻接矩阵或本地 .npy 采样数据库 |
| `dense_score(adjacency, nodes)` | 选中邻接子矩阵元素和的绝对值；不是归一化密度 |
| `greedy_dense_subgraph(adjacency, size=8)` | 贪心删除节点，保留 size 个节点 |
| `random_dense_search(adjacency, size=8, iterations=1000, seed=7)` | 以随机候选搜索稠密子图 |
| `sample_database_search(adjacency, samples, size=8, iterations=1000, seed=7)` | 从非零位置数等于 size 的样本中搜索 |
| `simulated_annealing_dense_search(adjacency, size=8, iterations=1000, temperature=0.1, cooling_ratio=0.995, seed=7)` | 模拟退火；temperature 为初始温度，cooling_ratio 为衰减系数 |
| `load_mutag_graphs() / load_graph_samples(paths)` | 加载四个示例图或各图对应的 .npy 样本 |
| `sample_to_orbit(sample) / sample_to_event(sample, max_count)` | 将光子样本映射为轨道或事件描述 |
| `event_feature_vector_from_samples(samples, events, max_count)` | 统计选定事件特征；max_count 限制单模式光子数 |
| `orbit_feature_vector_from_samples(samples, orbits)` | 统计指定轨道描述的特征 |
| `event_feature_vector(adjacency, events, max_count, samples=100, mean_photon_count=5.5)` | 根据图和采样预算估计事件特征 |
| `train_linear_graph_classifier(features, labels)` | 标准化特征并训练线性分类器，返回参数与分隔线 |
| `load_tace_as_graph() / load_phat_graph()` | 加载分子对接或团搜索示例图 |
| `postselect_subgraphs(dataset, min_photons, max_photons)` | 按总光子数筛选内置样本并返回候选节点列表 |
| `subgraph_density_summary(adjacency, subgraphs, seed=7)` | 比较样本候选与随机候选的平均密度 |
| `clique_shrink(adjacency, nodes) / clique_search(adjacency, nodes, iterations=10) / is_clique(adjacency, nodes)` | 收缩候选为团、局部扩展搜索、验证团结构 |
| `load_formic_acid() / vibronic_parameters(molecule, temperature=0.0)` | 加载甲酸数据并构造振动谱参数；温度单位 K |
| `sample_vibronic_spectrum(parameters, shots=10)` | 根据参数在本机生成振动谱样本 |
| `vibronic_energies(molecule) / vibronic_energies(samples, molecule)` | 由内置样本或指定样本计算跃迁能量 |
| `DenseSearchResult / GraphClassificationResult / DockingGraph / FormicAcidData / VibronicParameters` | 分别承载搜索结果、分类结果、图数据、分子数据与采样参数 |

`GBSProgram` 是程序描述与序列化工具，构建或导出程序不会执行采样，也不会提交云平台任务。Hafnian、Torontonian 和本地 GBS 采样由 The Walrus 在本机计算。图搜索、数据集和分子示例通过 SDK 本地应用接口运行；增加模式数、光子数或采样预算可能显著增加计算时间。

### 程序描述与结果可视化

```python
from jiuzhang.local.gbs import GBSProgram, dumps_ir, loads_ir
from jiuzhang.local.applications import draw_graph, greedy_dense_subgraph
import matplotlib.pyplot as plt

program = (
    GBSProgram(2, name="demo")
    .squeezing([0.2, 0.3])
    .edge(0, 1, 0.1)
    .measure_fock(shots=100)
)
payload = dumps_ir(program)
print(loads_ir(payload)["schema"])

adjacency = [[0, 1, 1], [1, 0, 0], [1, 0, 0]]
search = greedy_dense_subgraph(adjacency, size=2)
print(search.nodes, search.best_score)
draw_graph(adjacency, nodes=search.nodes, title="Dense subgraph")
plt.show()
```

## 🤝 九章量子社区

通过 [GitHub Issues](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/issues) 反馈问题或建议，附上 SDK 版本、最小复现代码和脱敏后的错误信息。

[九章量子](https://github.com/JiuZhangLiangZi) · [九章云平台](https://cloud.jiuzhangqt.com/) · [GitHub](https://github.com/JiuZhangLiangZi/jiuzhang-sdk) · [Gitee](https://gitee.com/jiuzhangliangzi/jiuzhang-sdk) · [PyPI](https://pypi.org/project/jiuzhang-sdk/)

## 📄 许可证

本项目采用 [MIT License](./LICENSE)。Copyright (c) 2026 九章量子 (JiuZhang Quantum)。
