# 基于 LangChain Agent 的智能数据分析与可视化平台

## 项目简介

这是一个智能数据分析平台，用户可以通过上传 CSV/Excel 数据文件，使用自然语言描述分析需求，系统自动完成字段识别、数据预览、统计分析、图表生成、分析结论输出、分析过程记录和报告导出。

## 技术栈

- **Python 3.9+**
- **Streamlit** - 前端界面
- **Pandas** - 数据读取、清洗、统计分析
- **Matplotlib** - 图表生成
- **SQLite** - 分析记录存储
- **LangChain Agent** - 自然语言任务规划（预留接口）

## 项目结构

```
智能数据分析平台/
├── app.py                    # 主应用入口
├── config.py                 # 系统配置
├── requirements.txt          # 依赖列表
├── README.md                 # 说明文档
├── database/
│   ├── db.py                 # 数据库操作
│   └── schema.sql            # 数据库结构
├── core/
│   ├── data_loader.py        # 数据加载模块
│   ├── data_profile.py       # 数据画像模块
│   ├── analysis_engine.py    # 分析引擎
│   ├── chart_generator.py    # 图表生成模块
│   ├── report_generator.py   # 报告生成模块
│   ├── trace_logger.py       # Trace记录模块
│   ├── security_guard.py     # 安全防护模块
│   └── agent_engine.py       # Agent引擎
├── tools/
│   ├── pandas_tools.py       # Pandas工具
│   ├── chart_tools.py        # 图表工具
│   └── report_tools.py       # 报告工具
├── outputs/
│   ├── charts/               # 生成的图表
│   └── reports/              # 导出的报告
└── sample_data/
    └── sales_demo.csv         # 示例数据
```

## 安装步骤

### 1. 克隆或下载项目

```bash
cd 智能数据分析平台
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中打开，默认地址：`http://localhost:8501`

## 使用说明

### 1. 数据上传
- 点击左侧「上传 CSV 或 Excel 文件」上传数据文件
- 或点击「加载示例数据」使用内置示例数据

### 2. 数据预览
- 在「数据预览」标签页查看上传数据的基本信息
- 显示数据行数、列数、缺失率等

### 3. 数据画像
- 在「数据画像」标签页查看字段分类
- 包括数值字段、类别字段、日期字段
- 查看描述性统计信息

### 4. 智能分析
- 在「智能分析」标签页输入自然语言分析需求
- 示例问题：
  - 统计不同地区的销售额
  - 分析每个月的订单趋势
  - 找出销售额最高的前10个商品
  - 生成各类别销售占比饼图

### 5. 查看结果
- 在「分析结果」标签页查看详细分析结果
- 包括分析计划、数据结果、图表、结论

### 6. 报告导出
- 在「报告导出」标签页生成并下载分析报告
- 支持 Markdown 和 Word 格式

## 功能特性

### 数据上传模块
- 支持 CSV 和 Excel 文件上传
- 自动读取数据并显示预览
- 字段信息统计（类型、缺失值、唯一值）
- 友好的错误提示

### 数据画像模块
- 自动识别字段类型（数值、类别、日期）
- 描述性统计分析
- 缺失值分析
- 分析建议生成

### 自然语言分析模块
- 支持多种分析类型：统计汇总、分组聚合、排序、趋势分析、占比分析
- 自动生成分析计划
- 图表自动生成

### LangChain Agent 模块
- 规则模拟模式（无需 API Key）
- 预留 LLM 接口（支持 OpenAI、通义千问）

### 图表生成模块
- 支持柱状图、折线图、饼图、散点图、直方图
- 自动保存到 outputs/charts/

### 分析结论生成
- 自动生成分析结论
- 包括主要发现、趋势、建议

### Trace 全链路记录
- 每次分析生成唯一 trace_id
- 记录工具调用、耗时、风险等级
- 保存到 SQLite 数据库

### 安全防护模块
- 危险指令检测
- 白名单工具限制
- 高风险操作人工审核

### 报告导出模块
- 支持 Markdown 和 Word 格式
- 包含数据信息、分析结果、图表、结论

## 示例数据分析

平台内置了示例数据 `sales_demo.csv`，包含以下字段：
- date: 日期
- region: 地区
- product: 产品
- category: 类别
- sales: 销售额
- quantity: 数量
- profit: 利润
- customer_type: 客户类型

示例问题：
1. "统计不同地区的销售额" - 分组求和分析
2. "分析每个月的订单趋势" - 时间序列趋势分析
3. "找出销售额最高的前10个商品" - TopN 分析
4. "生成各类别销售占比饼图" - 占比分析

## 配置说明

在 `config.py` 中可以修改以下配置：
- 中文字体设置
- 图表颜色
- 支持的文件类型
- 危险指令模式
- 允许的工具列表

## 数据库

SQLite 数据库会自动创建，包含以下表：
- upload_records: 上传记录
- analysis_records: 分析记录
- tool_call_logs: 工具调用日志
- chart_records: 图表记录
- report_records: 报告记录

## 后续扩展

预留了以下扩展接口：
1. LLM API 接入（OpenAI、通义千问）
2. 更多图表类型
3. 数据导出功能
4. 多语言支持

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
