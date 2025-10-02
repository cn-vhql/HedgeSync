"""
数据处理模块
负责现货数据导入、期货数据获取和数据对齐
"""

import pandas as pd
import numpy as np
import akshare as ak
import os
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
import warnings

warnings.filterwarnings('ignore')


class DataProcessor:
    """数据处理类"""

    def __init__(self, cache_dir: str = "cache"):
        """
        初始化数据处理器

        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def validate_spot_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        验证现货数据格式

        Args:
            df: 现货数据DataFrame

        Returns:
            (是否有效, 错误信息)
        """
        if df is None or df.empty:
            return False, "数据为空"

        # 检查必需列
        required_columns = ['date', 'spot_price']
        if not all(col in df.columns for col in required_columns):
            return False, f"数据必须包含列: {required_columns}"

        # 检查数据类型
        try:
            df['date'] = pd.to_datetime(df['date'])
            df['spot_price'] = pd.to_numeric(df['spot_price'])
        except Exception as e:
            return False, f"数据格式错误: {str(e)}"

        # 检查价格有效性
        if (df['spot_price'] < 0).any():
            return False, "现货价格不能为负数"

        # 检查缺失值
        if df['spot_price'].isnull().any():
            return False, "现货价格存在缺失值"

        if df['date'].isnull().any():
            return False, "日期存在缺失值"

        return True, ""

    def load_spot_data(self, file_path: str,
                      handle_missing: str = "drop") -> Tuple[Optional[pd.DataFrame], str]:
        """
        加载现货数据

        Args:
            file_path: CSV文件路径
            handle_missing: 缺失值处理方式 ("drop" 或 "interpolate")

        Returns:
            (处理后的DataFrame, 错误信息)
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)

            # 验证数据格式
            is_valid, error_msg = self.validate_spot_data(df)
            if not is_valid:
                return None, error_msg

            # 处理缺失值
            if df['spot_price'].isnull().any():
                if handle_missing == "drop":
                    df = df.dropna(subset=['spot_price'])
                elif handle_missing == "interpolate":
                    df['spot_price'] = df['spot_price'].interpolate()
                    df = df.dropna(subset=['spot_price'])

            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)

            return df, ""

        except Exception as e:
            return None, f"文件读取失败: {str(e)}"

    def get_future_data(self, future_code: str,
                       start_date: str,
                       end_date: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取期货数据

        Args:
            future_code: 期货合约代码 (如 "CU0")
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            (期货数据DataFrame, 错误信息)
        """
        try:
            # 检查缓存
            cache_file = os.path.join(self.cache_dir, f"future_{future_code}_{start_date}_{end_date}.csv")

            if os.path.exists(cache_file):
                cached_data = pd.read_csv(cache_file)
                cached_data['date'] = pd.to_datetime(cached_data['date'])
                return cached_data, "从缓存读取"

            # 获取期货数据
            # 使用akshare获取期货历史数据
            try:
                # 尝试获取主力合约数据
                future_data = ak.futures_main_sina(symbol=future_code)
            except:
                # 如果失败，尝试其他接口
                future_data = ak.futures_zh_daily_sina(symbol=future_code)

            if future_data.empty:
                return None, f"未找到期货合约 {future_code} 的数据"

            # 处理数据列名
            column_mapping = {
                'date': 'date',
                'close': 'future_price',
                'settlement': 'future_price',
                '收盘价': 'future_price',
                '结算价': 'future_price'
            }

            # 找到合适的列名
            price_col = None
            date_col = None

            for col in future_data.columns:
                if any(key in col.lower() for key in ['date', '日期', 'time']):
                    date_col = col
                elif any(key in col for key in ['close', 'settlement', '收盘', '结算']):
                    price_col = col

            if date_col is None or price_col is None:
                return None, "期货数据格式不正确，无法识别日期和价格列"

            # 提取需要的列
            result_df = pd.DataFrame({
                'date': pd.to_datetime(future_data[date_col]),
                'future_price': pd.to_numeric(future_data[price_col])
            })

            # 筛选日期范围
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            result_df = result_df[(result_df['date'] >= start_dt) & (result_df['date'] <= end_dt)]

            if result_df.empty:
                return None, "指定日期范围内无期货数据"

            # 按日期排序
            result_df = result_df.sort_values('date').reset_index(drop=True)

            # 缓存数据
            result_df.to_csv(cache_file, index=False)

            return result_df, ""

        except Exception as e:
            return None, f"获取期货数据失败: {str(e)}"

    def align_data(self, spot_df: pd.DataFrame,
                  future_df: pd.DataFrame) -> pd.DataFrame:
        """
        对齐现货和期货数据

        Args:
            spot_df: 现货数据
            future_df: 期货数据

        Returns:
            对齐后的DataFrame
        """
        # 基于日期对齐数据
        aligned_df = pd.merge(spot_df, future_df, on='date', how='inner')

        if aligned_df.empty:
            raise ValueError("现货和期货数据没有重叠的日期")

        # 按日期排序
        aligned_df = aligned_df.sort_values('date').reset_index(drop=True)

        return aligned_df

    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取数据摘要统计

        Args:
            df: 数据DataFrame

        Returns:
            数据摘要字典
        """
        if df.empty:
            return {}

        summary = {
            '数据行数': len(df),
            '时间范围': f"{df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}",
            '现货价格统计': {
                '均值': round(df['spot_price'].mean(), 2),
                '标准差': round(df['spot_price'].std(), 2),
                '最小值': round(df['spot_price'].min(), 2),
                '最大值': round(df['spot_price'].max(), 2),
                '波动率': round(df['spot_price'].std() / df['spot_price'].mean() * 100, 2)
            }
        }

        if 'future_price' in df.columns:
            summary['期货价格统计'] = {
                '均值': round(df['future_price'].mean(), 2),
                '标准差': round(df['future_price'].std(), 2),
                '最小值': round(df['future_price'].min(), 2),
                '最大值': round(df['future_price'].max(), 2),
                '波动率': round(df['future_price'].std() / df['future_price'].mean() * 100, 2)
            }

        return summary