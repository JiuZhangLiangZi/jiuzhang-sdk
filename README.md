# jiuzhang-sdk ✨

九章云平台 Python SDK，支持在 Python 脚本或 Jupyter Notebook 中提交 GBS 实验任务、查询任务结果，并提供本地 GBS 数学、采样、IR 序列化与应用实验工具。

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

安装正式版：

```bash
pip install jiuzhang-sdk
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

raw_result = client.get_result(task_id)
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
result = client.run_gbs(params, poll_interval=2.0, timeout=300.0)
print(result.status_name)
```

## 📓 Jupyter 示例

完整 Jupyter 示例见仓库根目录：

[sdk_usage.ipynb](./sdk_usage.ipynb)

该 Notebook 按以下步骤组织：

1. 配置云平台地址与工作台凭证。
2. 初始化 SDK 客户端。
3. 构造 GBS 实验参数。
4. 调用复杂度预估接口。
5. 提交云平台 GBS 实验。
6. 轮询并解析结果。
7. 绘制返回的分布曲线。
8. 展示本地 GBS 采样、本地 Program 序列化和本地应用实验。

本地应用实验示例：

- [mnist_recognition_zh.ipynb](./mnist_recognition_zh.ipynb)
- [dense_subgraph_zh.ipynb](./dense_subgraph_zh.ipynb)
- [graph_isomorphism_zh.ipynb](./graph_isomorphism_zh.ipynb)
- [molecular_docking_zh.ipynb](./molecular_docking_zh.ipynb)
- [molecular_vibronic_spectra_zh.ipynb](./molecular_vibronic_spectra_zh.ipynb)

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

## 📄 许可证

Proprietary. Copyright 2026 JiuZhang Quantum. All rights reserved.
