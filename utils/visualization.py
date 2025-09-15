"""
数据可视化模块
提供各种图表和可视化功能
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import streamlit as st


class Visualization:
    """数据可视化类"""
    
    # 工业化配色方案
    COLORS = {
        'primary': '#1a237e',      # 深蓝色
        'secondary': '#ff6f00',    # 橙色
        'success': '#00c853',      # 绿色
        'danger': '#d32f2f',       # 红色
        'warning': '#f57c00',      # 深橙色
        'info': '#0288d1',         # 浅蓝色
        'dark': '#121212',         # 深灰色
        'light': '#e0e0e0',        # 浅灰色
        'grid': '#2e2e2e',         # 网格线颜色
        'text': '#ffffff'          # 文字颜色
    }
    
    # 深色主题布局
    DARK_LAYOUT = {
        'plot_bgcolor': '#1e1e1e',
        'paper_bgcolor': '#121212',
        'font': {'color': '#ffffff', 'family': 'Inter, sans-serif'},
        'xaxis': {
            'gridcolor': '#2e2e2e',
            'linecolor': '#3e3e3e',
            'tickfont': {'color': '#b0b0b0'}
        },
        'yaxis': {
            'gridcolor': '#2e2e2e',
            'linecolor': '#3e3e3e',
            'tickfont': {'color': '#b0b0b0'}
        },
        'hoverlabel': {
            'bgcolor': '#2e2e2e',
            'font': {'color': '#ffffff'}
        }
    }
    
    @classmethod
    def create_realtime_line_chart(
        cls,
        df: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        title: str = "实时数据监控"
    ) -> go.Figure:
        """
        创建实时折线图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列名
            y_cols: Y轴列名列表
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        fig = go.Figure()
        
        colors = [cls.COLORS['primary'], cls.COLORS['secondary'], cls.COLORS['success']]
        
        for i, col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[col],
                mode='lines',
                name=col,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'{col}: %{{y:.2f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            **cls.DARK_LAYOUT,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode='x unified'
        )
        
        return fig
    
    @classmethod
    def create_gauge_chart(
        cls,
        value: float,
        title: str,
        min_val: float = 0,
        max_val: float = 100,
        threshold: float = None,
        unit: str = ""
    ) -> go.Figure:
        """
        创建仪表盘图
        
        Args:
            value: 当前值
            title: 标题
            min_val: 最小值
            max_val: 最大值
            threshold: 阈值
            unit: 单位
            
        Returns:
            Plotly图表对象
        """
        # 确定颜色
        if threshold:
            color = cls.COLORS['danger'] if value > threshold else cls.COLORS['success']
        else:
            color = cls.COLORS['primary']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 18}},
            number={'suffix': unit, 'font': {'size': 36}},
            gauge={
                'axis': {
                    'range': [min_val, max_val],
                    'tickwidth': 1,
                    'tickcolor': cls.COLORS['light']
                },
                'bar': {'color': color},
                'bgcolor': cls.COLORS['dark'],
                'borderwidth': 2,
                'bordercolor': cls.COLORS['grid'],
                'steps': [
                    {'range': [min_val, max_val], 'color': cls.COLORS['grid']}
                ],
                'threshold': {
                    'line': {'color': cls.COLORS['danger'], 'width': 4},
                    'thickness': 0.75,
                    'value': threshold if threshold else max_val
                }
            }
        ))
        
        fig.update_layout(
            **cls.DARK_LAYOUT,
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig
    
    @classmethod
    def create_heatmap(
        cls,
        data: pd.DataFrame,
        title: str = "数据热力图"
    ) -> go.Figure:
        """
        创建热力图
        
        Args:
            data: 数据DataFrame
            title: 标题
            
        Returns:
            Plotly图表对象
        """
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=[
                [0, cls.COLORS['dark']],
                [0.5, cls.COLORS['warning']],
                [1, cls.COLORS['danger']]
            ],
            hovertemplate='%{x}<br>%{y}<br>值: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            **cls.DARK_LAYOUT
        )
        
        return fig
    
    @classmethod
    def create_3d_surface(
        cls,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        title: str = "3D数据可视化"
    ) -> go.Figure:
        """
        创建3D曲面图
        
        Args:
            x, y, z: 数据数组
            title: 标题
            
        Returns:
            Plotly图表对象
        """
        fig = go.Figure(data=[go.Surface(
            x=x,
            y=y,
            z=z,
            colorscale='Viridis',
            showscale=True,
            hovertemplate='X: %{x}<br>Y: %{y}<br>Z: %{z}<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            scene=dict(
                xaxis=dict(
                    gridcolor=cls.COLORS['grid'],
                    backgroundcolor=cls.COLORS['dark']
                ),
                yaxis=dict(
                    gridcolor=cls.COLORS['grid'],
                    backgroundcolor=cls.COLORS['dark']
                ),
                zaxis=dict(
                    gridcolor=cls.COLORS['grid'],
                    backgroundcolor=cls.COLORS['dark']
                ),
                bgcolor=cls.COLORS['dark']
            ),
            **cls.DARK_LAYOUT
        )
        
        return fig
    
    @classmethod
    def create_multi_axis_chart(
        cls,
        df: pd.DataFrame,
        x_col: str,
        y1_cols: List[str],
        y2_cols: List[str],
        title: str = "多轴图表"
    ) -> go.Figure:
        """
        创建双Y轴图表
        
        Args:
            df: 数据DataFrame
            x_col: X轴列名
            y1_cols: 第一Y轴列名列表
            y2_cols: 第二Y轴列名列表
            title: 标题
            
        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]]
        )
        
        # 第一Y轴数据
        colors1 = [cls.COLORS['primary'], cls.COLORS['info']]
        for i, col in enumerate(y1_cols):
            fig.add_trace(
                go.Scatter(
                    x=df[x_col],
                    y=df[col],
                    name=col,
                    line=dict(color=colors1[i % len(colors1)], width=2)
                ),
                secondary_y=False
            )
        
        # 第二Y轴数据
        colors2 = [cls.COLORS['secondary'], cls.COLORS['warning']]
        for i, col in enumerate(y2_cols):
            fig.add_trace(
                go.Scatter(
                    x=df[x_col],
                    y=df[col],
                    name=col,
                    line=dict(color=colors2[i % len(colors2)], width=2, dash='dash')
                ),
                secondary_y=True
            )
        
        fig.update_xaxes(
            title_text=x_col,
            gridcolor=cls.COLORS['grid'],
            linecolor=cls.COLORS['grid']
        )
        
        fig.update_yaxes(
            title_text=", ".join(y1_cols),
            secondary_y=False,
            gridcolor=cls.COLORS['grid'],
            linecolor=cls.COLORS['grid']
        )
        
        fig.update_yaxes(
            title_text=", ".join(y2_cols),
            secondary_y=True,
            gridcolor=cls.COLORS['grid'],
            linecolor=cls.COLORS['grid']
        )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            **cls.DARK_LAYOUT,
            hovermode='x unified'
        )
        
        return fig
    
    @classmethod
    def create_bar_chart(
        cls,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "柱状图",
        color_col: str = None
    ) -> go.Figure:
        """
        创建柱状图
        
        Args:
            df: 数据DataFrame
            x_col: X轴列名
            y_col: Y轴列名
            title: 标题
            color_col: 颜色分组列名
            
        Returns:
            Plotly图表对象
        """
        if color_col:
            fig = px.bar(
                df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=[
                    cls.COLORS['primary'],
                    cls.COLORS['secondary'],
                    cls.COLORS['success']
                ]
            )
        else:
            fig = go.Figure(data=[
                go.Bar(
                    x=df[x_col],
                    y=df[y_col],
                    marker_color=cls.COLORS['primary'],
                    hovertemplate='%{x}<br>%{y}<extra></extra>'
                )
            ])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            **cls.DARK_LAYOUT
        )
        
        return fig
    
    @classmethod
    def create_pie_chart(
        cls,
        values: List[float],
        labels: List[str],
        title: str = "饼图"
    ) -> go.Figure:
        """
        创建饼图
        
        Args:
            values: 数值列表
            labels: 标签列表
            title: 标题
            
        Returns:
            Plotly图表对象
        """
        colors = [
            cls.COLORS['primary'],
            cls.COLORS['secondary'],
            cls.COLORS['success'],
            cls.COLORS['warning'],
            cls.COLORS['info']
        ]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=colors[:len(labels)]),
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>%{value}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            **cls.DARK_LAYOUT,
            showlegend=True
        )
        
        return fig
    
    @classmethod
    def create_scatter_matrix(
        cls,
        df: pd.DataFrame,
        dimensions: List[str],
        title: str = "散点矩阵图"
    ) -> go.Figure:
        """
        创建散点矩阵图
        
        Args:
            df: 数据DataFrame
            dimensions: 维度列表
            title: 标题
            
        Returns:
            Plotly图表对象
        """
        fig = go.Figure(data=go.Splom(
            dimensions=[dict(label=col, values=df[col]) for col in dimensions],
            marker=dict(
                color=cls.COLORS['primary'],
                size=5,
                line_color='white',
                line_width=0.5
            ),
            diagonal=dict(visible=False),
            showupperhalf=False
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            **cls.DARK_LAYOUT,
            dragmode='select',
            hovermode='closest'
        )
        
        return fig
    
    @staticmethod
    def display_metrics(metrics: Dict[str, Tuple[float, str, float]]):
        """
        显示指标卡片
        
        Args:
            metrics: 指标字典 {名称: (值, 单位, 变化值)}
        """
        cols = st.columns(len(metrics))
        
        for i, (name, (value, unit, delta)) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(
                    label=name,
                    value=f"{value:.2f} {unit}",
                    delta=f"{delta:.2f} {unit}" if delta else None,
                    delta_color="normal" if delta and delta >= 0 else "inverse"
                )