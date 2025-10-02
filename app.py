"""
期货套保策略分析工具 - Streamlit主界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime, timedelta
import warnings

# 导入自定义模块
from data_processor import DataProcessor
from hedge_ratio_calculator import HedgeRatioCalculator
from backtest_engine import BacktestEngine, HedgeDirection
from visualizer import Visualizer
from stress_test import StressTestAnalyzer

warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="期货套保策略分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">📊 期货套保策略分析工具</h1>', unsafe_allow_html=True)

    st.markdown("""
    **工具简介：** 本工具帮助您基于历史数据评估现货与期货的套保效果，支持库存管理和采购管理两类套保需求。

    **核心功能：** 数据处理 → 套保比例计算 → 历史回测 → 可视化分析 → 压力测试
    """)

    # 侧边栏配置
    with st.sidebar:
        st.markdown("## 📋 参数配置")

        # 套保方向
        hedge_direction = st.selectbox(
            "套保方向",
            options=[
                ("库存管理（现货多头）", HedgeDirection.SHORT_HEDGE),
                ("采购管理（现货空头）", HedgeDirection.LONG_HEDGE)
            ],
            format_func=lambda x: x[0],
            help="库存管理：持有现货，卖出期货对冲价格下跌风险；采购管理：计划采购现货，买入期货对冲价格上涨风险"
        )[1]

        # 现货数量
        spot_quantity = st.number_input(
            "现货数量",
            min_value=0.1,
            value=100.0,
            step=0.1,
            help="您持有的或计划交易的现货数量"
        )

        # 期货合约代码
        future_code = st.text_input(
            "期货合约代码",
            value="CU0",
            help="期货合约代码，如CU0（沪铜主力）、AL0（沪铝主力）等"
        )

        # 计算窗口
        window_options = {
            "全部数据": None,
            "近30天": 30,
            "近60天": 60,
            "近90天": 90,
            "近120天": 120,
            "近180天": 180,
            "近360天": 360
        }

        selected_window = st.selectbox(
            "套保比例计算窗口",
            options=list(window_options.keys()),
            index=0,
            help="用于计算最优套保比例的历史数据窗口"
        )
        window_size = window_options[selected_window]

        # 压力测试参数
        st.markdown("### 🧪 压力测试参数")
        stress_threshold = st.slider(
            "价格变化阈值 (%)",
            min_value=1.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            help="识别压力时期的价格日变化阈值"
        )

        consecutive_days = st.number_input(
            "最少连续天数",
            min_value=1,
            max_value=10,
            value=3,
            help="构成压力时期的最少连续天数"
        )

    # 主界面选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📁 数据上传", "📊 套保分析", "📈 可视化", "🧪 压力测试", "📋 结果导出"
    ])

    # 初始化session state
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if 'hedge_calculator' not in st.session_state:
        st.session_state.hedge_calculator = HedgeRatioCalculator()
    if 'backtest_engine' not in st.session_state:
        st.session_state.backtest_engine = BacktestEngine()
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = Visualizer()
    if 'stress_analyzer' not in st.session_state:
        st.session_state.stress_analyzer = StressTestAnalyzer()

    with tab1:
        st.markdown('<h2 class="section-header">📁 数据上传与处理</h2>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 现货数据上传")

            uploaded_file = st.file_uploader(
                "上传现货价格CSV文件",
                type=['csv'],
                help="CSV文件必须包含：date（日期，格式YYYY-MM-DD）和spot_price（现货价格）两列"
            )

            if uploaded_file is not None:
                try:
                    # 读取文件
                    stringio = io.StringIO(uploaded_file.getvalue().decode('utf-8'))
                    spot_data_raw = pd.read_csv(stringio)

                    st.success(f"✅ 文件读取成功，共 {len(spot_data_raw)} 行数据")

                    # 数据预览
                    st.markdown("#### 数据预览")
                    st.dataframe(spot_data_raw.head(10))

                    # 数据验证和处理
                    handle_missing = st.selectbox(
                        "缺失值处理方式",
                        options=["删除", "线性插值"],
                        help="选择如何处理现货价格中的缺失值"
                    )

                    if st.button("验证和处理数据", type="primary"):
                        with st.spinner("正在处理数据..."):
                            handle_missing_map = {"删除": "drop", "线性插值": "interpolate"}
                            spot_data, error_msg = st.session_state.data_processor.load_spot_data(
                                uploaded_file, handle_missing_map[handle_missing]
                            )

                        if error_msg:
                            st.error(f"❌ 数据处理失败：{error_msg}")
                        else:
                            st.success("✅ 数据处理成功！")
                            st.session_state.spot_data = spot_data

                            # 显示数据摘要
                            summary = st.session_state.data_processor.get_data_summary(spot_data)
                            st.markdown("#### 数据摘要")

                            col_summary1, col_summary2 = st.columns(2)
                            with col_summary1:
                                st.metric("数据行数", summary['数据行数'])
                                st.metric("时间范围", summary['时间范围'])
                            with col_summary2:
                                st.metric("价格均值", f"{summary['现货价格统计']['均值']:.2f}")
                                st.metric("价格波动率", f"{summary['现货价格统计']['波动率']:.2f}%")

                            # 显示处理后的数据
                            st.markdown("#### 处理后的数据")
                            st.dataframe(spot_data)

                except Exception as e:
                    st.error(f"❌ 文件读取失败：{str(e)}")

        with col2:
            st.markdown("### 📄 数据格式要求")

            st.markdown("""
            **CSV文件格式：**

            | date | spot_price |
            |------|------------|
            | 2023-01-01 | 68500.0 |
            | 2023-01-02 | 68200.0 |
            | 2023-01-03 | 68800.0 |

            **要求说明：**
            - 必须包含 `date` 和 `spot_price` 两列
            - 日期格式：YYYY-MM-DD
            - 价格：数值型，不能为负数
            - 建议至少包含60天以上的数据
            """)

            st.markdown("### 📥 示例数据下载")
            if st.button("下载示例数据"):
                sample_data = pd.DataFrame({
                    'date': pd.date_range('2023-01-01', periods=100, freq='D'),
                    'spot_price': np.random.normal(68000, 500, 100).cumsum()
                })
                sample_data['date'] = sample_data['date'].dt.strftime('%Y-%m-%d')
                csv = sample_data.to_csv(index=False)
                st.download_button(
                    label="下载 spot_data_sample.csv",
                    data=csv,
                    file_name="spot_data_sample.csv",
                    mime="text/csv"
                )

    with tab2:
        st.markdown('<h2 class="section-header">📊 套保分析与计算</h2>', unsafe_allow_html=True)

        if 'spot_data' not in st.session_state:
            st.warning("⚠️ 请先在数据上传页面加载现货数据")
        else:
            st.markdown("### 期货数据获取与对齐")

            # 获取期货数据
            if st.button("获取期货数据并开始分析", type="primary"):
                with st.spinner("正在获取期货数据..."):
                    try:
                        # 获取现货数据的时间范围
                        start_date = st.session_state.spot_data['date'].min().strftime('%Y-%m-%d')
                        end_date = st.session_state.spot_data['date'].max().strftime('%Y-%m-%d')

                        # 获取期货数据
                        future_data, error_msg = st.session_state.data_processor.get_future_data(
                            future_code, start_date, end_date
                        )

                        if error_msg and "缓存" not in error_msg:
                            st.error(f"❌ 期货数据获取失败：{error_msg}")
                        else:
                            st.success(f"✅ 期货数据获取成功！{'(从缓存读取)' if '缓存' in error_msg else ''}")
                            st.session_state.future_data = future_data

                            # 数据对齐
                            aligned_data = st.session_state.data_processor.align_data(
                                st.session_state.spot_data, future_data
                            )
                            st.session_state.aligned_data = aligned_data

                            st.success(f"✅ 数据对齐成功！共 {len(aligned_data)} 天有效数据")

                            # 显示对齐后的数据预览
                            st.markdown("#### 对齐后的数据预览")
                            st.dataframe(aligned_data.head(10))

                            # 计算套保比例
                            st.markdown("### 套保比例计算")
                            with st.spinner("正在计算最优套保比例..."):
                                optimal_ratio, calc_results = st.session_state.hedge_calculator.calculate_optimal_hedge_ratio(
                                    aligned_data, window_size
                                )

                            st.session_state.optimal_ratio = optimal_ratio
                            st.session_state.calc_results = calc_results

                            # 验证套保比例
                            is_valid, validation_msg = st.session_state.hedge_calculator.validate_hedge_ratio(optimal_ratio)

                            if is_valid:
                                st.success(f"✅ 套保比例计算完成：{optimal_ratio:.4f}")
                            else:
                                st.warning(f"⚠️ 套保比例：{optimal_ratio:.4f} ({validation_msg})")

                            # 显示计算结果
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("最优套保比例", f"{optimal_ratio:.4f}")
                                st.metric("R²", f"{calc_results['regression_results']['r_squared']:.4f}")
                            with col2:
                                st.metric("相关性", f"{calc_results['correlation_analysis']['correlation']:.4f}")
                                st.metric("F统计量", f"{calc_results['regression_results']['f_statistic']:.2f}")
                            with col3:
                                st.metric("数据点数", calc_results['data_points'])
                                st.metric("使用窗口", calc_results['window_used'])

                            # 运行回测
                            st.markdown("### 历史回测")
                            with st.spinner("正在运行历史回测..."):
                                backtest_results = st.session_state.backtest_engine.run_backtest(
                                    aligned_data, optimal_ratio, spot_quantity, hedge_direction
                                )

                            st.session_state.backtest_results = backtest_results
                            st.success("✅ 历史回测完成！")

                            # 显示回测摘要
                            summary = st.session_state.backtest_engine.generate_performance_summary()
                            st.session_state.visualizer.create_performance_dashboard(summary)

                    except Exception as e:
                        st.error(f"❌ 分析过程出错：{str(e)}")

            # 如果已有分析结果，显示详细信息
            if 'backtest_results' in st.session_state:
                st.markdown("### 📈 详细分析结果")

                backtest_results = st.session_state.backtest_results
                metrics = backtest_results['performance_metrics']

                # 盈亏分析
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**盈亏表现**")
                    pnl_data = {
                        '指标': ['套保总盈亏', '未套保总盈亏', '套保优势',
                                '平均每日盈亏(套保)', '平均每日盈亏(未套保)'],
                        '数值': [
                            f"{metrics['total_hedged_pnl']:.2f}",
                            f"{metrics['total_unhedged_pnl']:.2f}",
                            f"{metrics['total_hedged_pnl'] - metrics['total_unhedged_pnl']:.2f}",
                            f"{metrics['avg_daily_hedged_pnl']:.2f}",
                            f"{metrics['avg_daily_unhedged_pnl']:.2f}"
                        ]
                    }
                    st.dataframe(pd.DataFrame(pnl_data), hide_index=True)

                with col2:
                    st.markdown("**风险控制**")
                    risk_data = {
                        '指标': ['套保波动率', '未套保波动率', '波动率降低率',
                                '最大回撤(套保)', '最大回撤(未套保)'],
                        '数值': [
                            f"{metrics['hedged_volatility']:.2f}",
                            f"{metrics['unhedged_volatility']:.2f}",
                            f"{metrics['volatility_reduction_rate']:.2%}",
                            f"{metrics['max_drawdown_hedged']:.2f}",
                            f"{metrics['max_drawdown_unhedged']:.2f}"
                        ]
                    }
                    st.dataframe(pd.DataFrame(risk_data), hide_index=True)

                # 套保比例敏感性分析
                st.markdown("### 📊 套保比例敏感性分析")

                if st.button("运行敏感性分析"):
                    with st.spinner("正在分析不同套保比例的效果..."):
                        sensitivity_data = st.session_state.hedge_calculator.sensitivity_analysis(
                            st.session_state.aligned_data,
                            st.session_state.optimal_ratio
                        )
                        st.session_state.sensitivity_data = sensitivity_data

                if 'sensitivity_data' in st.session_state:
                    # 敏感性分析结果
                    sensitivity_fig = st.session_state.visualizer.plot_sensitivity_analysis(
                        st.session_state.sensitivity_data, st.session_state.optimal_ratio
                    )
                    st.plotly_chart(sensitivity_fig, use_container_width=True)

    with tab3:
        st.markdown('<h2 class="section-header">📈 可视化分析</h2>', unsafe_allow_html=True)

        if 'aligned_data' not in st.session_state:
            st.warning("⚠️ 请先完成套保分析")
        else:
            # 价格对比图
            st.markdown("### 价格走势对比")
            price_fig = st.session_state.visualizer.plot_price_comparison(st.session_state.aligned_data)
            st.plotly_chart(price_fig, use_container_width=True)

            # 盈亏对比图
            if 'backtest_results' in st.session_state:
                st.markdown("### 盈亏对比分析")
                pnl_fig = st.session_state.visualizer.plot_pnl_comparison(
                    st.session_state.backtest_results['data']
                )
                st.plotly_chart(pnl_fig, use_container_width=True)

                # 风险指标雷达图
                st.markdown("### 风险指标对比")
                radar_fig = st.session_state.visualizer.plot_risk_metrics_radar(
                    st.session_state.backtest_results['performance_metrics']
                )
                st.plotly_chart(radar_fig, use_container_width=True)

    with tab4:
        st.markdown('<h2 class="section-header">🧪 压力测试</h2>', unsafe_allow_html=True)

        if 'backtest_results' not in st.session_state:
            st.warning("⚠️ 请先完成套保分析")
        else:
            st.markdown("### 压力测试配置")

            # 自动识别压力时期
            if st.button("识别压力时期并运行测试", type="primary"):
                with st.spinner("正在识别压力时期并分析..."):
                    try:
                        # 识别压力时期
                        stress_periods = st.session_state.stress_analyzer.identify_stress_periods(
                            st.session_state.aligned_data, stress_threshold, consecutive_days
                        )

                        if not stress_periods:
                            st.info("ℹ️ 未发现明显的压力时期，可以尝试降低阈值或减少最少连续天数")
                        else:
                            st.success(f"✅ 识别到 {len(stress_periods)} 个压力时期")

                            # 显示压力时期
                            st.markdown("#### 识别到的压力时期")
                            period_df = pd.DataFrame(stress_periods)
                            st.dataframe(period_df[['start_date', 'end_date', 'duration_days', 'stress_type',
                                                 'spot_price_change_pct', 'max_daily_spot_change']])

                            # 运行压力测试
                            stress_results = st.session_state.stress_analyzer.run_stress_test(
                                st.session_state.backtest_results, stress_periods
                            )

                            st.session_state.stress_results = stress_results
                            st.success("✅ 压力测试完成！")

                            # 显示压力测试摘要
                            summary = stress_results.get('summary', {})
                            if summary:
                                st.markdown("### 压力测试摘要")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("压力时期数量", summary.get('total_stress_periods', 0))
                                    st.metric("总天数", summary.get('total_stress_days', 0))
                                with col2:
                                    st.metric("套保有效性", f"{summary.get('stress_effectiveness', 0):.2%}")
                                    st.metric("套保优势", f"{summary.get('total_stress_pnl_hedged', 0):.2f}")
                                with col3:
                                    st.metric("最大单日损失", f"{summary.get('max_single_loss_hedged', 0):.2f}")
                                    st.metric("相对正常时期表现", f"{summary.get('stress_vs_normal_pnl_ratio', 0):.2f}")

                    except Exception as e:
                        st.error(f"❌ 压力测试失败：{str(e)}")

            # 自定义压力测试
            st.markdown("### 自定义压力测试")
            st.markdown("选择特定时间段进行压力测试分析")

            if 'aligned_data' in st.session_state:
                min_date = st.session_state.aligned_data['date'].min().date()
                max_date = st.session_state.aligned_data['date'].max().date()

                col1, col2 = st.columns(2)
                with col1:
                    custom_start = st.date_input("开始日期", min_date, min_value=min_date, max_value=max_date)
                with col2:
                    custom_end = st.date_input("结束日期", max_date, min_value=min_date, max_value=max_date)

                if st.button("运行自定义压力测试"):
                    if custom_start >= custom_end:
                        st.error("❌ 开始日期必须早于结束日期")
                    else:
                        with st.spinner("正在运行自定义压力测试..."):
                            try:
                                custom_results = st.session_state.stress_analyzer.run_stress_test(
                                    st.session_state.backtest_results,
                                    custom_period=(custom_start.strftime('%Y-%m-%d'),
                                                custom_end.strftime('%Y-%m-%d'))
                                )
                                st.session_state.custom_stress_results = custom_results
                                st.success("✅ 自定义压力测试完成！")

                                # 显示结果
                                period_result = custom_results['stress_periods'][0]
                                st.markdown("#### 自定义时期测试结果")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("套保盈亏", f"{period_result['total_hedged_pnl']:.2f}")
                                    st.metric("未套保盈亏", f"{period_result['total_unhedged_pnl']:.2f}")
                                with col2:
                                    st.metric("套保优势", f"{period_result['hedge_advantage']:.2f}")
                                    st.metric("风险降低率", f"{period_result['risk_reduction_rate']:.2%}")

                            except Exception as e:
                                st.error(f"❌ 自定义压力测试失败：{str(e)}")

            # 压力测试图表
            if 'stress_results' in st.session_state:
                st.markdown("### 压力测试结果对比")
                stress_results = st.session_state.stress_results
                normal_data = stress_results.get('normal_period_comparison', {})

                if stress_results.get('stress_periods'):
                    # 聚合压力时期数据用于对比
                    stress_agg = {
                        'total_hedged_pnl': sum(p['total_hedged_pnl'] for p in stress_results['stress_periods']),
                        'total_unhedged_pnl': sum(p['total_unhedged_pnl'] for p in stress_results['stress_periods']),
                        'avg_daily_hedged_pnl': np.mean([p['avg_daily_hedged_pnl'] for p in stress_results['stress_periods']]),
                        'avg_daily_unhedged_pnl': np.mean([p['avg_daily_unhedged_pnl'] for p in stress_results['stress_periods']]),
                        'max_daily_loss_hedged': min(p['max_daily_loss_hedged'] for p in stress_results['stress_periods']),
                        'max_daily_loss_unhedged': min(p['max_daily_loss_unhedged'] for p in stress_results['stress_periods']),
                        'hedged_volatility': np.mean([p['hedged_volatility'] for p in stress_results['stress_periods']]),
                        'unhedged_volatility': np.mean([p['unhedged_volatility'] for p in stress_results['stress_periods']]),
                        'profitable_days_hedged': sum(p['profitable_days_hedged'] for p in stress_results['stress_periods']),
                        'profitable_days_unhedged': sum(p['profitable_days_unhedged'] for p in stress_results['stress_periods']),
                        'days': sum(p['days'] for p in stress_results['stress_periods'])
                    }

                    stress_fig = st.session_state.visualizer.plot_stress_test_results(
                        stress_agg, normal_data
                    )
                    st.plotly_chart(stress_fig, use_container_width=True)

            # 压力测试报告
            if 'stress_results' in st.session_state:
                st.markdown("### 压力测试报告")
                report = st.session_state.stress_analyzer.generate_stress_test_report()
                st.markdown(report)

    with tab5:
        st.markdown('<h2 class="section-header">📋 结果导出</h2>', unsafe_allow_html=True)

        if 'backtest_results' not in st.session_state:
            st.warning("⚠️ 暂无可导出的结果，请先完成分析")
        else:
            st.markdown("### 导出分析结果")

            # 导出回测数据
            if 'backtest_results' in st.session_state:
                st.markdown("#### 回测详细数据")
                backtest_data = st.session_state.backtest_results['data']

                csv_data = backtest_data.to_csv(index=False)
                st.download_button(
                    label="下载回测详细数据 (CSV)",
                    data=csv_data,
                    file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            # 导出敏感性分析数据
            if 'sensitivity_data' in st.session_state:
                st.markdown("#### 敏感性分析数据")
                sensitivity_csv = st.session_state.sensitivity_data.to_csv(index=False)
                st.download_button(
                    label="下载敏感性分析数据 (CSV)",
                    data=sensitivity_csv,
                    file_name=f"sensitivity_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            # 导出压力测试结果
            if 'stress_results' in st.session_state:
                st.markdown("#### 压力测试结果")

                if st.button("导出压力测试结果"):
                    try:
                        export_path = f"stress_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        st.session_state.stress_analyzer.export_stress_test_results(export_path)

                        # 读取并下载文件
                        with open(export_path, 'r', encoding='utf-8-sig') as f:
                            export_data = f.read()

                        st.download_button(
                            label="下载压力测试结果 (CSV)",
                            data=export_data,
                            file_name=export_path,
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"❌ 导出失败：{str(e)}")

            # 生成完整分析报告
            st.markdown("#### 完整分析报告")
            if st.button("生成完整报告"):
                report_sections = []

                # 套保参数
                hedge_params = st.session_state.backtest_results['hedge_parameters']
                report_sections.append(f"# 期货套保策略分析报告\n")
                report_sections.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                report_sections.append(f"## 分析参数\n")
                report_sections.append(f"- 套保方向：{'库存管理（卖出套保）' if hedge_params['hedge_direction'] == 'short_hedge' else '采购管理（买入套保）'}")
                report_sections.append(f"- 现货数量：{hedge_params['spot_quantity']}")
                report_sections.append(f"- 最优套保比例：{hedge_params['hedge_ratio']:.4f}")
                report_sections.append(f"- 期货合约代码：{future_code}\n")

                # 绩效摘要
                summary = st.session_state.backtest_engine.generate_performance_summary()
                report_sections.append(f"## 绩效摘要\n")
                for category, metrics in summary.items():
                    report_sections.append(f"### {category}\n")
                    for metric, value in metrics.items():
                        report_sections.append(f"- {metric}：{value}")
                    report_sections.append("")

                # 压力测试结果
                if 'stress_results' in st.session_state:
                    stress_report = st.session_state.stress_analyzer.generate_stress_test_report()
                    report_sections.append(stress_report)

                complete_report = "\n".join(report_sections)
                st.download_button(
                    label="下载完整分析报告 (Markdown)",
                    data=complete_report,
                    file_name=f"hedge_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>📊 期货套保策略分析工具 | 专业的套保效果评估平台</p>
        <p style='font-size: 0.8em;'>本工具仅供学习和研究使用，投资决策请谨慎</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()