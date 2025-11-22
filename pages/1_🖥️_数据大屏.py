"""
数据展示大屏页面
实时监控和数据可视化
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from utils.supabase_client import get_supabase_client
from utils.visualization import Visualization
from utils.data_processor import DataProcessor

# 页面配置
st.set_page_config(
    page_title="数据大屏 - 光伏关断器检测系统",
    page_icon="🖥️",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
        color: #ffffff;
    }
    .dashboard-header {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 10px;
        padding: 1.5rem;
        height: 100%;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 获取Supabase客户端
    supabase = st.session_state.get('supabase')
    
    # 页面标题
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="color: white; margin: 0;">🖥️ 实时数据监控大屏</h1>
        <p style="color: #e0e0e0; margin: 0;">光伏关断器检测数据实时展示</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 控制面板
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # 选择实验
        experiments = supabase.get_experiments(limit=20)
        if experiments:
            exp_options = {f"{exp['experiment_name']} ({exp['id'][:8]})": exp['id'] 
                          for exp in experiments}
            selected_exp = st.selectbox(
                "选择实验",
                options=list(exp_options.keys()),
                index=0
            )
            experiment_id = exp_options[selected_exp]
        else:
            st.warning("暂无实验数据")
            return
    
    with col2:
        # 时间范围选择
        time_range = st.selectbox(
            "时间范围",
            ["实时", "最近1小时", "最近24小时", "最近7天"],
            index=0
        )
    
    with col3:
        # 刷新频率
        refresh_rate = st.selectbox(
            "刷新频率",
            ["1秒", "5秒", "10秒", "30秒", "手动"],
            index=1
        )
    
    with col4:
        # 刷新按钮
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
    
    # 自动刷新
    if refresh_rate != "手动":
        refresh_seconds = int(refresh_rate.split("秒")[0])
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        if time.time() - st.session_state.last_refresh > refresh_seconds:
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    st.markdown("---")
    
    # 获取实验数据
    exp_data = supabase.get_experiment_data(experiment_id)
    
    if exp_data:
        # 转换为DataFrame
        df = pd.DataFrame(exp_data)
        
        # 数据处理
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 第一行：关键指标
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            current_avg = df['current'].mean()
            current_delta = df['current'].iloc[-1] - df['current'].iloc[0] if len(df) > 1 else 0
            st.metric(
                label="平均电流",
                value=f"{current_avg:.2f} A",
                delta=f"{current_delta:.2f} A"
            )
        
        with col2:
            voltage_avg = df['voltage'].mean()
            voltage_delta = df['voltage'].iloc[-1] - df['voltage'].iloc[0] if len(df) > 1 else 0
            st.metric(
                label="平均电压",
                value=f"{voltage_avg:.2f} V",
                delta=f"{voltage_delta:.2f} V"
            )
        
        with col3:
            power_avg = df['power'].mean()
            power_delta = df['power'].iloc[-1] - df['power'].iloc[0] if len(df) > 1 else 0
            st.metric(
                label="平均功率",
                value=f"{power_avg:.2f} W",
                delta=f"{power_delta:.2f} W"
            )
        
        with col4:
            efficiency = (df['power'] / (df['current'] * df['voltage'])).mean() * 100
            st.metric(
                label="效率",
                value=f"{efficiency:.1f}%",
                delta=None
            )
        
        with col5:
            data_points = len(df)
            st.metric(
                label="数据点数",
                value=f"{data_points:,}",
                delta=None
            )
        
        with col6:
            uptime = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 60
            st.metric(
                label="运行时间",
                value=f"{uptime:.1f} 分钟",
                delta=None
            )
        
        st.markdown("---")
        
        # 第二行：图表
        tab1, tab2, tab3, tab4 = st.tabs(["📈 实时曲线", "📊 统计分析", "🔥 热力图", "📉 趋势分析"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 多Y轴实时曲线
                fig = Visualization.create_multi_axis_chart(
                    df,
                    x_col='timestamp',
                    y1_cols=['current', 'voltage'],
                    y2_cols=['power'],
                    title="电流、电压、功率实时曲线"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 仪表盘
                st.subheader("实时监控")
                
                # 电流仪表盘
                current_gauge = Visualization.create_gauge_chart(
                    value=df['current'].iloc[-1],
                    title="当前电流",
                    min_val=0,
                    max_val=df['current'].max() * 1.2,
                    threshold=df['current'].max() * 0.9,
                    unit="A"
                )
                st.plotly_chart(current_gauge, use_container_width=True)
                
                # 电压仪表盘
                voltage_gauge = Visualization.create_gauge_chart(
                    value=df['voltage'].iloc[-1],
                    title="当前电压",
                    min_val=0,
                    max_val=df['voltage'].max() * 1.2,
                    threshold=df['voltage'].max() * 0.9,
                    unit="V"
                )
                st.plotly_chart(voltage_gauge, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # 数据分布直方图
                fig_hist = Visualization.create_bar_chart(
                    df.groupby(pd.cut(df['power'], bins=10))['power'].count().reset_index(),
                    x_col='power',
                    y_col='power',
                    title="功率分布直方图"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # 统计饼图
                status_counts = {
                    "正常": len(df[df['power'] < df['power'].mean() * 1.1]),
                    "警告": len(df[(df['power'] >= df['power'].mean() * 1.1) & 
                                  (df['power'] < df['power'].mean() * 1.3)]),
                    "异常": len(df[df['power'] >= df['power'].mean() * 1.3])
                }
                
                fig_pie = Visualization.create_pie_chart(
                    values=list(status_counts.values()),
                    labels=list(status_counts.keys()),
                    title="数据状态分布"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # 统计表格
            st.subheader("📊 统计信息")
            stats = DataProcessor.calculate_statistics(df)
            
            stats_df = pd.DataFrame([
                {"指标": key, "数值": f"{value:.2f}"} 
                for key, value in stats.items()
            ])
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        with tab3:
            # 创建热力图数据
            # 将时间分组并计算平均值
            df['hour'] = df['timestamp'].dt.hour
            df['minute_group'] = df['timestamp'].dt.minute // 10 * 10
            
            heatmap_data = df.pivot_table(
                values='power',
                index='hour',
                columns='minute_group',
                aggfunc='mean'
            )
            
            fig_heatmap = Visualization.create_heatmap(
                heatmap_data,
                title="功率热力图（按时间分布）"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab4:
            # 趋势分析
            col1, col2 = st.columns(2)
            
            with col1:
                # 移动平均
                window_size = st.slider("移动平均窗口", 5, 50, 20)
                df_filtered = DataProcessor.filter_data(df, 'power', window_size=window_size)
                
                fig_trend = Visualization.create_realtime_line_chart(
                    df_filtered,
                    x_col='timestamp',
                    y_cols=['power', 'power_filtered'],
                    title="功率趋势分析（移动平均）"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with col2:
                # 异常检测
                df_anomaly = DataProcessor.detect_anomalies(df, 'power')
                anomaly_count = df_anomaly['异常'].sum()
                
                st.info(f"检测到 {anomaly_count} 个异常数据点")
                
                if anomaly_count > 0:
                    fig_anomaly = Visualization.create_realtime_line_chart(
                        df_anomaly[df_anomaly['异常']],
                        x_col='timestamp',
                        y_cols=['power'],
                        title="异常数据点"
                    )
                    st.plotly_chart(fig_anomaly, use_container_width=True)
    
    else:
        st.info("该实验暂无数据")
    
    # 底部信息栏
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"🕐 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.caption(f"📡 数据源: Supabase 实时数据库")
    
    with col3:
        st.caption(f"🔧 系统状态: 正常运行")

if __name__ == "__main__":
    main()