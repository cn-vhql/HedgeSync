"""
历史回测与盈亏模拟模块
负责模拟套保策略的历史表现和风险指标计算
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from enum import Enum


class HedgeDirection(Enum):
    """套保方向枚举"""
    LONG_HEDGE = "long_hedge"  # 买入套保（现货空头，期货多头）
    SHORT_HEDGE = "short_hedge"  # 卖出套保（现货多头，期货空头）


class BacktestEngine:
    """历史回测引擎"""

    def __init__(self):
        """初始化回测引擎"""
        self.backtest_results = None

    def run_backtest(self,
                    aligned_data: pd.DataFrame,
                    hedge_ratio: float,
                    spot_quantity: float,
                    hedge_direction: HedgeDirection,
                    future_contract_size: float = 1.0) -> Dict:
        """
        运行历史回测

        Args:
            aligned_data: 对齐后的现货和期货数据
            hedge_ratio: 套保比例
            spot_quantity: 现货数量
            hedge_direction: 套保方向
            future_contract_size: 期货合约规模

        Returns:
            回测结果字典
        """
        if aligned_data.empty:
            raise ValueError("数据为空，无法进行回测")

        # 准备数据
        data = aligned_data.copy()

        # 计算期货数量
        future_quantity = spot_quantity * hedge_ratio

        # 计算每日价格变化
        data['spot_price_change'] = data['spot_price'].diff()
        data['future_price_change'] = data['future_price'].diff()

        # 计算每日盈亏
        if hedge_direction == HedgeDirection.SHORT_HEDGE:
            # 库存管理（现货多头）：卖出期货套保
            # 现货盈亏 = 现货数量 × 现货价格变化
            # 期货盈亏 = -期货数量 × 期货价格变化（空头）
            data['spot_pnl'] = spot_quantity * data['spot_price_change']
            data['future_pnl'] = -future_quantity * data['future_price_change']
            data['total_pnl'] = data['spot_pnl'] + data['future_pnl']

        elif hedge_direction == HedgeDirection.LONG_HEDGE:
            # 采购管理（现货空头）：买入期货套保
            # 现货盈亏 = -现货数量 × 现货价格变化（空头）
            # 期货盈亏 = 期货数量 × 期货价格变化（多头）
            data['spot_pnl'] = -spot_quantity * data['spot_price_change']
            data['future_pnl'] = future_quantity * data['future_price_change']
            data['total_pnl'] = data['spot_pnl'] + data['future_pnl']

        # 计算未套保的盈亏（仅现货）
        if hedge_direction == HedgeDirection.SHORT_HEDGE:
            data['unhedged_pnl'] = spot_quantity * data['spot_price_change']
        else:
            data['unhedged_pnl'] = -spot_quantity * data['spot_price_change']

        # 计算累计盈亏
        data['total_pnl_cumulative'] = data['total_pnl'].cumsum()
        data['unhedged_pnl_cumulative'] = data['unhedged_pnl'].cumsum()
        data['spot_pnl_cumulative'] = data['spot_pnl'].cumsum()
        data['future_pnl_cumulative'] = data['future_pnl'].cumsum()

        # 删除第一行（NaN）
        data = data.dropna()

        # 计算绩效指标
        performance_metrics = self._calculate_performance_metrics(
            data, hedge_direction, spot_quantity, future_quantity
        )

        # 构建结果
        result = {
            'data': data,
            'performance_metrics': performance_metrics,
            'hedge_parameters': {
                'hedge_ratio': hedge_ratio,
                'spot_quantity': spot_quantity,
                'future_quantity': future_quantity,
                'hedge_direction': hedge_direction.value,
                'future_contract_size': future_contract_size
            }
        }

        self.backtest_results = result
        return result

    def _calculate_performance_metrics(self,
                                     data: pd.DataFrame,
                                     hedge_direction: HedgeDirection,
                                     spot_quantity: float,
                                     future_quantity: float) -> Dict:
        """
        计算绩效指标

        Args:
            data: 回测数据
            hedge_direction: 套保方向
            spot_quantity: 现货数量
            future_quantity: 期货数量

        Returns:
            绩效指标字典
        """
        metrics = {}

        # 基础统计
        metrics['total_days'] = len(data)

        # 总盈亏
        metrics['total_hedged_pnl'] = data['total_pnl'].sum()
        metrics['total_unhedged_pnl'] = data['unhedged_pnl'].sum()
        metrics['total_spot_pnl'] = data['spot_pnl'].sum()
        metrics['total_future_pnl'] = data['future_pnl'].sum()

        # 平均每日盈亏
        metrics['avg_daily_hedged_pnl'] = data['total_pnl'].mean()
        metrics['avg_daily_unhedged_pnl'] = data['unhedged_pnl'].mean()

        # 盈利天数统计
        metrics['profitable_days_hedged'] = (data['total_pnl'] > 0).sum()
        metrics['profitable_days_unhedged'] = (data['unhedged_pnl'] > 0).sum()
        metrics['profitable_days_ratio_hedged'] = metrics['profitable_days_hedged'] / metrics['total_days']
        metrics['profitable_days_ratio_unhedged'] = metrics['profitable_days_unhedged'] / metrics['total_days']

        # 风险指标
        metrics['hedged_volatility'] = data['total_pnl'].std()
        metrics['unhedged_volatility'] = data['unhedged_pnl'].std()

        # 最大回撤
        metrics['max_drawdown_hedged'] = self._calculate_max_drawdown(data['total_pnl_cumulative'])
        metrics['max_drawdown_unhedged'] = self._calculate_max_drawdown(data['unhedged_pnl_cumulative'])

        # 夏普比率（假设无风险利率为0）
        if metrics['hedged_volatility'] > 0:
            metrics['sharpe_ratio_hedged'] = metrics['avg_daily_hedged_pnl'] / metrics['hedged_volatility']
        else:
            metrics['sharpe_ratio_hedged'] = 0

        if metrics['unhedged_volatility'] > 0:
            metrics['sharpe_ratio_unhedged'] = metrics['avg_daily_unhedged_pnl'] / metrics['unhedged_volatility']
        else:
            metrics['sharpe_ratio_unhedged'] = 0

        # 风险降低指标
        variance_reduction = (data['unhedged_pnl'].var() - data['total_pnl'].var()) / data['unhedged_pnl'].var()
        volatility_reduction = (metrics['unhedged_volatility'] - metrics['hedged_volatility']) / metrics['unhedged_volatility']

        metrics['variance_reduction_rate'] = variance_reduction
        metrics['volatility_reduction_rate'] = volatility_reduction
        metrics['hedging_effectiveness'] = variance_reduction  # 套保有效性

        # 套保成本（期货交易成本估算）
        metrics['estimated_hedge_cost'] = abs(future_quantity) * data['future_price'].mean() * 0.001  # 假设0.1%的交易成本

        # 最大单日盈亏
        metrics['max_daily_gain_hedged'] = data['total_pnl'].max()
        metrics['max_daily_loss_hedged'] = data['total_pnl'].min()
        metrics['max_daily_gain_unhedged'] = data['unhedged_pnl'].max()
        metrics['max_daily_loss_unhedged'] = data['unhedged_pnl'].min()

        # VaR（95%置信水平）
        metrics['var_95_hedged'] = np.percentile(data['total_pnl'], 5)
        metrics['var_95_unhedged'] = np.percentile(data['unhedged_pnl'], 5)

        # 时间范围
        metrics['start_date'] = data['date'].min().strftime('%Y-%m-%d')
        metrics['end_date'] = data['date'].max().strftime('%Y-%m-%d')

        return metrics

    def _calculate_max_drawdown(self, cumulative_series: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            cumulative_series: 累计收益序列

        Returns:
            最大回撤值
        """
        peak = cumulative_series.expanding().max()
        drawdown = cumulative_series - peak
        max_drawdown = drawdown.min()
        return max_drawdown

    def get_period_analysis(self,
                          start_date: str,
                          end_date: str) -> Dict:
        """
        获取特定时间段的分析

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            时间段分析结果
        """
        if self.backtest_results is None:
            raise ValueError("请先运行回测")

        data = self.backtest_results['data']
        hedge_direction = self.backtest_results['hedge_parameters']['hedge_direction']

        # 筛选时间段
        period_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]

        if period_data.empty:
            raise ValueError("指定时间段内无数据")

        # 计算时间段指标
        period_metrics = {
            'days': len(period_data),
            'total_hedged_pnl': period_data['total_pnl'].sum(),
            'total_unhedged_pnl': period_data['unhedged_pnl'].sum(),
            'avg_daily_hedged_pnl': period_data['total_pnl'].mean(),
            'avg_daily_unhedged_pnl': period_data['unhedged_pnl'].mean(),
            'hedged_volatility': period_data['total_pnl'].std(),
            'unhedged_volatility': period_data['unhedged_pnl'].std(),
            'max_daily_loss_hedged': period_data['total_pnl'].min(),
            'max_daily_loss_unhedged': period_data['unhedged_pnl'].min(),
            'profitable_days_hedged': (period_data['total_pnl'] > 0).sum(),
            'profitable_days_unhedged': (period_data['unhedged_pnl'] > 0).sum(),
            'hedge_advantage': period_data['total_pnl'].sum() - period_data['unhedged_pnl'].sum()
        }

        return {
            'period_data': period_data,
            'period_metrics': period_metrics
        }

    def calculate_rolling_metrics(self,
                                window_size: int = 30) -> pd.DataFrame:
        """
        计算滚动绩效指标

        Args:
            window_size: 滚动窗口大小

        Returns:
            滚动指标DataFrame
        """
        if self.backtest_results is None:
            raise ValueError("请先运行回测")

        data = self.backtest_results['data']

        # 计算滚动指标
        rolling_metrics = pd.DataFrame({
            'date': data['date'],
            'rolling_volatility_hedged': data['total_pnl'].rolling(window=window_size).std(),
            'rolling_volatility_unhedged': data['unhedged_pnl'].rolling(window=window_size).std(),
            'rolling_sharpe_hedged': data['total_pnl'].rolling(window=window_size).mean() / data['total_pnl'].rolling(window=window_size).std(),
            'rolling_sharpe_unhedged': data['unhedged_pnl'].rolling(window=window_size).mean() / data['unhedged_pnl'].rolling(window=window_size).std(),
            'rolling_corr': data['spot_price_change'].rolling(window=window_size).corr(data['future_price_change'])
        })

        return rolling_metrics

    def generate_performance_summary(self) -> Dict:
        """
        生成绩效摘要

        Returns:
            绩效摘要字典
        """
        if self.backtest_results is None:
            raise ValueError("请先运行回测")

        metrics = self.backtest_results['performance_metrics']
        params = self.backtest_results['hedge_parameters']

        summary = {
            '套保策略摘要': {
                '套保方向': '库存管理（卖出套保）' if params['hedge_direction'] == HedgeDirection.SHORT_HEDGE.value else '采购管理（买入套保）',
                '套保比例': f"{params['hedge_ratio']:.4f}",
                '现货数量': params['spot_quantity'],
                '期货数量': f"{params['future_quantity']:.4f}",
                '回测期间': f"{metrics['start_date']} 至 {metrics['end_date']}",
                '交易天数': metrics['total_days']
            },
            '盈亏表现': {
                '套保总盈亏': f"{metrics['total_hedged_pnl']:.2f}",
                '未套保总盈亏': f"{metrics['total_unhedged_pnl']:.2f}",
                '套保优势': f"{metrics['total_hedged_pnl'] - metrics['total_unhedged_pnl']:.2f}",
                '平均每日盈亏（套保）': f"{metrics['avg_daily_hedged_pnl']:.2f}",
                '平均每日盈亏（未套保）': f"{metrics['avg_daily_unhedged_pnl']:.2f}"
            },
            '风险控制': {
                '套保波动率': f"{metrics['hedged_volatility']:.2f}",
                '未套保波动率': f"{metrics['unhedged_volatility']:.2f}",
                '波动率降低': f"{metrics['volatility_reduction_rate']:.2%}",
                '最大回撤（套保）': f"{metrics['max_drawdown_hedged']:.2f}",
                '最大回撤（未套保）': f"{metrics['max_drawdown_unhedged']:.2f}",
                '套保有效性': f"{metrics['hedging_effectiveness']:.2%}"
            },
            '其他指标': {
                '盈利天数占比（套保）': f"{metrics['profitable_days_ratio_hedged']:.2%}",
                '盈利天数占比（未套保）': f"{metrics['profitable_days_ratio_unhedged']:.2%}",
                '夏普比率（套保）': f"{metrics['sharpe_ratio_hedged']:.4f}",
                '夏普比率（未套保）': f"{metrics['sharpe_ratio_unhedged']:.4f}",
                'VaR（95%，套保）': f"{metrics['var_95_hedged']:.2f}",
                'VaR（95%，未套保）': f"{metrics['var_95_unhedged']:.2f}"
            }
        }

        return summary