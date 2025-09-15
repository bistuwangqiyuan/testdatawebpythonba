"""
实验仿真页面
提供光伏关断器的虚拟仿真环境
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.supabase_client import get_supabase_client
from utils.visualization import Visualization
from utils.data_processor import DataProcessor
import time

# 页面配置
st.set_page_config(
    page_title="实验仿真 - 光伏关断器检测系统",
    page_icon="🎮",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .simulation-header {
        background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .circuit-container {
        background-color: #1e1e1e;
        border: 2px solid #6a1b9a;
        border-radius: 15px;
        padding: 2rem;
        position: relative;
        min-height: 400px;
    }
    .parameter-panel {
        background-color: #2e2e2e;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .simulation-control {
        background-color: #1e1e1e;
        border: 1px solid #3e3e3e;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .node-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin: 0 5px;
    }
    .node-active { background-color: #00e676; }
    .node-inactive { background-color: #424242; }
    .node-fault { background-color: #f44336; }
    .simulation-status {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        margin: 0.5rem;
    }
    .status-ready { background-color: #424242; color: #e0e0e0; }
    .status-running { background-color: #8e24aa; color: white; }
    .status-paused { background-color: #ff6f00; color: white; }
    .status-completed { background-color: #00c853; color: white; }
</style>
""", unsafe_allow_html=True)

# 仿真模型定义
class PVRSDSimulator:
    """光伏关断器仿真器"""
    
    def __init__(self, rated_voltage=1000, rated_current=10, rated_power=10000):
        self.rated_voltage = rated_voltage
        self.rated_current = rated_current
        self.rated_power = rated_power
        self.is_on = True
        self.fault_state = None
        self.temperature = 25  # 初始温度
        self.efficiency = 0.97  # 初始效率
        
    def calculate_output(self, input_voltage, input_current, time_step=0.1):
        """计算输出参数"""
        if not self.is_on or self.fault_state:
            return 0, 0, 0
        
        # 考虑温度影响
        temp_factor = 1 - (self.temperature - 25) * 0.002
        
        # 计算输出
        output_voltage = input_voltage * self.efficiency * temp_factor
        output_current = input_current * self.efficiency
        output_power = output_voltage * output_current
        
        # 更新温度（简化模型）
        power_loss = (input_voltage * input_current) * (1 - self.efficiency)
        self.temperature += power_loss * 0.001 * time_step
        self.temperature = max(25, min(self.temperature, 85))  # 限制温度范围
        
        return output_voltage, output_current, output_power
    
    def inject_fault(self, fault_type):
        """注入故障"""
        self.fault_state = fault_type
        if fault_type in ['short_circuit', 'overcurrent']:
            self.is_on = False  # 触发保护
    
    def clear_fault(self):
        """清除故障"""
        self.fault_state = None
        self.is_on = True
        self.temperature = 25

def main():
    # 获取Supabase客户端
    supabase = st.session_state.supabase
    
    # 页面标题
    st.markdown("""
    <div class="simulation-header">
        <h1 style="color: white; margin: 0;">🎮 实验仿真平台</h1>
        <p style="color: #f3e5f5; margin: 0;">光伏关断器虚拟仿真环境 - 安全、高效、可重复</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化仿真器
    if 'simulator' not in st.session_state:
        st.session_state.simulator = PVRSDSimulator()
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'simulation_data' not in st.session_state:
        st.session_state.simulation_data = []
    if 'simulation_time' not in st.session_state:
        st.session_state.simulation_time = 0
    
    # 创建布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 仿真控制面板
        st.subheader("🎛️ 仿真控制")
        
        control_col1, control_col2, control_col3, control_col4 = st.columns(4)
        
        with control_col1:
            if not st.session_state.simulation_running:
                if st.button("▶️ 开始仿真", type="primary", use_container_width=True):
                    st.session_state.simulation_running = True
                    st.session_state.simulation_start_time = time.time()
                    st.session_state.simulation_data = []
                    st.session_state.simulation_time = 0
                    st.rerun()
            else:
                if st.button("⏸️ 暂停仿真", type="secondary", use_container_width=True):
                    st.session_state.simulation_running = False
                    st.rerun()
        
        with control_col2:
            if st.button("⏹️ 停止仿真", use_container_width=True):
                st.session_state.simulation_running = False
                st.session_state.simulation_time = 0
                st.session_state.simulation_data = []
                st.session_state.simulator = PVRSDSimulator()
                st.rerun()
        
        with control_col3:
            if st.button("💾 保存数据", use_container_width=True):
                if st.session_state.simulation_data:
                    # 创建仿真实验记录
                    exp_data = {
                        "experiment_name": f"仿真实验_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "experiment_type": "simulation",
                        "operator_id": st.session_state.user.get("id", "guest"),
                        "notes": "虚拟仿真实验数据"
                    }
                    experiment = supabase.insert_experiment(exp_data)
                    
                    if experiment:
                        # 保存仿真数据
                        data_records = []
                        for i, data in enumerate(st.session_state.simulation_data):
                            record = {
                                'experiment_id': experiment['id'],
                                'sequence_number': i + 1,
                                'voltage': data['output_voltage'],
                                'current': data['output_current'],
                                'power': data['output_power'],
                                'temperature': data['temperature'],
                                'timestamp': datetime.now(),
                                'device_address': 1,
                                'device_type': 'Simulation'
                            }
                            data_records.append(record)
                        
                        if supabase.insert_experiment_data(data_records):
                            st.success("仿真数据已保存")
                        else:
                            st.error("数据保存失败")
        
        with control_col4:
            # 显示仿真状态
            if st.session_state.simulation_running:
                status_class = "status-running"
                status_text = "运行中"
            elif st.session_state.simulation_data:
                status_class = "status-completed"
                status_text = "已完成"
            else:
                status_class = "status-ready"
                status_text = "就绪"
            
            st.markdown(f'<div class="simulation-status {status_class}">{status_text}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 电路图和实时监控
        circuit_col, monitor_col = st.columns([1, 1])
        
        with circuit_col:
            st.subheader("🔌 电路示意图")
            
            # 创建简化的电路图
            fig_circuit = go.Figure()
            
            # 添加组件
            # 光伏输入
            fig_circuit.add_shape(
                type="rect",
                x0=0, y0=0.4, x1=0.2, y1=0.6,
                fillcolor="#ff6f00",
                line=dict(color="#ff6f00", width=2)
            )
            fig_circuit.add_annotation(
                x=0.1, y=0.7,
                text="PV Input",
                showarrow=False,
                font=dict(color="white", size=12)
            )
            
            # 关断器
            rsd_color = "#00e676" if st.session_state.simulator.is_on else "#f44336"
            fig_circuit.add_shape(
                type="rect",
                x0=0.4, y0=0.3, x1=0.6, y1=0.7,
                fillcolor=rsd_color,
                line=dict(color=rsd_color, width=2)
            )
            fig_circuit.add_annotation(
                x=0.5, y=0.5,
                text="PVRSD",
                showarrow=False,
                font=dict(color="white", size=14, weight="bold")
            )
            
            # 负载
            fig_circuit.add_shape(
                type="rect",
                x0=0.8, y0=0.4, x1=1.0, y1=0.6,
                fillcolor="#0288d1",
                line=dict(color="#0288d1", width=2)
            )
            fig_circuit.add_annotation(
                x=0.9, y=0.7,
                text="Load",
                showarrow=False,
                font=dict(color="white", size=12)
            )
            
            # 连接线
            fig_circuit.add_shape(
                type="line",
                x0=0.2, y0=0.5, x1=0.4, y1=0.5,
                line=dict(color="#ffffff", width=3)
            )
            fig_circuit.add_shape(
                type="line",
                x0=0.6, y0=0.5, x1=0.8, y1=0.5,
                line=dict(color="#ffffff", width=3)
            )
            
            # 更新布局
            fig_circuit.update_layout(
                showlegend=False,
                xaxis=dict(visible=False, range=[0, 1]),
                yaxis=dict(visible=False, range=[0, 1]),
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#1e1e1e',
                height=300,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_circuit, use_container_width=True)
            
            # 节点状态指示
            st.markdown("### 节点状态")
            col_n1, col_n2, col_n3 = st.columns(3)
            with col_n1:
                input_class = "node-active" if st.session_state.simulation_running else "node-inactive"
                st.markdown(f'<span class="node-indicator {input_class}"></span> 输入节点', unsafe_allow_html=True)
            with col_n2:
                rsd_class = "node-active" if st.session_state.simulator.is_on else "node-fault"
                st.markdown(f'<span class="node-indicator {rsd_class}"></span> 关断器', unsafe_allow_html=True)
            with col_n3:
                output_class = "node-active" if st.session_state.simulator.is_on and st.session_state.simulation_running else "node-inactive"
                st.markdown(f'<span class="node-indicator {output_class}"></span> 输出节点', unsafe_allow_html=True)
        
        with monitor_col:
            st.subheader("📊 实时监控")
            
            if st.session_state.simulation_running and st.session_state.simulation_data:
                latest_data = st.session_state.simulation_data[-1]
                
                # 显示实时数据
                met_col1, met_col2 = st.columns(2)
                with met_col1:
                    st.metric("输出电压", f"{latest_data['output_voltage']:.1f} V")
                    st.metric("输出电流", f"{latest_data['output_current']:.2f} A")
                with met_col2:
                    st.metric("输出功率", f"{latest_data['output_power']:.1f} W")
                    st.metric("设备温度", f"{latest_data['temperature']:.1f} °C")
                
                # 效率指标
                efficiency = (latest_data['output_power'] / latest_data['input_power'] * 100) if latest_data['input_power'] > 0 else 0
                st.metric("转换效率", f"{efficiency:.1f}%")
            else:
                st.info("等待仿真开始...")
    
    with col2:
        # 参数设置面板
        st.subheader("⚙️ 参数设置")
        
        with st.expander("输入参数", expanded=True):
            input_voltage = st.slider(
                "输入电压 (V)",
                min_value=0,
                max_value=1500,
                value=1000,
                step=10
            )
            
            input_current = st.slider(
                "输入电流 (A)",
                min_value=0.0,
                max_value=20.0,
                value=10.0,
                step=0.1
            )
            
            # 环境条件
            st.markdown("### 环境条件")
            ambient_temp = st.slider(
                "环境温度 (°C)",
                min_value=-40,
                max_value=85,
                value=25,
                step=5
            )
            
            irradiance = st.slider(
                "光照强度 (W/m²)",
                min_value=0,
                max_value=1200,
                value=1000,
                step=50
            )
        
        with st.expander("故障注入", expanded=True):
            st.markdown("### 🚨 故障模拟")
            
            fault_type = st.selectbox(
                "故障类型",
                ["无故障", "过流", "短路", "过温", "通信故障"]
            )
            
            if st.button("注入故障", type="secondary", use_container_width=True):
                if fault_type != "无故障":
                    st.session_state.simulator.inject_fault(fault_type)
                    st.warning(f"已注入{fault_type}故障")
                else:
                    st.session_state.simulator.clear_fault()
                    st.success("故障已清除")
        
        # 仿真设置
        with st.expander("仿真设置"):
            simulation_speed = st.select_slider(
                "仿真速度",
                options=[0.1, 0.5, 1.0, 2.0, 5.0],
                value=1.0,
                format_func=lambda x: f"{x}x"
            )
            
            data_points = st.number_input(
                "数据点数",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )
    
    # 仿真主循环
    if st.session_state.simulation_running:
        # 生成仿真数据
        time_step = 0.1 / simulation_speed
        
        # 计算输入功率（考虑光照影响）
        actual_input_voltage = input_voltage * (irradiance / 1000)
        actual_input_current = input_current * (irradiance / 1000)
        
        # 运行仿真
        output_v, output_i, output_p = st.session_state.simulator.calculate_output(
            actual_input_voltage,
            actual_input_current,
            time_step
        )
        
        # 记录数据
        data_point = {
            'time': st.session_state.simulation_time,
            'input_voltage': actual_input_voltage,
            'input_current': actual_input_current,
            'input_power': actual_input_voltage * actual_input_current,
            'output_voltage': output_v,
            'output_current': output_i,
            'output_power': output_p,
            'temperature': st.session_state.simulator.temperature,
            'efficiency': st.session_state.simulator.efficiency
        }
        
        st.session_state.simulation_data.append(data_point)
        st.session_state.simulation_time += time_step
        
        # 限制数据点数
        if len(st.session_state.simulation_data) > data_points:
            st.session_state.simulation_data.pop(0)
        
        # 显示实时曲线
        if len(st.session_state.simulation_data) > 10:
            df_sim = pd.DataFrame(st.session_state.simulation_data)
            
            # 创建多子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('电压', '电流', '功率', '温度'),
                specs=[[{'secondary_y': False}, {'secondary_y': False}],
                      [{'secondary_y': False}, {'secondary_y': False}]]
            )
            
            # 电压曲线
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['input_voltage'], name='输入电压', line=dict(color='#ff6f00')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['output_voltage'], name='输出电压', line=dict(color='#00e676')),
                row=1, col=1
            )
            
            # 电流曲线
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['input_current'], name='输入电流', line=dict(color='#ff6f00')),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['output_current'], name='输出电流', line=dict(color='#00e676')),
                row=1, col=2
            )
            
            # 功率曲线
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['input_power'], name='输入功率', line=dict(color='#ff6f00')),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['output_power'], name='输出功率', line=dict(color='#00e676')),
                row=2, col=1
            )
            
            # 温度曲线
            fig.add_trace(
                go.Scatter(x=df_sim['time'], y=df_sim['temperature'], name='设备温度', line=dict(color='#f44336')),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=600,
                showlegend=True,
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#121212',
                font=dict(color='#ffffff'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5
                )
            )
            
            # 更新坐标轴
            fig.update_xaxes(title_text="时间 (s)", gridcolor='#2e2e2e')
            fig.update_yaxes(title_text="电压 (V)", row=1, col=1, gridcolor='#2e2e2e')
            fig.update_yaxes(title_text="电流 (A)", row=1, col=2, gridcolor='#2e2e2e')
            fig.update_yaxes(title_text="功率 (W)", row=2, col=1, gridcolor='#2e2e2e')
            fig.update_yaxes(title_text="温度 (°C)", row=2, col=2, gridcolor='#2e2e2e')
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 延时刷新
        time.sleep(time_step)
        st.rerun()
    
    # 仿真分析工具
    if st.session_state.simulation_data and not st.session_state.simulation_running:
        st.markdown("---")
        st.subheader("📈 仿真分析")
        
        df_analysis = pd.DataFrame(st.session_state.simulation_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 性能统计")
            avg_efficiency = (df_analysis['output_power'].mean() / df_analysis['input_power'].mean() * 100)
            st.metric("平均效率", f"{avg_efficiency:.2f}%")
            st.metric("功率损耗", f"{(df_analysis['input_power'] - df_analysis['output_power']).mean():.1f} W")
            st.metric("最高温度", f"{df_analysis['temperature'].max():.1f} °C")
        
        with col2:
            st.markdown("### 稳定性分析")
            voltage_std = df_analysis['output_voltage'].std()
            current_std = df_analysis['output_current'].std()
            st.metric("电压稳定性", f"±{voltage_std:.2f} V")
            st.metric("电流稳定性", f"±{current_std:.3f} A")
            st.metric("温升", f"{df_analysis['temperature'].iloc[-1] - df_analysis['temperature'].iloc[0]:.1f} °C")
        
        with col3:
            st.markdown("### 故障响应")
            if st.session_state.simulator.fault_state:
                st.error(f"当前故障: {st.session_state.simulator.fault_state}")
                st.metric("保护状态", "已触发" if not st.session_state.simulator.is_on else "未触发")
            else:
                st.success("系统正常")
                st.metric("运行时间", f"{st.session_state.simulation_time:.1f} s")

if __name__ == "__main__":
    main()