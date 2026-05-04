import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.absolute()
OUTPUTS_DIR = BASE_DIR / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
REPORTS_DIR = OUTPUTS_DIR / "reports"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "analysis.db"
TRACE_LOGS_DIR = BASE_DIR / "outputs" / "trace_logs"

for directory in [OUTPUTS_DIR, CHARTS_DIR, REPORTS_DIR, SAMPLE_DATA_DIR, DATABASE_DIR, TRACE_LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

CHINESE_FONT_CANDIDATES = [
    "SimHei",
    "Microsoft YaHei",
    "PingFang SC",
    "STHeiti",
    "WenQuanYi Micro Hei",
    "Noto Sans CJK SC",
]

CHART_COLORS = [
    "#2E86AB",
    "#A23B72",
    "#F18F01",
    "#C73E1D",
    "#3B1F2B",
    "#95C8D8",
    "#E8A87C",
    "#41B3A3",
    "#E27D60",
    "#85DCB8",
]

SUPPORTED_FILE_TYPES = ["csv", "xlsx", "xls"]

MAX_PREVIEW_ROWS = 20

DANGEROUS_PATTERNS = [
    "import os",
    "import sys",
    "subprocess",
    "eval",
    "exec",
    "open(",
    "write",
    "delete",
    "remove",
    "rmdir",
    "shutil",
    "socket",
    "requests.post",
    "os.system",
    "__import__",
    "os.popen",
    "getattr",
    "setattr",
    "delattr",
    "compile(",
    "memoryview",
    "buffer(",
]

HIGH_RISK_PATTERNS = [
    "全量导出",
    "所有数据",
    "drop",
    "truncate",
    "敏感字段",
    "password",
    "secret",
    "token",
    "credential",
]

ALLOWED_TOOLS = [
    "data_profile",
    "schema_check",
    "groupby_sum",
    "groupby_count",
    "groupby_mean",
    "groupby_max",
    "groupby_min",
    "trend_analysis",
    "topn_analysis",
    "correlation_analysis",
    "outlier_detection",
    "describe",
    "filter",
    "sort",
    "generate_chart",
    "generate_report",
]

LLM_MODES = {
    "rule": "规则模拟模式",
    "react": "ReAct推理模式",
    "qwen": "通义千问",
    "openai": "OpenAI",
    "local": "本地LLM",
}

LLM_PROVIDERS = {
    "qwen": {
        "name": "通义千问",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen3.5-122b-a10b"],
        "default_model": "qwen-turbo",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4",
        "env_key": "OPENAI_API_KEY",
    },
    "local": {
        "name": "本地LLM (Ollama)",
        "models": ["llama2", "qwen", "mistral"],
        "default_model": "qwen",
        "default_url": "http://localhost:11434/v1",
    }
}

LLM_DEFAULT_CONFIG = {
    "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.7")),
    "max_tokens": 2000,
    "top_p": 0.95,
}

AGENT_MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "5"))
ENABLE_HUMAN_REVIEW = os.getenv("ENABLE_HUMAN_REVIEW", "true").lower() == "true"

SYSTEM_PROMPTS = {
    "react_agent": """你是一个专业的数据分析助手，名字叫 DataAnalyticsAgent。

你可以使用以下工具来帮助用户分析数据。每个工具都有明确的用途和参数要求。

## 可用工具列表：

{tool_descriptions}

## 数据信息：
- 数据字段：{columns}
- 数值字段：{numeric_columns}
- 类别字段：{categorical_columns}
- 日期字段：{date_columns}

## 分析原则：
1. 先理解用户需求，再选择合适的工具
2. 每一步分析都要给出清晰的思考过程（thought）
3. 必要时先生成数据画像了解数据结构
4. 分步执行复杂分析，每步都要观察结果
5. 最终用自然语言总结分析结论

## 输出格式要求：
你必须返回JSON格式的结果，包含以下字段：
- thought: 你的思考过程，说明为什么选择这个工具
- action: 要执行的工具名称（必须是上述工具之一）
- action_input: 工具所需的参数（JSON对象）
- need_human_review: 是否需要人工审核（boolean，只有高风险操作才为true）

## 注意事项：
- 不要执行任意Python代码，只能调用注册的工具
- 如果action或参数中包含危险内容，立即标记need_human_review=true
- 如果分析完成或无法继续，返回 "action": "final_answer"

请开始分析。""",

    "final_answer": """你是一个数据分析报告生成专家。根据分析过程和结果，生成一份专业的分析报告。

## 分析数据：
{analysis_data}

## 分析步骤：
{analysis_steps}

## 要求：
1. 用自然语言总结主要发现
2. 指出数据中的关键洞察
3. 提供可行的建议
4. 保持语言专业、正式

请用中文回答。""",

    "human_review_request": """检测到高风险操作，需要人工审核：

操作：{action}
参数：{action_input}
风险原因：{risk_reason}

请确认是否执行此操作。"""
}

TOOL_DESCRIPTIONS = {
    "data_profile": {
        "name": "data_profile",
        "description": "生成数据画像，了解数据基本信息和字段统计特征",
        "args_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "schema_check": {
        "name": "schema_check",
        "description": "检查数据字段结构，返回字段名、类型、缺失值等信息",
        "args_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "groupby_sum": {
        "name": "groupby_sum",
        "description": "按类别字段分组计算数值字段的总和",
        "args_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "分组字段名"},
                "value": {"type": "string", "description": "要汇总的数值字段名"}
            },
            "required": ["group_by", "value"]
        }
    },
    "groupby_count": {
        "name": "groupby_count",
        "description": "按类别字段分组计数",
        "args_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "分组字段名"},
                "value": {"type": "string", "description": "计数的字段名"}
            },
            "required": ["group_by"]
        }
    },
    "groupby_mean": {
        "name": "groupby_mean",
        "description": "按类别字段分组计算数值字段的平均值",
        "args_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "分组字段名"},
                "value": {"type": "string", "description": "要计算平均的数值字段名"}
            },
            "required": ["group_by", "value"]
        }
    },
    "groupby_max": {
        "name": "groupby_max",
        "description": "按类别字段分组计算数值字段的最大值",
        "args_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "分组字段名"},
                "value": {"type": "string", "description": "要计算最大值的数值字段名"}
            },
            "required": ["group_by", "value"]
        }
    },
    "groupby_min": {
        "name": "groupby_min",
        "description": "按类别字段分组计算数值字段的最小值",
        "args_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "分组字段名"},
                "value": {"type": "string", "description": "要计算最小值的数值字段名"}
            },
            "required": ["group_by", "value"]
        }
    },
    "trend_analysis": {
        "name": "trend_analysis",
        "description": "分析时间序列趋势，按指定周期汇总",
        "args_schema": {
            "type": "object",
            "properties": {
                "date_col": {"type": "string", "description": "日期字段名"},
                "value": {"type": "string", "description": "要分析趋势的数值字段"},
                "freq": {"type": "string", "description": "周期，D/W/M/Q/Y", "enum": ["D", "W", "M", "Q", "Y"]}
            },
            "required": ["date_col", "value"]
        }
    },
    "topn_analysis": {
        "name": "topn_analysis",
        "description": "找出排名前N的数据",
        "args_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "排序依据的数值字段"},
                "n": {"type": "integer", "description": "返回前N条", "default": 10},
                "group_by": {"type": "string", "description": "可选，按某字段分组后再排序"}
            },
            "required": ["value"]
        }
    },
    "correlation_analysis": {
        "name": "correlation_analysis",
        "description": "分析两个数值字段之间的相关性",
        "args_schema": {
            "type": "object",
            "properties": {
                "col1": {"type": "string", "description": "第一个数值字段"},
                "col2": {"type": "string", "description": "第二个数值字段"}
            },
            "required": ["col1", "col2"]
        }
    },
    "outlier_detection": {
        "name": "outlier_detection",
        "description": "检测数据中的异常值",
        "args_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "要检测的数值字段"},
                "method": {"type": "string", "description": "检测方法", "enum": ["iqr", "zscore"], "default": "iqr"}
            },
            "required": ["column"]
        }
    },
    "describe": {
        "name": "describe",
        "description": "生成描述性统计信息",
        "args_schema": {
            "type": "object",
            "properties": {
                "columns": {"type": "array", "items": {"type": "string"}, "description": "要统计的字段列表"}
            }
        }
    },
    "filter": {
        "name": "filter",
        "description": "根据条件筛选数据",
        "args_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "筛选字段"},
                "operator": {"type": "string", "description": "操作符", "enum": ["==", "!=", ">", "<", ">=", "<=", "contains"]},
                "value": {"type": "string", "description": "筛选值"}
            },
            "required": ["column", "operator", "value"]
        }
    },
    "sort": {
        "name": "sort",
        "description": "对数据排序",
        "args_schema": {
            "type": "object",
            "properties": {
                "columns": {"type": "array", "items": {"type": "string"}, "description": "排序列"},
                "ascending": {"type": "boolean", "description": "升序还是降序", "default": True}
            },
            "required": ["columns"]
        }
    },
    "generate_chart": {
        "name": "generate_chart",
        "description": "生成数据可视化图表",
        "args_schema": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "description": "图表类型", "enum": ["bar", "line", "pie", "scatter", "histogram"]},
                "title": {"type": "string", "description": "图表标题"},
                "data": {"type": "object", "description": "图表数据，x轴和y轴数据"}
            },
            "required": ["chart_type"]
        }
    },
    "generate_report": {
        "name": "generate_report",
        "description": "生成数据分析报告",
        "args_schema": {
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "报告类型", "enum": ["markdown", "word"], "default": "markdown"},
                "title": {"type": "string", "description": "报告标题"}
            }
        }
    }
}

RISK_LEVELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
}

REPORT_TEMPLATES = {
    "markdown": "# {title}\n\n**Trace ID**: {trace_id}\n\n**生成时间**: {generated_time}\n\n---\n\n## 一、数据基本信息\n\n{basic_info}\n\n## 二、分析需求\n\n{analysis_requirement}\n\n## 三、分析计划\n\n{analysis_plan}\n\n## 四、ReAct执行过程\n\n{react_steps}\n\n## 五、分析结果\n\n{analysis_results}\n\n## 六、图表展示\n\n{chart_info}\n\n## 七、分析结论\n\n{conclusions}\n\n---\n\n*本报告由智能数据分析平台自动生成*\n",
}

REACT_FALLBACK_PLAN = {
    "thought": "无法解析模型输出或LLM未返回有效结果，改用默认数据画像分析。",
    "action": "data_profile",
    "action_input": {},
    "need_human_review": False
}
