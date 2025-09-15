"""
数据处理模块
提供数据清洗、转换和分析功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理类"""
    
    @staticmethod
    def validate_experiment_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证实验数据格式
        
        Args:
            df: 数据DataFrame
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需列
        required_columns = ['电流', '电压', '功率']
        # 兼容英文列名
        alt_columns = {
            '电流': ['current', 'Current', 'I', 'i'],
            '电压': ['voltage', 'Voltage', 'V', 'v'],
            '功率': ['power', 'Power', 'P', 'p']
        }
        
        # 标准化列名
        for cn_name, alt_names in alt_columns.items():
            for alt in alt_names:
                if alt in df.columns and cn_name not in df.columns:
                    df.rename(columns={alt: cn_name}, inplace=True)
                    break
        
        # 检查必需列是否存在
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
        
        # 检查数据类型
        for col in required_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].isna().any():
                        errors.append(f"列 '{col}' 包含非数值数据")
                except Exception as e:
                    errors.append(f"列 '{col}' 数据类型转换失败: {str(e)}")
        
        # 检查数据范围
        if '电流' in df.columns:
            if (df['电流'] < 0).any():
                errors.append("电流值不能为负数")
            if (df['电流'] > 1000).any():
                errors.append("电流值超出合理范围 (>1000A)")
        
        if '电压' in df.columns:
            if (df['电压'] < 0).any():
                errors.append("电压值不能为负数")
            if (df['电压'] > 10000).any():
                errors.append("电压值超出合理范围 (>10000V)")
        
        # 检查功率计算
        if all(col in df.columns for col in ['电流', '电压', '功率']):
            calculated_power = df['电流'] * df['电压']
            power_diff = abs(df['功率'] - calculated_power)
            if (power_diff > calculated_power * 0.05).any():  # 5%误差容限
                errors.append("功率值与电流电压计算值偏差过大")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def process_excel_data(file_path: str) -> pd.DataFrame:
        """
        处理Excel文件数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            处理后的DataFrame
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 跳过前面的元数据行（如果有）
            if '序号' in df.columns or '序号' in df.iloc[0:5].values.flatten():
                # 找到数据开始的行
                for i in range(len(df)):
                    if '序号' in str(df.iloc[i].values):
                        df = pd.read_excel(file_path, skiprows=i+1, engine='openpyxl')
                        break
            
            # 清理列名
            df.columns = df.columns.str.strip()
            
            # 移除空行
            df = df.dropna(how='all')
            
            # 重置索引
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"处理Excel文件失败: {e}")
            raise
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> Dict[str, float]:
        """
        计算数据统计信息
        
        Args:
            df: 数据DataFrame
            
        Returns:
            统计信息字典
        """
        stats = {}
        
        numeric_columns = ['电流', '电压', '功率']
        
        for col in numeric_columns:
            if col in df.columns:
                stats[f"{col}_平均值"] = df[col].mean()
                stats[f"{col}_最大值"] = df[col].max()
                stats[f"{col}_最小值"] = df[col].min()
                stats[f"{col}_标准差"] = df[col].std()
                stats[f"{col}_中位数"] = df[col].median()
        
        # 计算额外指标
        if '功率' in df.columns:
            stats['总能量'] = df['功率'].sum() * 0.001  # 假设每个数据点代表1秒，转换为kWh
            stats['功率因数'] = df['功率'].mean() / (df['电流'].mean() * df['电压'].mean()) if '电流' in df.columns and '电压' in df.columns else 0
        
        return stats
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
        """
        检测异常数据点
        
        Args:
            df: 数据DataFrame
            column: 要检测的列名
            method: 检测方法 ('iqr', 'zscore', 'isolation')
            
        Returns:
            包含异常标记的DataFrame
        """
        df = df.copy()
        
        if method == 'iqr':
            # 四分位距方法
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df['异常'] = (df[column] < lower_bound) | (df[column] > upper_bound)
            
        elif method == 'zscore':
            # Z分数方法
            mean = df[column].mean()
            std = df[column].std()
            z_scores = np.abs((df[column] - mean) / std)
            df['异常'] = z_scores > 3
            
        return df
    
    @staticmethod
    def resample_data(df: pd.DataFrame, freq: str = '1S') -> pd.DataFrame:
        """
        重采样时间序列数据
        
        Args:
            df: 数据DataFrame（需要有时间戳列）
            freq: 采样频率
            
        Returns:
            重采样后的DataFrame
        """
        if 'timestamp' in df.columns or '时间戳' in df.columns:
            time_col = 'timestamp' if 'timestamp' in df.columns else '时间戳'
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.set_index(time_col)
            
            # 对数值列进行重采样
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            resampled = df[numeric_columns].resample(freq).mean()
            
            return resampled.reset_index()
        else:
            logger.warning("数据中没有时间戳列，无法进行重采样")
            return df
    
    @staticmethod
    def prepare_for_database(df: pd.DataFrame, experiment_id: str) -> List[Dict]:
        """
        准备数据以插入数据库
        
        Args:
            df: 数据DataFrame
            experiment_id: 实验ID
            
        Returns:
            数据字典列表
        """
        records = []
        
        for idx, row in df.iterrows():
            record = {
                'experiment_id': experiment_id,
                'sequence_number': idx + 1,
                'current': float(row.get('电流', 0)),
                'voltage': float(row.get('电压', 0)),
                'power': float(row.get('功率', 0)),
                'device_address': int(row.get('设备地址', 1)),
                'device_type': str(row.get('设备类型', '未知')),
                'timestamp': row.get('时间戳', datetime.now())
            }
            
            # 添加温度和湿度（如果有）
            if '温度' in row:
                record['temperature'] = float(row['温度'])
            if '湿度' in row:
                record['humidity'] = float(row['湿度'])
            
            records.append(record)
        
        return records
    
    @staticmethod
    def generate_test_data(
        duration: int = 300,
        sampling_rate: int = 1,
        voltage_nominal: float = 20.0,
        current_nominal: float = 1.0,
        noise_level: float = 0.05
    ) -> pd.DataFrame:
        """
        生成测试数据
        
        Args:
            duration: 持续时间（秒）
            sampling_rate: 采样率（Hz）
            voltage_nominal: 额定电压
            current_nominal: 额定电流
            noise_level: 噪声水平（0-1）
            
        Returns:
            生成的测试数据DataFrame
        """
        num_points = duration * sampling_rate
        time_stamps = pd.date_range(start=datetime.now(), periods=num_points, freq=f'{1/sampling_rate}S')
        
        # 生成基础信号
        t = np.linspace(0, duration, num_points)
        
        # 电压：稳定值 + 噪声 + 小幅波动
        voltage = voltage_nominal * (1 + noise_level * np.random.randn(num_points) + 0.1 * np.sin(2 * np.pi * 0.1 * t))
        
        # 电流：缓慢变化 + 噪声
        current = current_nominal * (1 + 0.5 * np.sin(2 * np.pi * 0.05 * t) + noise_level * np.random.randn(num_points))
        
        # 功率：电压 × 电流
        power = voltage * current
        
        df = pd.DataFrame({
            '序号': range(1, num_points + 1),
            '电流': current,
            '电压': voltage,
            '功率': power,
            '时间戳': time_stamps,
            '设备地址': 1,
            '设备类型': '测试设备'
        })
        
        return df
    
    @staticmethod
    def filter_data(
        df: pd.DataFrame,
        column: str,
        method: str = 'moving_average',
        window_size: int = 5
    ) -> pd.DataFrame:
        """
        数据滤波
        
        Args:
            df: 数据DataFrame
            column: 要滤波的列
            method: 滤波方法
            window_size: 窗口大小
            
        Returns:
            滤波后的DataFrame
        """
        df = df.copy()
        
        if method == 'moving_average':
            df[f'{column}_filtered'] = df[column].rolling(window=window_size, center=True).mean()
        elif method == 'exponential':
            df[f'{column}_filtered'] = df[column].ewm(span=window_size, adjust=False).mean()
        elif method == 'median':
            df[f'{column}_filtered'] = df[column].rolling(window=window_size, center=True).median()
        
        # 填充边缘值
        df[f'{column}_filtered'].fillna(df[column], inplace=True)
        
        return df