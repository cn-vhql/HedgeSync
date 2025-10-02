"""
可视化模块
负责生成各种图表展示套保分析结果
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional, Tuple
import pyecharts.options as opts
from pyecharts.charts import Line, Bar, Radar, Scatter


class Visualizer:
    """可视化器类"""

    def __init__(self):
        """初始化可视化器"""
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8'
        }

    def plot_price_comparison(self, data: pd.DataFrame) -> go.Figure:
        """
        绘制现货与期货价格对比图

        Args:
            data: 包含现货和期货价格的数据

        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('价格走势对比', '价格相关性'),
            vertical_spacing=0.15,
            row_heights=[0.7, 0.3]
        )

        # 价格走势
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['spot_price'],
                mode='lines',
                name='现货价格',
                line=dict(color=self.color_scheme['primary'], width=2),
                hovertemplate='日期: %{x}<br>现货价格: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['future_price'],
                mode='lines',
                name='期货价格',
                line=dict(color=self.color_scheme['secondary'], width=2),
                yaxis='y2',
                hovertemplate='日期: %{x}<br>期货价格: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # 散点图展示相关性
        fig.add_trace(
            go.Scatter(
                x=data['spot_price'],
                y=data['future_price'],
                mode='markers',
                name='价格相关性',
                marker=dict(color=self.color_scheme['info'], size=4, opacity=0.6),
                hovertemplate='现货价格: %{x:.2f}<br>期货价格: %{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # 设置布局
        fig.update_layout(
            title='现货与期货价格对比分析',
            height=800,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # 设置Y轴
        fig.update_yaxes(title_text="现货价格", row=1, col=1)
        fig.update_yaxes(title_text="期货价格", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="期货价格", row=2, col=1)
        fig.update_xaxes(title_text="现货价格", row=2, col=1)
        fig.update_xaxes(title_text="日期", row=1, col=1)

        return fig

    def plot_pnl_comparison(self, backtest_data: pd.DataFrame) -> go.Figure:
        """
        绘制套保与未套保盈亏对比图

        Args:
            backtest_data: 回测数据

        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('累计盈亏对比', '每日盈亏', '盈亏分布'),
            vertical_spacing=0.12,
            row_heights=[0.5, 0.3, 0.2]
        )

        # 累计盈亏对比
        fig.add_trace(
            go.Scatter(
                x=backtest_data['date'],
                y=backtest_data['total_pnl_cumulative'],
                mode='lines',
                name='套保累计盈亏',
                line=dict(color=self.color_scheme['success'], width=2.5),
                hovertemplate='日期: %{x}<br>套保累计盈亏: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=backtest_data['date'],
                y=backtest_data['unhedged_pnl_cumulative'],
                mode='lines',
                name='未套保累计盈亏',
                line=dict(color=self.color_scheme['danger'], width=2.5, dash='dash'),
                hovertemplate='日期: %{x}<br>未套保累计盈亏: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # 每日盈亏柱状图
        fig.add_trace(
            go.Bar(
                x=backtest_data['date'],
                y=backtest_data['total_pnl'],
                name='套保每日盈亏',
                marker_color=[self.color_scheme['success'] if x >= 0 else self.color_scheme['danger']
                             for x in backtest_data['total_pnl']],
                hovertemplate='日期: %{x}<br>套保每日盈亏: %{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # 盈亏分布直方图
        fig.add_trace(
            go.Histogram(
                x=backtest_data['total_pnl'],
                name='套保盈亏分布',
                nbinsx=30,
                marker_color=self.color_scheme['success'],
                opacity=0.7,
                hovertemplate='盈亏区间: %{x}<br>频次: %{y}<extra></extra>'
            ),
            row=3, col=1
        )

        fig.add_trace(
            go.Histogram(
                x=backtest_data['unhedged_pnl'],
                name='未套保盈亏分布',
                nbinsx=30,
                marker_color=self.color_scheme['danger'],
                opacity=0.7,
                hovertemplate='盈亏区间: %{x}<br>频次: %{y}<extra></extra>'
            ),
            row=3, col=1
        )

        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

        # 设置布局
        fig.update_layout(
            title='套保效果对比分析',
            height=900,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='overlay'
        )

        # 设置轴标签
        fig.update_yaxes(title_text="累计盈亏", row=1, col=1)
        fig.update_yaxes(title_text="每日盈亏", row=2, col=1)
        fig.update_yaxes(title_text="频次", row=3, col=1)
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_xaxes(title_text="盈亏", row=3, col=1)

        return fig

    def plot_risk_metrics_radar(self, metrics: Dict) -> go.Figure:
        """
        绘制风险指标雷达图

        Args:
            metrics: 绩效指标字典

        Returns:
            Plotly图表对象
        """
        # 准备数据
        categories = ['波动率', '最大回撤', 'VaR(95%)', '夏普比率', '盈利天数占比']

        # 标准化数值（0-1范围）
        max_volatility = max(metrics['hedged_volatility'], metrics['unhedged_volatility'])
        max_drawdown = max(abs(metrics['max_drawdown_hedged']), abs(metrics['max_drawdown_unhedged']))
        max_var = max(abs(metrics['var_95_hedged']), abs(metrics['var_95_unhedged']))
        max_sharpe = max(abs(metrics['sharpe_ratio_hedged']), abs(metrics['sharpe_ratio_unhedged']))
        max_profit_ratio = max(metrics['profitable_days_ratio_hedged'], metrics['profitable_days_ratio_unhedged'])

        hedged_values = [
            1 - (metrics['hedged_volatility'] / max_volatility) if max_volatility > 0 else 0,  # 波动率越小越好
            1 - (abs(metrics['max_drawdown_hedged']) / max_drawdown) if max_drawdown > 0 else 0,  # 回撤越小越好
            1 - (abs(metrics['var_95_hedged']) / max_var) if max_var > 0 else 0,  # VaR越小越好
            abs(metrics['sharpe_ratio_hedged']) / max_sharpe if max_sharpe > 0 else 0,  # 夏普比率越大越好
            metrics['profitable_days_ratio_hedged'] / max_profit_ratio if max_profit_ratio > 0 else 0
        ]

        unhedged_values = [
            1 - (metrics['unhedged_volatility'] / max_volatility) if max_volatility > 0 else 0,
            1 - (abs(metrics['max_drawdown_unhedged']) / max_drawdown) if max_drawdown > 0 else 0,
            1 - (abs(metrics['var_95_unhedged']) / max_var) if max_var > 0 else 0,
            abs(metrics['sharpe_ratio_unhedged']) / max_sharpe if max_sharpe > 0 else 0,
            metrics['profitable_days_ratio_unhedged'] / max_profit_ratio if max_profit_ratio > 0 else 0
        ]

        fig = go.Figure()

        # 添加套保数据
        fig.add_trace(go.Scatterpolar(
            r=hedged_values,
            theta=categories,
            fill='toself',
            name='套保策略',
            line_color=self.color_scheme['success'],
            fillcolor=f'rgba(44, 160, 44, 0.25)'  # 将十六进制转换为RGBA格式
        ))

        # 添加未套保数据
        fig.add_trace(go.Scatterpolar(
            r=unhedged_values,
            theta=categories,
            fill='toself',
            name='未套保',
            line_color=self.color_scheme['danger'],
            fillcolor=f'rgba(214, 39, 40, 0.25)'  # 将十六进制转换为RGBA格式
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title='风险收益指标对比',
            height=500
        )

        return fig

    def plot_sensitivity_analysis(self, sensitivity_data: pd.DataFrame,
                                optimal_ratio: float) -> go.Figure:
        """
        绘制套保比例敏感性分析图

        Args:
            sensitivity_data: 敏感性分析数据
            optimal_ratio: 最优套保比例

        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('风险降低率 vs 套保比例', '套保有效性 vs 套保比例',
                          '波动率 vs 套保比例', '夏普比率 vs 套保比例'),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        # 风险降低率
        fig.add_trace(
            go.Scatter(
                x=sensitivity_data['hedge_ratio'],
                y=sensitivity_data['risk_reduction'] * 100,
                mode='lines+markers',
                name='风险降低率',
                line=dict(color=self.color_scheme['primary'], width=2),
                hovertemplate='套保比例: %{x:.4f}<br>风险降低率: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )

        # 标记最优比例
        optimal_idx = (sensitivity_data['hedge_ratio'] - optimal_ratio).abs().idxmin()
        fig.add_trace(
            go.Scatter(
                x=[sensitivity_data.loc[optimal_idx, 'hedge_ratio']],
                y=[sensitivity_data.loc[optimal_idx, 'risk_reduction'] * 100],
                mode='markers',
                name='最优比例',
                marker=dict(color=self.color_scheme['danger'], size=10),
                hovertemplate='最优套保比例: %{x:.4f}<extra></extra>'
            ),
            row=1, col=1
        )

        # 套保有效性
        fig.add_trace(
            go.Scatter(
                x=sensitivity_data['hedge_ratio'],
                y=sensitivity_data['effectiveness'] * 100,
                mode='lines+markers',
                name='套保有效性',
                line=dict(color=self.color_scheme['success'], width=2),
                showlegend=False,
                hovertemplate='套保比例: %{x:.4f}<br>套保有效性: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=2
        )

        # 波动率
        fig.add_trace(
            go.Scatter(
                x=sensitivity_data['hedge_ratio'],
                y=sensitivity_data['volatility'],
                mode='lines+markers',
                name='波动率',
                line=dict(color=self.color_scheme['warning'], width=2),
                showlegend=False,
                hovertemplate='套保比例: %{x:.4f}<br>波动率: %{y:.4f}<extra></extra>'
            ),
            row=2, col=1
        )

        # 夏普比率（计算）
        sharpe_ratios = sensitivity_data['risk_reduction'] / sensitivity_data['volatility']
        fig.add_trace(
            go.Scatter(
                x=sensitivity_data['hedge_ratio'],
                y=sharpe_ratios,
                mode='lines+markers',
                name='风险调整收益',
                line=dict(color=self.color_scheme['info'], width=2),
                showlegend=False,
                hovertemplate='套保比例: %{x:.4f}<br>风险调整收益: %{y:.4f}<extra></extra>'
            ),
            row=2, col=2
        )

        # 添加最优比例垂直线
        for row in [1, 2]:
            for col in [1, 2]:
                fig.add_vline(
                    x=optimal_ratio,
                    line_dash="dash",
                    line_color="red",
                    opacity=0.5,
                    row=row, col=col
                )

        fig.update_layout(
            title='套保比例敏感性分析',
            height=700,
            hovermode='x'
        )

        # 设置轴标签
        fig.update_xaxes(title_text="套保比例", row=2, col=1)
        fig.update_xaxes(title_text="套保比例", row=2, col=2)
        fig.update_yaxes(title_text="风险降低率 (%)", row=1, col=1)
        fig.update_yaxes(title_text="套保有效性 (%)", row=1, col=2)
        fig.update_yaxes(title_text="波动率", row=2, col=1)
        fig.update_yaxes(title_text="风险调整收益", row=2, col=2)

        return fig

    def plot_stress_test_results(self, stress_data: Dict,
                               normal_data: Dict) -> go.Figure:
        """
        绘制压力测试结果对比图

        Args:
            stress_data: 压力时期数据
            normal_data: 正常时期数据

        Returns:
            Plotly图表对象
        """
        categories = ['总盈亏', '平均每日盈亏', '最大单日亏损', '波动率', '盈利天数占比']

        stress_values = [
            stress_data['total_hedged_pnl'],
            stress_data['avg_daily_hedged_pnl'],
            stress_data['max_daily_loss_hedged'],
            stress_data['hedged_volatility'],
            stress_data['profitable_days_hedged'] / stress_data['days'] * 100
        ]

        normal_values = [
            normal_data['total_hedged_pnl'],
            normal_data['avg_daily_hedged_pnl'],
            normal_data['max_daily_loss_hedged'],
            normal_data['hedged_volatility'],
            normal_data['profitable_days_hedged'] / normal_data['days'] * 100
        ]

        fig = go.Figure()

        # 正常时期
        fig.add_trace(go.Bar(
            name='正常时期',
            x=categories,
            y=normal_values,
            marker_color=self.color_scheme['success'],
            hovertemplate='指标: %{x}<br>数值: %{y:.2f}<extra></extra>'
        ))

        # 压力时期
        fig.add_trace(go.Bar(
            name='压力时期',
            x=categories,
            y=stress_values,
            marker_color=self.color_scheme['danger'],
            hovertemplate='指标: %{x}<br>数值: %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title='压力测试结果对比',
            xaxis_title='指标',
            yaxis_title='数值',
            barmode='group',
            height=500
        )

        return fig

    def create_performance_dashboard(self, summary: Dict) -> None:
        """
        创建绩效仪表板（在Streamlit中显示）

        Args:
            summary: 绩效摘要字典
        """
        # 创建指标卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="套保总盈亏",
                value=summary['盈亏表现']['套保总盈亏'],
                delta=summary['盈亏表现']['套保优势']
            )

        with col2:
            st.metric(
                label="风险降低率",
                value=summary['风险控制']['波动率降低'],
                delta=None
            )

        with col3:
            st.metric(
                label="套保有效性",
                value=summary['风险控制']['套保有效性'],
                delta=None
            )

        with col4:
            st.metric(
                label="夏普比率",
                value=summary['其他指标']['夏普比率（套保）'],
                delta=None
            )

        # 显示详细表格
        st.subheader("详细绩效指标")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**盈亏表现**")
            pnl_data = {
                '指标': ['套保总盈亏', '未套保总盈亏', '套保优势', '平均每日盈亏(套保)', '平均每日盈亏(未套保)'],
                '数值': [
                    summary['盈亏表现']['套保总盈亏'],
                    summary['盈亏表现']['未套保总盈亏'],
                    summary['盈亏表现']['套保优势'],
                    summary['盈亏表现']['平均每日盈亏（套保）'],
                    summary['盈亏表现']['平均每日盈亏（未套保）']
                ]
            }
            st.dataframe(pd.DataFrame(pnl_data), hide_index=True)

        with col2:
            st.markdown("**风险控制**")
            risk_data = {
                '指标': ['套保波动率', '未套保波动率', '波动率降低', '最大回撤(套保)', '最大回撤(未套保)'],
                '数值': [
                    summary['风险控制']['套保波动率'],
                    summary['风险控制']['未套保波动率'],
                    summary['风险控制']['波动率降低'],
                    summary['风险控制']['最大回撤（套保）'],
                    summary['风险控制']['最大回撤（未套保）']
                ]
            }
            st.dataframe(pd.DataFrame(risk_data), hide_index=True)

    def create_echart_price_comparison(self, data: pd.DataFrame):
        """
        创建ECharts价格对比图

        Args:
            data: 价格数据

        Returns:
            ECharts图表对象
        """
        line = Line()

        # 添加X轴数据
        x_data = data['date'].dt.strftime('%Y-%m-%d').tolist()

        # 添加现货价格线
        line.add_xaxis(x_data)
        line.add_yaxis(
            "现货价格",
            data['spot_price'].round(2).tolist(),
            color="#1f77b4",
            linestyle_opts=opts.LineStyleOpts(width=2),
            label_opts=opts.LabelOpts(is_show=False)
        )

        # 添加期货价格线
        line.add_yaxis(
            "期货价格",
            data['future_price'].round(2).tolist(),
            color="#ff7f0e",
            linestyle_opts=opts.LineStyleOpts(width=2),
            label_opts=opts.LabelOpts(is_show=False)
        )

        line.set_global_opts(
            title_opts=opts.TitleOpts(title="现货与期货价格走势"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(orient="horizontal", pos_top="5%")
        )

        return line