# 中文快速上手｜Global Market Entry Intelligence

本仓库属于 **Jinlei Cao** 的开放研究工具包，用于演示如何将国际经济学、计量分析、跨国投资研究和企业战略决策结合成可复现的定量项目。

## 一、先区分两个模式

- `marketintel demo`：**纯合成数据**；帮助查看图表和网页交互；对任何国家都不构成实证判断。
- `marketintel fetch` + `marketintel analyze`：从世界银行 API 下载真实指标后运行。输出中记录原始观测年份、数据缺失情况与评分假设。

## 二、Mac 安装（推荐 Python 3.10 及以上）

1. 下载 ZIP 并解压。
2. 使用终端进入解压后最外层文件夹。
3. 按顺序执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[app,dev]'
marketintel demo
streamlit run app/streamlit_app.py
```

浏览器会打开可交互的市场比较网页，默认是合成数据。调整五个指标的权重，观察市场排名和得分的变化。

## 三、做真实世界银行数据分析

```bash
marketintel fetch
marketintel analyze
streamlit run app/streamlit_app.py
```

在左侧选择 `reports/latest`。请先看 `Data provenance` 标签页，确认各指标年份与缺失情况，再解读排名。

## 四、Chloe 的 GitHub 上传流程

1. 在 `https://github.com/jinlei-cao` 登录。
2. 点击 **New repository**，命名为 `global-market-entry-intelligence`，设为 Public。
3. 从仓库空白页点击 **uploading an existing file**。
4. 在 Finder 中打开解压后的根目录，按 `Command + Shift + .` 显示隐藏目录。
5. 选中项目目录**内部所有文件与文件夹**，拖入 GitHub 网页。请勿直接上传 ZIP。
6. 提交说明：`Initial release: Global Market Entry Intelligence v0.1.0`。
7. 检查 README 是否在仓库主页直接显示，检查 Actions 是否通过。

## 五、适合放在申请材料里的是什么

- 研究问题、指标体系、数据处理过程、模型设计、敏感性实验及可复现实验文件。
- 世界银行真实数据必须在本地跑通后，才能引用真实的国家排名或具体观察值。
- 展示时建议同时说明两点局限：**各国数据年份不一致**、**加权指标法依赖指标选择和决策权重**。
- 仓库源码是 AI 辅助搭建的起点，建议由 Chloe 独立执行、检查、修改并解释每个分析决策，形成可验证的个人研究过程。

## 六、项目与既有经历的关联

- 本科学习：国际经济与贸易、计量经济学、统计、运营管理与跨境商务。
- 本科论文：对外投资与东道国经济结果。
- 职业发展：商业咨询、运营咨询、投资研究、国际市场进入、商业分析。

这些关联属于研究方向建议，不代表已取得企业使用成果或已发表论文。
