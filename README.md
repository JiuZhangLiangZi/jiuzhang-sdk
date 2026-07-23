# jiuzhang SDK - 九章光量子云平台 Python SDK

[English](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/blob/main/README_EN.md) | 中文

`jiuzhang-sdk` 是九章光量子计算云平台的 Python 开发套件。它可以帮助您通过 Python 脚本 and Jupyter Notebook 轻松向九章云平台提交高斯玻色采样（GBS）实验任务、轮询查询任务状态，并对返回的实验结果进行结构化解析与本地数据分析。

## 📥 安装

安装当前的预发布版本：

```bash
pip install --pre jiuzhang-sdk
```

安装指定版本：

```bash
pip install jiuzhang-sdk==0.1.0a30
```
> 💡 **提示**：如果您想体验最完整的调用流程（包含 Jupyter 环境下的环境检查、HTML 表格渲染，以及计算 TVD、Hellinger、JS 散度等本地采样数据分析比对指标），推荐直接移步并使用根目录下的 [Jupyter Notebook 完整用例 (sdk_full_usage.ipynb)](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/blob/main/sdk_full_usage.ipynb)。

## 🚀 快速开始

Python 代码示例：

```python
from jiuzhang import CloudClient, GBSParams

# 设置 API Key
api_key = "your-api-key-here"

# 初始化客户端
client = CloudClient(api_key=api_key)

# 构造实验参数并直接传入具体值
params = GBSParams(
    project_id="EXP-39dfbfdcab444d32",
    quantum_computer_id="PH_QC_04",
    mt=300,
    pump_energy_nj=4.6,
    task_name="GBS experiment 001",
)

result = client.run_gbs(params)
print(result.task_id)
print(result.status_name)
print(result.quantum_computer_id)

client.close()
```

## 🧩 核心概念

### ☁️ CloudClient 客户端
![CloudClient.png](https://raw.githubusercontent.com/JiuZhangLiangZi/jiuzhang-sdk/main/imgs/CloudClient.png)

`CloudClient` 是 SDK 的主要入口，用于同远程九章光量子云平台建立 HTTP 通信。它负责估算经典计算时间、提交量子计算任务以及轮询查询任务最终状态。

---

## ⚛️ GBSParams 参数对象

`GBSParams` 是类型化的 GBS 实验任务输入参数封装对象。

```python
from jiuzhang import GBSParams

params = GBSParams(
    project_id="EXP-39dfbfdcab444d32",
    quantum_computer_id="PH_QC_04",
    mt=300,
    pump_energy_nj=4.6,
    task_name="GBS experiment 001",
)
```

| 字段                    | 类型              | 必填 | 说明                                           |
|-----------------------|-----------------|----|----------------------------------------------|
| `project_id`          | `str`           | 是  | 云平台项目 `experiment_code`                      |
| `quantum_computer_id` | `str`           | 是  | 目标云端量子计算机 ID (例如 `PH_QC_04`)                 |
| `mt`                  | `int`           | 是  | 泵浦脉冲时序数 (Time-bin count)，范围 `1 <= mt <= 500` |
| `pump_energy_nj`      | `float`         | 是  | 泵浦脉冲能量，单位为 nJ                                |
| `squeezing_param`     | `float \| None` | 否  | 压缩参数                                         |
| `task_name`           | `str`           | 否  | 任务自定义展示名称，不能超过 200 个字符                       |

---

## 📊 GBSResult 结果对象

`GBSResult` 是任务执行成功后对返回数据进行提取和结构化封装的对象。

| 属性                          | 说明                                                    |
|-----------------------------|-------------------------------------------------------|
| `task_id`                   | 平台生成的任务唯一 ID                                          |
| `status_name`               | 标准化的任务状态字符串（如 `SUCCESS`、`FAILED`、`PENDING`、`RUNNING`） |
| `project_id`                | 关联的项目 ID                                              |
| `quantum_computer_id`       | 运行该任务的目标量子计算机 ID                                      |
| `experimental_distribution` | 实验分布数据曲线（`result_map_points` 中的 `experimental` 数据点）   |
| `ground_truth_distribution` | 参考基准分布曲线（`result_map_points` 中的 `ground_truth` 数据点）   |
| `result_map_points`         | 云端计算并返回的全部可视化概率分布验证曲线字典                               |
| `download_url`              | 任务原始样本结果数据文件的云端下载 URL 地址                              |
| `raw`                       | 云平台返回的原始底层响应 JSON 数据字典                                |

---

## 🏗️ 架构设计

SDK 采用轻量级客户端架构，不要求用户管理底层的物理量子硬件调度或任务调度：

![structure-chart.png](https://raw.githubusercontent.com/JiuZhangLiangZi/jiuzhang-sdk/main/imgs/structure-chart.png)

| 层级    | 作用                              | 主要组件                                    |
|-------|---------------------------------|-----------------------------------------|
| 用户层   | Python 脚本、Jupyter Notebook、业务系统 | 用户代码                                    |
| SDK 层 | 任务参数校验与封装、任务生命周期管理              | `CloudClient`, `GBSParams`, `GBSResult` |
| 通信层   | 请求鉴权与构造、HTTP JSON 传输            | `TokenManager`, HTTP Client             |
| 云平台层  | 远程量子计算和经典辅助时间估算服务               | 九章光量子云平台                                |

---

## 🧱 组件说明

![module.png](https://raw.githubusercontent.com/JiuZhangLiangZi/jiuzhang-sdk/main/imgs/module.png)

* ☁️ `CloudClient`：负责任务提交、经典算力估算、查询与轮询等核心云端通信。
* ⚛️ `GBSParams`：封装 GBS 实验任务的物理与配置参数。
* 📊 `GBSResult`：对任务最终状态和返回曲线进行结构化解析与持有。
* 🔐 `TokenManager`：API Key 本地校验及日志输出的脱敏脱密。
* 📈 `jiuzhang.gbs.analysis`：本地轻量级采样结果 analysis 比对工具箱（如计算 TVD、Hellinger 距离及 JS 散度等）。
* 📒 `jiuzhang.jupyter`： Jupyer Notebook 环境展示与 HTML 表格格式化输出辅助组件。

---

## 🌐 云平台接口约定

SDK 与九章云平台通过以下 RESTful HTTP 接口进行通信：

| SDK 方法                                           | HTTP 接口路径              | 核心行为                        |
|--------------------------------------------------|------------------------|-----------------------------|
| `estimate_runtime(...)` / `estimate_gbs(params)` | `POST /estimate`       | 预估经典仿真计算时间                  |
| `submit_task(...)` / `submit_gbs(params)`        | `POST /tasks/submit`   | 提交 GBS 实验任务                 |
| `get_result(task_id)`                            | `GET /tasks/{task_id}` | 获取任务运行状态及分布曲线               |
| `run_experiment(...)` / `run_gbs(params)`        | 串联逻辑                   | 预估复杂度 → 提交任务 → 轮询结果 → 结构化解析 |

所有网络通信均通过 `X-Jiuzhang-API-Key` 头部进行认证。SDK 内部会自动校验 HTTP 响应及内部的 `code` 业务状态码，当 `code != 0` 时会自动抛出对应的具体业务异常。

---

## 📒 Jupyter Notebook 集成

SDK 提供了专门的辅助函数来优化 Jupyter 交互体验。完整的 Notebook 示例用例请参考：[sdk_full_usage.ipynb](https://github.com/JiuZhangLiangZi/jiuzhang-sdk/blob/main/sdk_full_usage.ipynb)。

```python
from jiuzhang.jupyter import display_gbs_result, get_notebook_client, show_environment

# 1. 查看脱敏后的当前环境配置
show_environment()

# 2. 自动从环境获取客户端并执行任务
client = get_notebook_client()
result = client.run_gbs(params)

# 3. 在 Notebook 单元格中以漂亮的 HTML 汇总表格渲染展示 GBSResult
display_gbs_result(result)
```

---

## 🛠️ 开发与测试

在 `code/` 目录下：

```bash
# 格式化代码
ruff format src tests
# 执行静态检查
ruff check src tests
# 执行严格类型检查
mypy src
# 执行单元测试
pytest
```

---

## 📄 授权协议

Proprietary. Copyright 2026 JiuZhang Quantum. All rights reserved.
