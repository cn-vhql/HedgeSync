"""
压力测试模块
负责识别极端行情和评估套保策略在压力时期的表现
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class StressTestAnalyzer:
    """压力测试分析器"""

    def __init__(self):
        """初始化压力测试分析器"""
        self.stress_periods = []
        self.stress_results = {}

    def identify_stress_periods(self,
                              aligned_data: pd.DataFrame,
                              price_change_threshold: float = 5.0,
                              min_consecutive_days: int = 3) -> List[Dict]:
        """
        识别压力时期

        Args:
            aligned_data: 对齐后的价格数据
            price_change_threshold: 价格变化阈值（百分比）
            min_consecutive_days: 最少连续天数

        Returns:
            压力时期列表
        """
        if aligned_data.empty:
            raise ValueError("数据为空，无法识别压力时期")

        data = aligned_data.copy()

        # 计算现货价格日变化率
        data['spot_price_change_pct'] = data['spot_price'].pct_change() * 100

        # 识别极端变化日
        data['is_extreme'] = np.abs(data['spot_price_change_pct']) > price_change_threshold

        # 找到连续的压力时期
        stress_periods = []
        in_stress_period = False
        period_start = None

        for idx, row in data.iterrows():
            if row['is_extreme'] and not in_stress_period:
                # 开始新的压力时期
                in_stress_period = True
                period_start = idx
            elif not row['is_extreme'] and in_stress_period:
                # 结束压力时期
                period_end = idx - 1
                period_length = period_end - period_start + 1

                if period_length >= min_consecutive_days:
                    # 记录压力时期
                    period_data = data.loc[period_start:period_end]
                    stress_period = self._create_stress_period_summary(
                        period_data, period_start, period_end
                    )
                    stress_periods.append(stress_period)

                in_stress_period = False

        # 处理最后一个未结束的压力时期
        if in_stress_period and period_start is not None:
            period_end = len(data) - 1
            period_length = period_end - period_start + 1

            if period_length >= min_consecutive_days:
                period_data = data.loc[period_start:period_end]
                stress_period = self._create_stress_period_summary(
                    period_data, period_start, period_end
                )
                stress_periods.append(stress_period)

        self.stress_periods = stress_periods
        return stress_periods

    def _create_stress_period_summary(self,
                                    period_data: pd.DataFrame,
                                    start_idx: int,
                                    end_idx: int) -> Dict:
        """
        创建压力时期摘要

        Args:
            period_data: 压力时期数据
            start_idx: 开始索引
            end_idx: 结束索引

        Returns:
            压力时期摘要字典
        """
        summary = {
            'start_date': period_data['date'].min().strftime('%Y-%m-%d'),
            'end_date': period_data['date'].max().strftime('%Y-%m-%d'),
            'duration_days': len(period_data),
            'start_index': start_idx,
            'end_index': end_idx,
            'spot_price_change': period_data['spot_price'].iloc[-1] - period_data['spot_price'].iloc[0],
            'spot_price_change_pct': (period_data['spot_price'].iloc[-1] / period_data['spot_price'].iloc[0] - 1) * 100,
            'future_price_change': period_data['future_price'].iloc[-1] - period_data['future_price'].iloc[0],
            'future_price_change_pct': (period_data['future_price'].iloc[-1] / period_data['future_price'].iloc[0] - 1) * 100,
            'max_daily_spot_change': period_data['spot_price_change_pct'].abs().max(),
            'avg_daily_spot_change': period_data['spot_price_change_pct'].abs().mean(),
            'volatility_spot': period_data['spot_price_change_pct'].std(),
            'volatility_future': period_data['future_price'].pct_change().std() * 100
        }

        # 判断压力类型
        if summary['spot_price_change_pct'] < -price_change_threshold * summary['duration_days'] * 0.3:
            summary['stress_type'] = '大跌行情'
        elif summary['spot_price_change_pct'] > price_change_threshold * summary['duration_days'] * 0.3:
            summary['stress_type'] = '大涨行情'
        else:
            summary['stress_type'] = '高波动行情'

        return summary

    def run_stress_test(self,
                       backtest_results: Dict,
                       stress_periods: Optional[List[Dict]] = None,
                       custom_period: Optional[Tuple[str, str]] = None) -> Dict:
        """
        运行压力测试

        Args:
            backtest_results: 回测结果
            stress_periods: 压力时期列表，如果为None则使用之前识别的
            custom_period: 自定义测试时期 (start_date, end_date)

        Returns:
            压力测试结果
        """
        if backtest_results is None or 'data' not in backtest_results:
            raise ValueError("回测结果无效")

        data = backtest_results['data']
        hedge_params = backtest_results['hedge_parameters']

        if custom_period:
            # 自定义时期压力测试
            stress_results = self._test_custom_period(data, custom_period, hedge_params)
        elif stress_periods:
            # 指定压力时期测试
            stress_results = self._test_specific_periods(data, stress_periods, hedge_params)
        else:
            # 使用之前识别的压力时期
            if not self.stress_periods:
                self.identify_stress_periods(data)
            stress_results = self._test_specific_periods(data, self.stress_periods, hedge_params)

        # 添加正常时期对比
        normal_results = self._get_normal_period_analysis(data)
        stress_results['normal_period_comparison'] = normal_results

        # 计算压力测试汇总指标
        stress_results['summary'] = self._calculate_stress_summary(
            stress_results['stress_periods'],
            normal_results
        )

        self.stress_results = stress_results
        return stress_results

    def _test_custom_period(self,
                          data: pd.DataFrame,
                          custom_period: Tuple[str, str],
                          hedge_params: Dict) -> Dict:
        """
        测试自定义时期

        Args:
            data: 回测数据
            custom_period: 自定义时期 (start_date, end_date)
            hedge_params: 套保参数

        Returns:
            自定义时期测试结果
        """
        start_date, end_date = custom_period
        period_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]

        if period_data.empty:
            raise ValueError(f"指定时期 {start_date} 至 {end_date} 无数据")

        period_result = self._calculate_period_performance(period_data, hedge_params)
        period_result['period_info'] = {
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': len(period_data),
            'stress_type': '自定义测试'
        }

        return {
            'stress_periods': [period_result],
            'test_type': 'custom_period'
        }

    def _test_specific_periods(self,
                             data: pd.DataFrame,
                             stress_periods: List[Dict],
                             hedge_params: Dict) -> Dict:
        """
        测试指定压力时期

        Args:
            data: 回测数据
            stress_periods: 压力时期列表
            hedge_params: 套保参数

        Returns:
            压力时期测试结果
        """
        period_results = []

        for period in stress_periods:
            start_idx = period['start_index']
            end_idx = period['end_index']

            # 提取时期数据
            period_data = data.iloc[start_idx:end_idx+1].copy()

            # 计算时期绩效
            period_result = self._calculate_period_performance(period_data, hedge_params)
            period_result['period_info'] = period

            period_results.append(period_result)

        return {
            'stress_periods': period_results,
            'test_type': 'identified_periods'
        }

    def _calculate_period_performance(self,
                                    period_data: pd.DataFrame,
                                    hedge_params: Dict) -> Dict:
        """
        计算时期绩效

        Args:
            period_data: 时期数据
            hedge_params: 套保参数

        Returns:
            时期绩效结果
        """
        if period_data.empty:
            return {}

        # 基础统计
        total_hedged_pnl = period_data['total_pnl'].sum()
        total_unhedged_pnl = period_data['unhedged_pnl'].sum()
        total_spot_pnl = period_data['spot_pnl'].sum()
        total_future_pnl = period_data['future_pnl'].sum()

        # 风险指标
        hedged_volatility = period_data['total_pnl'].std()
        unhedged_volatility = period_data['unhedged_pnl'].std()

        # 极端损失
        max_daily_loss_hedged = period_data['total_pnl'].min()
        max_daily_loss_unhedged = period_data['unhedged_pnl'].min()

        # 盈利天数
        profitable_days_hedged = (period_data['total_pnl'] > 0).sum()
        profitable_days_unhedged = (period_data['unhedged_pnl'] > 0).sum()

        # VaR
        var_95_hedged = np.percentile(period_data['total_pnl'], 5)
        var_95_unhedged = np.percentile(period_data['unhedged_pnl'], 5)

        # 套保优势
        hedge_advantage = total_hedged_pnl - total_unhedged_pnl
        risk_reduction = (unhedged_volatility - hedged_volatility) / unhedged_volatility if unhedged_volatility > 0 else 0

        result = {
            'days': len(period_data),
            'total_hedged_pnl': total_hedged_pnl,
            'total_unhedged_pnl': total_unhedged_pnl,
            'total_spot_pnl': total_spot_pnl,
            'total_future_pnl': total_future_pnl,
            'avg_daily_hedged_pnl': period_data['total_pnl'].mean(),
            'avg_daily_unhedged_pnl': period_data['unhedged_pnl'].mean(),
            'hedged_volatility': hedged_volatility,
            'unhedged_volatility': unhedged_volatility,
            'max_daily_loss_hedged': max_daily_loss_hedged,
            'max_daily_loss_unhedged': max_daily_loss_unhedged,
            'profitable_days_hedged': profitable_days_hedged,
            'profitable_days_unhedged': profitable_days_unhedged,
            'profitable_days_ratio_hedged': profitable_days_hedged / len(period_data),
            'profitable_days_ratio_unhedged': profitable_days_unhedged / len(period_data),
            'var_95_hedged': var_95_hedged,
            'var_95_unhedged': var_95_unhedged,
            'hedge_advantage': hedge_advantage,
            'risk_reduction_rate': risk_reduction,
            'max_drawdown_hedged': self._calculate_max_drawdown(period_data['total_pnl_cumulative']),
            'max_drawdown_unhedged': self._calculate_max_drawdown(period_data['unhedged_pnl_cumulative'])
        }

        return result

    def _get_normal_period_analysis(self, data: pd.DataFrame) -> Dict:
        """
        获取正常时期分析

        Args:
            data: 完整回测数据

        Returns:
            正常时期分析结果
        """
        if self.stress_periods:
            # 排除压力时期，获取正常时期数据
            normal_data = data.copy()

            for period in self.stress_periods:
                start_idx = period['start_index']
                end_idx = period['end_index']
                normal_data = normal_data.drop(normal_data.index[start_idx:end_idx+1])
        else:
            # 如果没有压力时期，使用所有数据
            normal_data = data

        if normal_data.empty:
            # 如果没有正常时期数据，使用整个时期
            normal_data = data

        hedge_params = {'hedge_direction': 'short_hedge'}  # 默认参数，仅用于计算
        normal_result = self._calculate_period_performance(normal_data, hedge_params)
        normal_result['period_info'] = {
            'duration_days': len(normal_data),
            'stress_type': '正常时期'
        }

        return normal_result

    def _calculate_stress_summary(self,
                                stress_periods_results: List[Dict],
                                normal_result: Dict) -> Dict:
        """
        计算压力测试汇总

        Args:
            stress_periods_results: 压力时期结果列表
            normal_result: 正常时期结果

        Returns:
            压力测试汇总
        """
        if not stress_periods_results:
            return {}

        # 聚合压力时期结果
        total_stress_days = sum(p['days'] for p in stress_periods_results)
        total_stress_pnl_hedged = sum(p['total_hedged_pnl'] for p in stress_periods_results)
        total_stress_pnl_unhedged = sum(p['total_unhedged_pnl'] for p in stress_periods_results)

        avg_volatility_hedged = np.mean([p['hedged_volatility'] for p in stress_periods_results])
        avg_volatility_unhedged = np.mean([p['unhedged_volatility'] for p in stress_periods_results])

        max_loss_hedged = min(p['max_daily_loss_hedged'] for p in stress_periods_results)
        max_loss_unhedged = min(p['max_daily_loss_unhedged'] for p in stress_periods_results)

        # 计算相对表现
        stress_vs_normal_pnl_ratio = (total_stress_pnl_hedged / total_stress_days) / normal_result['avg_daily_hedged_pnl'] if normal_result['avg_daily_hedged_pnl'] != 0 else 0
        stress_vs_normal_volatility_ratio = avg_volatility_hedged / normal_result['hedged_volatility'] if normal_result['hedged_volatility'] != 0 else 0

        summary = {
            'total_stress_periods': len(stress_periods_results),
            'total_stress_days': total_stress_days,
            'total_stress_pnl_hedged': total_stress_pnl_hedged,
            'total_stress_pnl_unhedged': total_stress_pnl_unhedged,
            'avg_stress_pnl_hedged': total_stress_pnl_hedged / total_stress_days,
            'avg_stress_pnl_unhedged': total_stress_pnl_unhedged / total_stress_days,
            'avg_volatility_hedged': avg_volatility_hedged,
            'avg_volatility_unhedged': avg_volatility_unhedged,
            'max_single_loss_hedged': max_loss_hedged,
            'max_single_loss_unhedged': max_loss_unhedged,
            'stress_effectiveness': 1 - (avg_volatility_hedged / avg_volatility_unhedged) if avg_volatility_unhedged > 0 else 0,
            'stress_vs_normal_pnl_ratio': stress_vs_normal_pnl_ratio,
            'stress_vs_normal_volatility_ratio': stress_vs_normal_volatility_ratio
        }

        return summary

    def _calculate_max_drawdown(self, cumulative_series: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            cumulative_series: 累计收益序列

        Returns:
            最大回撤值
        """
        if cumulative_series.empty:
            return 0

        peak = cumulative_series.expanding().max()
        drawdown = cumulative_series - peak
        max_drawdown = drawdown.min()
        return max_drawdown

    def generate_stress_test_report(self) -> str:
        """
        生成压力测试报告

        Returns:
            压力测试报告文本
        """
        if not self.stress_results:
            return "请先运行压力测试"

        report = []
        report.append("## 压力测试报告\n")

        # 测试概述
        summary = self.stress_results.get('summary', {})
        if summary:
            report.append(f"### 测试概述")
            report.append(f"- 识别压力时期数量: {summary.get('total_stress_periods', 0)}个")
            report.append(f"- 压力时期总天数: {summary.get('total_stress_days', 0)}天")
            report.append(f"- 压力时期套保总盈亏: {summary.get('total_stress_pnl_hedged', 0):.2f}")
            report.append(f"- 压力时期未套保总盈亏: {summary.get('total_stress_pnl_unhedged', 0):.2f}")
            report.append(f"- 压力时期套保有效性: {summary.get('stress_effectiveness', 0):.2%}")
            report.append("")

        # 各压力时期详情
        stress_periods = self.stress_results.get('stress_periods', [])
        if stress_periods:
            report.append("### 各压力时期详情")

            for i, period in enumerate(stress_periods, 1):
                period_info = period.get('period_info', {})
                report.append(f"**时期 {i}: {period_info.get('stress_type', '未知')}**")
                report.append(f"- 时间: {period_info.get('start_date', '')} 至 {period_info.get('end_date', '')}")
                report.append(f"- 持续天数: {period_info.get('duration_days', 0)}天")
                report.append(f"- 套保盈亏: {period.get('total_hedged_pnl', 0):.2f}")
                report.append(f"- 未套保盈亏: {period.get('total_unhedged_pnl', 0):.2f}")
                report.append(f"- 套保优势: {period.get('hedge_advantage', 0):.2f}")
                report.append(f"- 最大单日亏损(套保): {period.get('max_daily_loss_hedged', 0):.2f}")
                report.append(f"- 最大单日亏损(未套保): {period.get('max_daily_loss_unhedged', 0):.2f}")
                report.append("")

        # 正常时期对比
        normal_period = self.stress_results.get('normal_period_comparison', {})
        if normal_period:
            report.append("### 正常时期对比")
            report.append(f"- 正常时期天数: {normal_period.get('days', 0)}天")
            report.append(f"- 正常时期套保盈亏: {normal_period.get('total_hedged_pnl', 0):.2f}")
            report.append(f"- 正常时期未套保盈亏: {normal_period.get('total_unhedged_pnl', 0):.2f}")
            report.append("")

        # 结论与建议
        report.append("### 结论与建议")

        if summary and summary.get('stress_effectiveness', 0) > 0.5:
            report.append("✅ **套保策略在压力时期表现良好**")
            report.append("- 套保有效降低了极端行情下的风险")
            report.append("- 建议维持当前套保策略")
        elif summary and summary.get('stress_effectiveness', 0) > 0.2:
            report.append("⚠️ **套保策略在压力时期表现中等**")
            report.append("- 套保起到一定风险降低作用，但效果有限")
            report.append("- 建议优化套保比例或考虑其他风险管理工具")
        else:
            report.append("❌ **套保策略在压力时期表现不佳**")
            report.append("- 套保未能有效降低极端风险")
            report.append("- 建议重新评估套保策略和风险管理方法")

        return "\n".join(report)

    def export_stress_test_results(self, file_path: str) -> None:
        """
        导出压力测试结果

        Args:
            file_path: 导出文件路径
        """
        if not self.stress_results:
            raise ValueError("没有可导出的压力测试结果")

        # 准备导出数据
        export_data = []

        # 添加各压力时期数据
        for i, period in enumerate(self.stress_results.get('stress_periods', []), 1):
            period_info = period.get('period_info', {})
            export_data.append({
                '时期编号': i,
                '类型': period_info.get('stress_type', ''),
                '开始日期': period_info.get('start_date', ''),
                '结束日期': period_info.get('end_date', ''),
                '持续天数': period_info.get('duration_days', 0),
                '套保总盈亏': period.get('total_hedged_pnl', 0),
                '未套保总盈亏': period.get('total_unhedged_pnl', 0),
                '套保优势': period.get('hedge_advantage', 0),
                '套保波动率': period.get('hedged_volatility', 0),
                '未套保波动率': period.get('unhedged_volatility', 0),
                '风险降低率': period.get('risk_reduction_rate', 0),
                '最大单日亏损(套保)': period.get('max_daily_loss_hedged', 0),
                '最大单日亏损(未套保)': period.get('max_daily_loss_unhedged', 0)
            })

        # 导出为CSV
        df = pd.DataFrame(export_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')