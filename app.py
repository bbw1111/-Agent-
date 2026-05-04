import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

from config import (
    BASE_DIR, OUTPUTS_DIR, CHARTS_DIR, REPORTS_DIR, SAMPLE_DATA_DIR,
    DATABASE_DIR, DATABASE_PATH, LLM_MODES, RISK_LEVELS, LLM_PROVIDERS,
    ENABLE_HUMAN_REVIEW
)
from database.db import init_database, save_upload_record, get_analysis_history
from core.data_loader import DataLoader
from core.data_profile import DataProfiler
from core.agent_engine import AgentEngine
from core.security_guard import SecurityGuard
from core.report_generator import ReportGenerator

st.set_page_config(
    page_title="智能数据分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2E86AB;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #E0E0E0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .review-box {
        padding: 1rem;
        background-color: #fff;
        border: 2px solid #dc3545;
        border-radius: 8px;
        color: #721c24;
    }
    .step-card {
        background-color: #f8f9fa;
        border-left: 4px solid #2E86AB;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .trace-card {
        background-color: #f1f3f5;
        border: 1px solid #dee2e6;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    .api-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .api-status.configured {
        background-color: #d4edda;
        color: #155724;
    }
    .api-status.not-configured {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session():
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    if 'agent_engine' not in st.session_state:
        st.session_state.agent_engine = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'data_source' not in st.session_state:
        st.session_state.data_source = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None
    if 'current_trace_id' not in st.session_state:
        st.session_state.current_trace_id = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'agent_result' not in st.session_state:
        st.session_state.agent_result = None
    if 'react_steps' not in st.session_state:
        st.session_state.react_steps = []
    if 'pending_review' not in st.session_state:
        st.session_state.pending_review = None
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'llm_mode' not in st.session_state:
        st.session_state.llm_mode = 'rule'
    if 'llm_model' not in st.session_state:
        st.session_state.llm_model = 'qwen-turbo'

def render_dataframe(df, max_rows=20, max_height="500px"):
    if df is None or df.empty:
        st.info("无数据")
        return

    preview_df = df.head(max_rows).copy()
    preview_df.columns = [str(c).replace('"', '').replace("'", '').replace('\n', ' ').replace('\r', '').strip() for c in preview_df.columns]

    for col in preview_df.columns:
        preview_df[col] = preview_df[col].astype(str).replace('"', '').replace("'", '').replace('\n', ' ').replace('\r', '')

    html_table = preview_df.to_html(
        index=False,
        escape=True,
        border=0,
        classes='data-table'
    )

    custom_css = """
    <style>
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .data-table th {
        background-color: #2E86AB;
        color: white;
        padding: 10px 8px;
        text-align: left;
        font-weight: 600;
    }
    .data-table td {
        padding: 8px;
        border-bottom: 1px solid #eee;
        max-width: 300px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .data-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .data-table tr:hover {
        background-color: #e9ecef;
    }
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

    st.markdown(
        f'<div style="overflow-x:auto; max-height:{max_height}; border:1px solid #ddd; border-radius:8px; background:white;">'
        f'{html_table}'
        f'</div>',
        unsafe_allow_html=True
    )

def load_sample_data():
    sample_file = SAMPLE_DATA_DIR / "sales_demo.csv"
    if sample_file.exists():
        df = pd.read_csv(sample_file)
        loader = DataLoader()
        loader.df = df
        loader.file_name = "sales_demo.csv"
        return loader, df
    return None, None

def check_api_status(provider='qwen'):
    provider_config = LLM_PROVIDERS.get(provider, {})
    env_key = provider_config.get('env_key')

    api_key = st.session_state.get('api_key')

    if api_key and api_key.strip():
        return True, "已配置"

    if env_key:
        env_api_key = os.environ.get(env_key)
        if env_api_key and env_api_key.strip():
            return True, "已配置"

    return False, "未配置"

def main():
    initialize_session()
    init_database()

    st.markdown('<h1 class="main-header">📊 基于智能 Agent 的数据分析与可视化平台</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## ⚙️ 系统设置")

        with st.expander("📁 文件上传", expanded=True):
            uploaded_file = st.file_uploader(
                "上传 CSV 或 Excel 文件",
                type=['csv', 'xlsx', 'xls'],
                help="支持 CSV、Excel 格式文件"
            )

            if uploaded_file is not None:
                try:
                    loader = DataLoader()
                    df = loader.load_file(uploaded_file)

                    st.session_state.data_loader = loader
                    st.session_state.df = df
                    st.session_state.current_data = df
                    st.session_state.data_source = uploaded_file.name
                    st.session_state.file_name = uploaded_file.name
                    st.session_state.agent_engine = AgentEngine(
                        df,
                        llm_provider='qwen',
                        llm_config={}
                    )
                    st.session_state.analysis_results = None
                    st.session_state.react_steps = []
                    st.session_state.pending_review = None
                    st.session_state.report_path = None
                    st.session_state.trace_id = None
                    st.success(f"✅ 文件 '{uploaded_file.name}' 加载成功！共 {len(df)} 行，{len(df.columns)} 列")

                except Exception as e:
                    st.error(f"❌ 文件读取失败: {str(e)}")
                    st.session_state.df = None
                    st.session_state.current_data = None
                    st.session_state.data_source = None

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 加载示例数据", use_container_width=True):
                    loader, df = load_sample_data()
                    if loader:
                        st.session_state.data_loader = loader
                        st.session_state.df = df
                        st.session_state.current_data = df
                        st.session_state.data_source = "sales_demo.csv"
                        st.session_state.file_name = "sales_demo.csv"
                        st.session_state.agent_engine = AgentEngine(
                            df,
                            llm_provider='qwen',
                            llm_config={}
                        )
                        st.session_state.analysis_results = None
                        st.session_state.react_steps = []
                        st.session_state.pending_review = None
                        st.session_state.report_path = None
                        st.session_state.trace_id = None
                        st.success("示例数据加载成功！")
                        st.rerun()

            with col2:
                if st.button("🗑️ 清空数据", use_container_width=True):
                    keys_to_clear = [
                        'data_loader', 'df', 'current_data', 'data_source', 'file_name',
                        'agent_engine', 'analysis_results', 'analysis_result', 'agent_result',
                        'result', 'react_steps', 'pending_review', 'report_path',
                        'trace_id', 'current_trace_id'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            st.session_state[key] = None
                    st.rerun()

        st.divider()

        with st.expander("🤖 模型设置", expanded=True):
            llm_mode = st.selectbox(
                "分析模式",
                options=list(LLM_MODES.keys()),
                format_func=lambda x: LLM_MODES[x],
                index=0,
                help="规则模拟模式无需API Key可直接使用"
            )

            api_configured, api_status_text = check_api_status(llm_mode)
            status_class = "configured" if api_configured else "not-configured"
            st.markdown(f"**API状态**: <span class='api-status {status_class}'>{api_status_text}</span>", unsafe_allow_html=True)

            if llm_mode != 'rule' and not api_configured:
                st.warning("⚠️ 未检测到 API Key，系统将自动切换为本地规则分析模式。")

            if llm_mode != 'rule':
                st.markdown("**🔑 API Key 配置**")
                default_key = st.session_state.get('api_key', '')
                api_key_input = st.text_input(
                    "API Key",
                    type="password",
                    value=default_key,
                    help=f"请输入 {LLM_PROVIDERS.get(llm_mode, {}).get('name', 'LLM')} 的 API Key",
                    placeholder="sk-xxxxxxxx"
                )
                if api_key_input:
                    st.session_state.api_key = api_key_input

                if llm_mode == 'qwen':
                    st.info("💡 通义千问: https://dashscope.console.aliyun.com/")
                    default_model = st.session_state.get('llm_model', 'qwen-turbo')
                    model_idx = 0
                    if default_model in LLM_PROVIDERS['qwen']['models']:
                        model_idx = LLM_PROVIDERS['qwen']['models'].index(default_model)
                    llm_model = st.selectbox(
                        "选择模型",
                        options=LLM_PROVIDERS['qwen']['models'],
                        index=model_idx,
                        help="推荐使用 qwen-turbo"
                    )
                    st.session_state.llm_model = llm_model
                elif llm_mode == 'openai':
                    default_model = st.session_state.get('llm_model', 'gpt-4')
                    model_idx = 0
                    if default_model in LLM_PROVIDERS['openai']['models']:
                        model_idx = LLM_PROVIDERS['openai']['models'].index(default_model)
                    llm_model = st.selectbox(
                        "选择模型",
                        options=LLM_PROVIDERS['openai']['models'],
                        index=model_idx
                    )
                    st.session_state.llm_model = llm_model
                else:
                    llm_model = st.session_state.get('llm_model', 'qwen-turbo')
            else:
                api_key_input = None
                llm_model = None

            chart_type = st.selectbox(
                "图表类型",
                options=['auto', 'bar', 'line', 'pie', 'scatter', 'histogram'],
                format_func=lambda x: {
                    'auto': '自动选择', 'bar': '柱状图', 'line': '折线图',
                    'pie': '饼图', 'scatter': '散点图', 'histogram': '直方图'
                }.get(x, x),
                index=0
            )

        st.divider()

        with st.expander("🛡️ 安全设置", expanded=True):
            enable_review = st.checkbox("启用人工审核", value=ENABLE_HUMAN_REVIEW, help="高风险操作需要人工确认")
            save_records = st.checkbox("保存分析记录", value=True, help="是否保存分析过程到数据库")

        st.divider()

        with st.expander("📜 历史记录", expanded=True):
            history = get_analysis_history(10)
            if history:
                for record in history[:5]:
                    with st.container():
                        st.text(f"Trace: {record['trace_id'][:8]}...")
                        st.text(f"问题: {record['user_question'][:30]}...")
                        st.text(f"状态: {record['status']}")
                        st.divider()
            else:
                st.info("暂无历史记录")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 数据预览", "🔍 数据画像", "💬 智能分析", "📋 分析结果", "📤 报告导出"
    ])

    with tab1:
        st.markdown("### 📊 数据预览")

        if st.session_state.df is not None:
            df = st.session_state.df
            data_source = getattr(st.session_state, 'data_source', '未知')

            st.info(f"📁 当前数据来源: **{data_source}**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("数据行数", f"{len(df):,}")
            with col2:
                st.metric("数据列数", len(df.columns))
            with col3:
                st.metric("完整行数", f"{len(df.dropna()):,}")
            with col4:
                missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
                st.metric("缺失率", f"{missing_pct:.2f}%")

            st.markdown("#### 数据预览（前20行）")

            st.write("字段列表：", list(df.columns))
            st.write("数据形状：", df.shape)

            try:
                render_dataframe(df, max_rows=20, max_height="400px")
            except Exception as e:
                st.error(f"数据表格渲染失败：{e}")
                st.write("原始数据预览（前20行）：")
                st.write(df.head(20).to_dict(orient="records"))

            st.markdown("#### 字段信息")
            columns_info = []
            for col in df.columns:
                columns_info.append({
                    "字段名": col,
                    "数据类型": str(df[col].dtype),
                    "非空数量": int(df[col].count()),
                    "缺失数量": int(df[col].isnull().sum()),
                    "唯一值数量": int(df[col].nunique())
                })

            try:
                render_dataframe(pd.DataFrame(columns_info), max_rows=50, max_height="300px")
            except Exception as e:
                st.error(f"字段信息渲染失败：{e}")
                for info in columns_info:
                    st.write(info)

        else:
            st.info("👆 请上传 CSV/Excel 文件或点击「加载示例数据」开始分析")

            sample_file = SAMPLE_DATA_DIR / "sales_demo.csv"
            if sample_file.exists():
                st.markdown("---")
                st.markdown("**示例数据预览：**")
                try:
                    sample_df = pd.read_csv(sample_file, encoding='utf-8-sig')
                    sample_df.columns = [str(c).strip().replace('\ufeff', '') for c in sample_df.columns]
                    render_dataframe(sample_df.head(10), max_rows=10, max_height="300px")
                except Exception as e:
                    st.warning(f"示例数据加载失败：{e}")
                    st.write("请上传您自己的数据文件")

    with tab2:
        st.markdown("### 🔍 数据画像")

        if st.session_state.df is not None:
            df = st.session_state.df
            profiler = DataProfiler(df)
            profile = profiler.generate_profile()

            if profile:
                st.markdown("#### 基本信息")
                basic = profile['basic_info']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总行数", f"{basic['total_rows']:,}")
                with col2:
                    st.metric("总列数", f"{basic['total_columns']}")
                with col3:
                    st.metric("内存占用", f"{basic['memory_usage']:.2f} MB")
                with col4:
                    st.metric("重复行", f"{basic['duplicate_rows']:,}")

                st.markdown("#### 字段分类")
                types = profile['column_types']

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📈 数值字段**")
                    if types['numeric']:
                        for col in types['numeric']:
                            st.text(f"  • {col}")
                    else:
                        st.text("  无")

                with col2:
                    st.markdown("**🏷️ 类别字段**")
                    if types['categorical']:
                        for col in types['categorical']:
                            st.text(f"  • {col}")
                    else:
                        st.text("  无")

                if profile['numeric_summary']:
                    st.markdown("#### 数值字段统计")
                    for col, stats in profile['numeric_summary'].items():
                        with st.expander(f"📊 {col}"):
                            c1, c2, c3, c4 = st.columns(4)
                            with c1:
                                st.metric("平均值", f"{stats['mean']:.2f}")
                            with c2:
                                st.metric("标准差", f"{stats['std']:.2f}")
                            with c3:
                                st.metric("最小值", f"{stats['min']:.2f}")
                            with c4:
                                st.metric("最大值", f"{stats['max']:.2f}")

        else:
            st.info("请先加载数据")

    with tab3:
        st.markdown("### 💬 智能分析")

        if st.session_state.df is not None:
            df = st.session_state.df

            st.markdown("#### 📝 输入分析需求")
            user_question = st.text_area(
                "请输入您的分析问题",
                placeholder="例如：分析不同地区的销售额、生成数据画像、找出销售额最高的前10个商品",
                height=80
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                analyze_button = st.button("🚀 启动 Agent 分析", type="primary", use_container_width=True)

            if analyze_button and user_question:
                security = SecurityGuard()
                is_valid, msg_or_warnings, risk_level, warnings = security.check_analysis_request(
                    user_question, list(df.columns)
                )

                if not is_valid:
                    st.error(f"❌ {msg_or_warnings}")
                    return

                llm_config = {}
                if llm_mode != 'rule':
                    effective_api_key = st.session_state.get('api_key') or api_key_input
                    effective_model = st.session_state.get('llm_model') or llm_model
                    if effective_api_key and effective_api_key.strip():
                        llm_config = {'api_key': effective_api_key, 'model': effective_model}

                with st.spinner("🤔 Agent 正在推理分析..."):
                    if st.session_state.agent_engine is None:
                        st.session_state.agent_engine = AgentEngine(
                            df,
                            llm_provider=llm_mode,
                            llm_config=llm_config
                        )
                    else:
                        st.session_state.agent_engine.llm_provider = llm_mode
                        st.session_state.agent_engine.llm_config = llm_config
                        st.session_state.agent_engine.llm_client = None

                    result = st.session_state.agent_engine.process_user_question(
                        user_question=user_question,
                        mode=llm_mode,
                        chart_type=chart_type
                    )

                    st.session_state.result = result
                    st.session_state.analysis_results = result
                    st.session_state.analysis_result = result
                    st.session_state.agent_result = result
                    st.session_state.current_trace_id = result.get('trace_id', '')
                    st.session_state.react_steps = result.get('steps', [])

                    if result.get('need_human_review'):
                        st.session_state.pending_review = result.get('review_info')
                    else:
                        st.session_state.pending_review = None

            if st.session_state.pending_review:
                st.markdown("---")
                st.markdown("### ⚠️ 人工审核")

                review_info = st.session_state.pending_review
                st.markdown(f"""
                <div class="review-box">
                    <h4>检测到需要审核的操作</h4>
                    <p><strong>操作:</strong> {review_info.get('action', 'N/A')}</p>
                    <p><strong>参数:</strong> {str(review_info.get('action_input', {}))}</p>
                    <p><strong>风险等级:</strong> {review_info.get('risk_level', 'medium')}</p>
                    <p><strong>风险原因:</strong> {review_info.get('risk_reason', '未说明')}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 确认执行", type="primary", use_container_width=True):
                        if st.session_state.agent_engine:
                            review_result = st.session_state.agent_engine.continue_after_review(
                                approved=True,
                                reason="用户确认执行"
                            )
                            st.session_state.analysis_results = review_result
                            st.session_state.react_steps = review_result.get('steps', [])
                            st.session_state.pending_review = None
                            st.success("已执行操作")
                            st.rerun()

                with col2:
                    if st.button("❌ 拒绝执行", use_container_width=True):
                        if st.session_state.agent_engine:
                            review_result = st.session_state.agent_engine.continue_after_review(
                                approved=False,
                                reason="用户拒绝执行"
                            )
                            st.session_state.pending_review = None
                            st.warning("操作已拒绝")
                            st.rerun()

            if st.session_state.react_steps:
                st.markdown("---")
                st.markdown("### 🔄 ReAct 执行过程")

                for step_info in st.session_state.react_steps:
                    with st.expander(f"**步骤 {step_info['step']}**: {step_info['action']}", expanded=(step_info['step'] <= 2)):
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**状态**: {step_info.get('status', '')}")
                            st.markdown(f"**耗时**: {step_info.get('duration_ms', 0)} ms")

                            if step_info.get('need_review'):
                                st.warning("⏳ 需人工审核")
                            elif step_info.get('approved') is False:
                                st.error("❌ 已拒绝")
                            elif step_info.get('approved') is True:
                                st.success("✅ 已批准")

                        with col2:
                            st.markdown(f"**思维**: {step_info.get('thought', '')}")
                            st.markdown(f"**动作**: `{step_info.get('action', '')}`")
                            if step_info.get('action_input'):
                                st.markdown(f"**参数**: `{str(step_info.get('action_input', {}))}`")
                            st.markdown(f"**结果**: {step_info.get('observation', '')}")

            if st.session_state.analysis_results:
                result = st.session_state.analysis_results

                if result.get('success') and not result.get('need_human_review'):
                    st.markdown("---")
                    st.success("✅ 分析完成！")

                    if result.get('final_answer'):
                        st.markdown("#### 💡 分析结论")
                        st.markdown(result['final_answer'])

        else:
            st.info("请先加载数据")

    with tab4:
        st.markdown("### 📋 分析结果详情")

        result = st.session_state.get("result")

        if result:
            task_type = result.get('task_type', '')
            result_status = result.get('status', 'success')
            result_success = result.get('success', result_status == 'success')

            if result_status == 'error' or result_success is False:
                st.error("❌ 分析失败")
                error_msg = result.get('error', '未知错误')
                if error_msg:
                    st.code(error_msg)
                final_answer = result.get('final_answer', '')
                if final_answer:
                    st.markdown("#### 💡 分析结果")
                    st.markdown(final_answer)
                st.markdown("#### 📋 返回信息")
                st.json(result)
            elif result_success or result_status == 'success':
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Trace ID", (result.get('trace_id') or 'N/A')[:12])
                with col2:
                    st.metric("风险等级", result.get('risk_level', '未知'))

                if result.get('user_question'):
                    st.markdown("#### 用户问题")
                    st.info(result.get('user_question', ''))

                st.markdown("#### 任务类型")
                if task_type == 'general_chat':
                    st.markdown("🤖 **通用问答**")
                elif task_type == 'data_analysis':
                    st.markdown("📊 **数据分析**")
                else:
                    st.markdown("❓ **不明确**")

                if task_type == 'general_chat':
                    final_answer = result.get('final_answer', '')
                    if final_answer:
                        st.markdown("#### 💬 AI 回答")
                        st.markdown(final_answer)
                elif task_type == 'data_analysis':
                    final_answer = result.get('final_answer', '')
                    if not final_answer:
                        final_answer = result.get('summary', '')

                    if final_answer:
                        st.markdown("#### 💡 最终结论")
                        st.markdown(final_answer)

                    summary = result.get('summary', '')
                    if summary and summary != final_answer:
                        st.markdown("#### 📝 分析摘要")
                        st.markdown(summary)

                    data_table = result.get('data_table')
                    if data_table is not None:
                        st.markdown("#### 📊 统计数据")
                        if isinstance(data_table, pd.DataFrame) and not data_table.empty:
                            try:
                                render_dataframe(data_table, max_rows=50, max_height="400px")
                            except Exception as e:
                                st.error(f"数据表格渲染失败：{e}")
                                st.write(data_table)
                        elif isinstance(data_table, dict):
                            st.json(data_table)
                        else:
                            st.write(data_table)

                    if result.get('steps'):
                        st.markdown("#### 🔄 分析链路")
                        steps_df = pd.DataFrame(result['steps'])
                        if not steps_df.empty:
                            display_cols = ['step', 'thought', 'action', 'status', 'duration_ms']
                            available_cols = [c for c in display_cols if c in steps_df.columns]
                            try:
                                render_dataframe(steps_df[available_cols], max_rows=50, max_height="400px")
                            except Exception as e:
                                st.error(f"分析链路表格渲染失败：{e}")
                                for _, row in steps_df[available_cols].iterrows():
                                    st.write(row.to_dict())
                else:
                    final_answer = result.get('final_answer', '')
                    if final_answer:
                        st.markdown("#### 💡 提示")
                        st.markdown(final_answer)

                charts = result.get('charts', [])
                chart_error = result.get('error', '')
                if task_type == 'data_analysis':
                    if charts:
                        st.markdown("#### 📈 生成的图表")
                        for chart_info in charts:
                            chart_path = chart_info.get('path')
                            if chart_path and Path(chart_path).exists():
                                st.image(chart_path, caption=f"{chart_info.get('type', '图表')}")
                    elif chart_error:
                        st.warning(f"⚠️ 图表生成失败：{chart_error}")

                with st.expander("🔧 调试信息"):
                    st.json(result)

        else:
            st.info("请先在「智能分析」页面进行数据分析")

    with tab5:
        st.markdown("### 📤 报告导出")

        result = st.session_state.get("result") or st.session_state.get("analysis_result") or st.session_state.get("agent_result") or st.session_state.get("analysis_results")

        if not result:
            st.warning("⚠️ 暂无分析结果，请先在「智能分析」页面进行数据分析")
        elif not st.session_state.df is None and len(st.session_state.df) == 0:
            st.warning("⚠️ 数据已清空，请重新上传或加载数据")
        else:
            col1, col2 = st.columns(2)
            with col1:
                report_format = st.selectbox("报告格式", ["markdown", "word"])
            with col2:
                include_charts = st.checkbox("包含图表路径", value=True)

            if st.button("📄 生成报告", type="primary", use_container_width=True):
                try:
                    with st.spinner("正在生成报告..."):
                        report_gen = ReportGenerator(st.session_state.df)

                        react_steps = result.get("steps") or []
                        react_steps_str = ""
                        if react_steps:
                            for s in react_steps:
                                step_num = s.get('step', '')
                                action = s.get('action', '')
                                observation = str(s.get('observation', ''))[:100]
                                react_steps_str += f"\n- 步骤{step_num}: {action} - {observation}"
                        else:
                            react_steps_str = "本次分析未记录详细Agent执行步骤。"

                        file_name = getattr(st.session_state, 'file_name', None) or 'N/A'

                        analysis_data = {
                            'title': '智能数据分析报告',
                            'basic_info': {
                                'row_count': len(st.session_state.df) if st.session_state.df is not None else 0,
                                'column_count': len(st.session_state.df.columns) if st.session_state.df is not None else 0,
                                'file_name': file_name,
                                'numeric_columns': list(st.session_state.df.select_dtypes(include=['number']).columns) if st.session_state.df is not None else [],
                                'categorical_columns': list(st.session_state.df.select_dtypes(include=['object', 'category']).columns) if st.session_state.df is not None else []
                            },
                            'user_question': result.get('user_question', ''),
                            'summary': result.get('summary', ''),
                            'final_answer': result.get('final_answer', ''),
                            'data_table': result.get('data_table'),
                            'analysis_plan': result.get('analysis_plan', ''),
                            'react_steps': react_steps_str,
                            'analysis_results': result.get('analysis_results'),
                            'chart_paths': result.get('charts', []) if include_charts else [],
                            'conclusions': [result.get('final_answer', '')] if result.get('final_answer') else [],
                            'trace_id': result.get('trace_id', ''),
                            'risk_level': result.get('risk_level', 'low')
                        }

                        trace_id = result.get('trace_id', 'unknown')

                        if report_format == 'markdown':
                            report_path, report_content = report_gen.generate_markdown_report(
                                analysis_data,
                                trace_id
                            )
                        else:
                            report_path, report_content = report_gen.generate_word_report(
                                analysis_data,
                                trace_id
                            )

                        if report_path:
                            st.session_state.report_path = report_path
                            st.success(f"✅ 报告已生成: {report_path}")
                        else:
                            st.error(f"❌ 报告生成失败: {report_content}")

                except Exception as e:
                    st.error(f"❌ 生成报告时出错: {str(e)}")

            if st.session_state.report_path and Path(st.session_state.report_path).exists():
                report_path = st.session_state.report_path
                st.markdown("#### 报告预览")

                if report_path.endswith('.md'):
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    st.markdown(report_content)
                    with open(report_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ 下载报告",
                            data=f,
                            file_name=Path(report_path).name,
                            mime="text/markdown"
                        )
                elif report_path.endswith('.docx'):
                    st.info("📄 Word 报告已生成，请点击下方按钮下载查看")
                    with open(report_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ 下载 Word 报告",
                            data=f,
                            file_name=Path(report_path).name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            elif Path('outputs/reports').exists():
                existing_reports = list(Path('outputs/reports').glob('report_*.md'))
                if existing_reports:
                    latest_report = max(existing_reports, key=lambda p: p.stat().st_mtime)
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    st.markdown("#### 报告预览")
                    st.markdown(report_content)
                    with open(latest_report, 'rb') as f:
                        st.download_button(
                            label="⬇️ 下载最新报告",
                            data=f,
                            file_name=latest_report.name,
                            mime="text/markdown"
                        )

if __name__ == "__main__":
    main()
