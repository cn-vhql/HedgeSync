"""
套保比例计算模块
实现最优套保比例计算和相关模型评估
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Tuple, Dict, Optional
from scipy import stats


class HedgeRatioCalculator:
    """套保比例计算器"""

    def __init__(self):
        """初始化套保比例计算器"""
        self.last_calculation = None

    def calculate_optimal_hedge_ratio(self,
                                    aligned_data: pd.DataFrame,
                                    window_size: Optional[int] = None) -> Tuple[float, Dict]:
        """
        计算最优套保比例（最小方差法）

        Args:
            aligned_data: 对齐后的现货和期货价格数据
            window_size: 计算窗口大小，None表示使用全部数据

        Returns:
            (最优套保比例, 回归结果字典)
        """
        if aligned_data.empty:
            raise ValueError("数据为空，无法计算套保比例")

        # 准备数据
        if window_size and window_size < len(aligned_data):
            # 使用指定窗口
            data = aligned_data.tail(window_size).copy()
        else:
            # 使用全部数据
            data = aligned_data.copy()

        # 计算价格变化量
        data['spot_change'] = data['spot_price'].diff()
        data['future_change'] = data['future_price'].diff()

        # 删除第一行（NaN）
        data = data.dropna()

        if len(data) < 2:
            raise ValueError("数据量不足，无法计算套保比例")

        # 方法1: 最小方差法 (直接计算)
        cov_matrix = np.cov(data['spot_change'], data['future_change'])
        hedge_ratio_mv = cov_matrix[0, 1] / cov_matrix[1, 1]

        # 方法2: 线性回归法 (OLS)
        X = sm.add_constant(data['future_change'])  # 添加常数项
        model = sm.OLS(data['spot_change'], X).fit()

        hedge_ratio_ols = model.params[1]  # 斜率系数

        # 方法3: 相关系数调整法
        correlation = np.corrcoef(data['spot_change'], data['future_change'])[0, 1]
        spot_vol = data['spot_change'].std()
        future_vol = data['future_change'].std()
        hedge_ratio_corr = correlation * (spot_vol / future_vol)

        # 使用最小方差法的结果作为主要推荐值
        optimal_ratio = hedge_ratio_mv

        # 构建结果字典
        result = {
            'optimal_hedge_ratio': optimal_ratio,
            'hedge_ratio_ols': hedge_ratio_ols,
            'hedge_ratio_corr': hedge_ratio_corr,
            'regression_results': {
                'r_squared': model.rsquared,
                'adj_r_squared': model.rsquared_adj,
                'f_statistic': model.fvalue,
                'f_pvalue': model.f_pvalue,
                'intercept': model.params[0],
                'intercept_pvalue': model.pvalues[0],
                'slope': model.params[1],
                'slope_pvalue': model.pvalues[1],
                'slope_std_error': model.bse[1]
            },
            'correlation_analysis': {
                'correlation': correlation,
                'spot_volatility': spot_vol,
                'future_volatility': future_vol,
                'correlation_pvalue': stats.pearsonr(data['spot_change'], data['future_change'])[1]
            },
            'calculation_method': 'minimum_variance',
            'data_points': len(data),
            'window_used': window_size if window_size else 'all_data'
        }

        self.last_calculation = result
        return optimal_ratio, result

    def calculate_hedge_effectiveness(self,
                                    aligned_data: pd.DataFrame,
                                    hedge_ratio: float) -> Dict:
        """
        计算套保有效性指标

        Args:
            aligned_data: 对齐后的数据
            hedge_ratio: 套保比例

        Returns:
            套保有效性指标字典
        """
        if aligned_data.empty:
            raise ValueError("数据为空，无法计算套保有效性")

        data = aligned_data.copy()
        data['spot_change'] = data['spot_price'].diff()
        data['future_change'] = data['future_price'].diff()

        # 计算套保后的收益变化
        data['hedged_change'] = data['spot_change'] - hedge_ratio * data['future_change']

        # 删除第一行（NaN）
        data = data.dropna()

        if len(data) < 2:
            raise ValueError("数据量不足，无法计算套保有效性")

        # 计算方差
        unhedged_variance = data['spot_change'].var()
        hedged_variance = data['hedged_change'].var()

        # 套保有效性
        hedge_effectiveness = 1 - (hedged_variance / unhedged_variance)

        # 风险降低率
        risk_reduction = (unhedged_variance - hedged_variance) / unhedged_variance

        # 计算统计指标
        result = {
            'hedge_effectiveness': hedge_effectiveness,
            'risk_reduction_rate': risk_reduction,
            'unhedged_variance': unhedged_variance,
            'hedged_variance': hedged_variance,
            'unhedged_volatility': np.sqrt(unhedged_variance),
            'hedged_volatility': np.sqrt(hedged_variance),
            'variance_reduction': unhedged_variance - hedged_variance
        }

        return result

    def calculate_hedge_quantity(self,
                               spot_quantity: float,
                               hedge_ratio: float,
                               future_contract_size: float = 1.0) -> Dict:
        """
        计算期货套保数量

        Args:
            spot_quantity: 现货数量
            hedge_ratio: 套保比例
            future_contract_size: 期货合约规模

        Returns:
            套保数量计算结果
        """
        # 计算需要的期货数量
        future_quantity = spot_quantity * hedge_ratio

        # 计算合约数量
        contract_count = future_quantity / future_contract_size

        result = {
            'spot_quantity': spot_quantity,
            'optimal_hedge_ratio': hedge_ratio,
            'future_quantity_needed': future_quantity,
            'future_contract_size': future_contract_size,
            'contract_count': contract_count,
            'rounded_contract_count': round(contract_count),
            'actual_hedge_ratio': (round(contract_count) * future_contract_size) / spot_quantity
        }

        return result

    def sensitivity_analysis(self,
                           aligned_data: pd.DataFrame,
                           base_ratio: float,
                           ratio_range: float = 0.2,
                           steps: int = 20) -> pd.DataFrame:
        """
        套保比例敏感性分析

        Args:
            aligned_data: 对齐后的数据
            base_ratio: 基准套保比例
            ratio_range: 比例变化范围 (±)
            steps: 分析步数

        Returns:
            敏感性分析结果DataFrame
        """
        if aligned_data.empty:
            raise ValueError("数据为空，无法进行敏感性分析")

        data = aligned_data.copy()
        data['spot_change'] = data['spot_price'].diff()
        data['future_change'] = data['future_price'].diff()
        data = data.dropna()

        # 生成套保比例范围
        ratio_min = base_ratio * (1 - ratio_range)
        ratio_max = base_ratio * (1 + ratio_range)
        ratios = np.linspace(ratio_min, ratio_max, steps)

        results = []

        for ratio in ratios:
            # 计算套保后的收益变化
            hedged_change = data['spot_change'] - ratio * data['future_change']

            # 计算统计指标
            variance = hedged_change.var()
            volatility = np.sqrt(variance)
            unhedged_variance = data['spot_change'].var()

            effectiveness = 1 - (variance / unhedged_variance)
            risk_reduction = (unhedged_variance - variance) / unhedged_variance

            results.append({
                'hedge_ratio': ratio,
                'variance': variance,
                'volatility': volatility,
                'effectiveness': effectiveness,
                'risk_reduction': risk_reduction,
                'ratio_deviation_pct': ((ratio - base_ratio) / base_ratio) * 100
            })

        return pd.DataFrame(results)

    def validate_hedge_ratio(self, ratio: float) -> Tuple[bool, str]:
        """
        验证套保比例的合理性

        Args:
            ratio: 套保比例

        Returns:
            (是否合理, 建议信息)
        """
        if np.isnan(ratio):
            return False, "套保比例无效 (NaN)"

        if np.isinf(ratio):
            return False, "套保比例无效 (无穷大)"

        if abs(ratio) > 10:
            return False, f"套保比例过大 ({ratio:.4f})，建议检查数据"

        if abs(ratio) < 0.01:
            return True, "套保比例很小，套保效果可能有限"

        if abs(ratio) > 5:
            return True, "套保比例较大，请确认期货和现货品种匹配"

        return True, "套保比例合理"