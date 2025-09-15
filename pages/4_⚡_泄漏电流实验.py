"""
泄漏电流实验页面
按照IEC 62109-2标准进行泄漏电流测试
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from utils.supabase_client import get_supabase_client, require_auth, require_role
from utils.visualization import Visualization
from utils.data_processor import DataProcessor

# 页面配置
st.set_page_config(
    page_title="泄漏电流实验 - 光伏关断器检测系统",
    page_icon="⚡",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .experiment-header {
        background: linear-gradient(135deg, #ff6f00 0%, #ff8f00 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .test-condition-card {
        background-color: #1e1e1e;
        border: 2px solid #ff6f00;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .test-condition-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255,111,0,0.3);
    }
    .test-phase {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        background-color: #2e2e2e;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .test-phase.active {
        background-color: #ff6f00;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@require_auth
@require_role(['engineer', 'admin'])
def main():
    # 获取Supabase客户端
    supabase = st.session_state.supabase
    
    # 页面标题
    st.markdown("""
    <div class="experiment-header">
        <h1 style="color: white; margin: 0;">⚡ 泄漏电流实验（Leakage Current Test）</h1>
        <p style="color: #fff3e0; margin: 0;">参考标准: IEC 62109-2 | 测试不同环境条件下的泄漏电流</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'leakage_experiment_running' not in st.session_state:
        st.session_state.leakage_experiment_running = False
    if 'leakage_data' not in st.session_state:
        st.session_state.leakage_data = []
    if 'current_phase' not in st.session_state:
        st.session_state.current_phase = 0
    if 'phase_start_time' not in st.session_state:
        st.session_state.phase_start_time = None
    
    # 测试阶段定义
    test_phases = [
        {"name": "常温测试", "temp": 25, "humidity": 60, "duration": 30},
        {"name": "高温测试", "temp": 40, "humidity": 60, "duration": 30},
        {"name": "极高温测试", "temp": 60, "humidity": 60, "duration": 30},
        {"name": "高湿测试", "temp": 25, "humidity": 93, "duration": 30},
        {"name": "高温高湿", "temp": 40, "humidity": 93, "duration": 30}
    ]
    
    # 侧边栏 - 实验参数设置
    with st.sidebar:
        st.subheader("🔧 实验参数设置")
        
        # 获取测试标准
        standards = supabase.get_test_standards('leakage')
        if standards:
            standard = standards[0]
            params = standard.get('parameters', {})
            criteria = standard.get('pass_criteria', {})
            
            st.info(f"标准: {standard['standard_name']}")
            
            # 参数设置
            rated_voltage = st.number_input(
                "额定电压 (V)",
                min_value=0.0,
                max_value=1500.0,
                value=1000.0,
                step=10.0
            )
            
            test_voltage = st.number_input(
                "测试电压 (V)",
                min_value=0.0,
                max_value=2000.0,
                value=rated_voltage * 1.1,
                step=10.0,
                help=params.get('test_voltage', '1.1×额定电压')
            )
            
            # 泄漏电流限值
            st.markdown("### 泄漏电流限值 (mA)")
            leakage_limit_25c = st.number_input(
                "25°C限值",
                min_value=0.1,
                max_value=10.0,
                value=float(criteria.get('max_leakage_25C', 3.5)),
                step=0.1
            )
            
            leakage_limit_60c = st.number_input(
                "60°C限值",
                min_value=0.1,
                max_value=10.0,
                value=float(criteria.get('max_leakage_60C', 5.0)),
                step=0.1
            )
        else:
            st.error("未找到测试标准")
            test_voltage = 1100.0
            leakage_limit_25c = 3.5
            leakage_limit_60c = 5.0
        
        st.markdown("---")
        
        # 设备选择
        st.subheader("🔌 设备选择")
        devices = supabase.get_devices()
        if devices:
            device_options = {f"{d['device_serial']} - {d['device_model']}": d['id'] for d in devices}
            selected_device = st.selectbox(
                "选择测试设备",
                options=list(device_options.keys())
            )
            device_id = device_options[selected_device]
        else:
            st.warning("请先添加设备")
            device_id = None
        
        # 实验信息
        experiment_name = st.text_input(
            "实验名称",
            value=f"泄漏电流实验_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        
        # 测试阶段选择
        st.markdown("### 测试阶段")
        selected_phases = []
        for phase in test_phases:
            if st.checkbox(phase['name'], value=True):
                selected_phases.append(phase)
    
    # 主要内容区域
    # 显示测试阶段流程
    st.subheader("🔄 测试流程")
    phase_cols = st.columns(len(test_phases))
    for i, (col, phase) in enumerate(zip(phase_cols, test_phases)):
        with col:
            is_active = st.session_state.leakage_experiment_running and st.session_state.current_phase == i
            phase_class = "test-phase active" if is_active else "test-phase"
            st.markdown(f"""
            <div class="{phase_class}">
                {phase['name']}<br>
                <small>{phase['temp']}°C / {phase['humidity']}%RH</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 实验控制
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if not st.session_state.leakage_experiment_running:
            if st.button("▶️ 开始实验", type="primary", use_container_width=True):
                if device_id and selected_phases:
                    # 创建实验记录
                    exp_data = {
                        "experiment_name": experiment_name,
                        "experiment_type": "leakage",
                        "device_id": device_id,
                        "operator_id": st.session_state.user.id,
                        "notes": f"测试阶段: {', '.join([p['name'] for p in selected_phases])}"
                    }
                    experiment = supabase.insert_experiment(exp_data)
                    
                    if experiment:
                        st.session_state.leakage_experiment_id = experiment['id']
                        st.session_state.leakage_experiment_running = True
                        st.session_state.current_phase = 0
                        st.session_state.phase_start_time = time.time()
                        st.session_state.leakage_data = []
                        st.session_state.selected_phases = selected_phases
                        st.success("实验已开始")
                        st.rerun()
                    else:
                        st.error("创建实验失败")
                else:
                    st.error("请选择测试设备和至少一个测试阶段")
        else:
            if st.button("⏹️ 停止实验", type="secondary", use_container_width=True):
                st.session_state.leakage_experiment_running = False
                # 更新实验状态
                supabase.client.table("experiments").update({
                    "status": "completed",
                    "end_time": datetime.now().isoformat()
                }).eq("id", st.session_state.leakage_experiment_id).execute()
                st.success("实验已停止")
        
        # 实时数据显示
        if st.session_state.leakage_experiment_running:
            current_phase = st.session_state.selected_phases[st.session_state.current_phase]
            elapsed_time = time.time() - st.session_state.phase_start_time
            
            # 检查是否需要切换到下一阶段
            if elapsed_time > current_phase['duration']:
                st.session_state.current_phase += 1
                if st.session_state.current_phase < len(st.session_state.selected_phases):
                    st.session_state.phase_start_time = time.time()
                    st.rerun()
                else:
                    st.session_state.leakage_experiment_running = False
                    # 实验完成，判定结果
                    result = "pass"  # 简化判定逻辑
                    supabase.client.table("experiments").update({
                        "status": "completed",
                        "result": result,
                        "end_time": datetime.now().isoformat()
                    }).eq("id", st.session_state.leakage_experiment_id).execute()
            
            # 显示当前测试信息
            st.markdown(f"""
            ### 当前测试: {current_phase['name']}
            - **温度**: {current_phase['temp']}°C
            - **湿度**: {current_phase['humidity']}%RH
            - **进度**: {elapsed_time:.0f}/{current_phase['duration']}秒
            """)
            
            # 进度条
            st.progress(elapsed_time / current_phase['duration'])
            
            # 生成模拟数据
            # 泄漏电流随温度和湿度增加
            base_leakage = 2.0  # 基础泄漏电流 mA
            temp_factor = 1 + (current_phase['temp'] - 25) * 0.02  # 温度系数
            humidity_factor = 1 + (current_phase['humidity'] - 60) * 0.01  # 湿度系数
            
            leakage_current = base_leakage * temp_factor * humidity_factor
            leakage_current += np.random.normal(0, 0.2)  # 添加噪声
            leakage_current = max(0.1, leakage_current)  # 确保为正值
            
            data_point = {
                'experiment_id': st.session_state.leakage_experiment_id,
                'sequence_number': len(st.session_state.leakage_data) + 1,
                'voltage': test_voltage,
                'current': leakage_current / 1000,  # 转换为A
                'power': test_voltage * leakage_current / 1000,
                'temperature': current_phase['temp'],
                'humidity': current_phase['humidity'],
                'timestamp': datetime.now(),
                'device_address': 1,
                'device_type': 'PVRSD'
            }
            
            st.session_state.leakage_data.append(data_point)
            
            # 每5个数据点保存一次
            if len(st.session_state.leakage_data) % 5 == 0:
                supabase.insert_experiment_data(st.session_state.leakage_data[-5:])
            
            # 显示实时数据图表
            if len(st.session_state.leakage_data) > 1:
                df = pd.DataFrame(st.session_state.leakage_data)
                
                # 泄漏电流曲线
                fig = Visualization.create_realtime_line_chart(
                    df,
                    x_col='timestamp',
                    y_cols=['current'],
                    title="泄漏电流实时监测"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 各阶段对比（如果有多个阶段的数据）
                if st.session_state.current_phase > 0:
                    # 按温度和湿度分组统计
                    grouped = df.groupby(['temperature', 'humidity'])['current'].agg(['mean', 'max', 'min']).reset_index()
                    
                    fig_compare = Visualization.create_bar_chart(
                        grouped,
                        x_col='temperature',
                        y_col='mean',
                        title="不同条件下的平均泄漏电流",
                        color_col='humidity'
                    )
                    st.plotly_chart(fig_compare, use_container_width=True)
            
            # 每秒刷新
            time.sleep(1)
            st.rerun()
    
    with col2:
        # 实时指标和判定
        st.subheader("📊 实时监测")
        
        if st.session_state.leakage_experiment_running and st.session_state.leakage_data:
            current_data = st.session_state.leakage_data[-1]
            current_phase = st.session_state.selected_phases[st.session_state.current_phase]
            
            # 泄漏电流仪表
            # 根据温度选择限值
            if current_phase['temp'] <= 25:
                limit = leakage_limit_25c
            else:
                limit = leakage_limit_60c
            
            leakage_gauge = Visualization.create_gauge_chart(
                value=current_data['current'] * 1000,
                title="泄漏电流",
                min_val=0,
                max_val=limit * 1.5,
                threshold=limit,
                unit="mA"
            )
            st.plotly_chart(leakage_gauge, use_container_width=True)
            
            # 环境条件显示
            col_temp, col_hum = st.columns(2)
            with col_temp:
                st.metric("温度", f"{current_phase['temp']}°C")
            with col_hum:
                st.metric("湿度", f"{current_phase['humidity']}%RH")
            
            # 判定结果
            if current_data['current'] * 1000 > limit:
                st.error(f"⚠️ 泄漏电流超限! (>{limit}mA)")
            else:
                st.success("✅ 泄漏电流正常")
            
            # 统计信息
            df_current_phase = pd.DataFrame([d for d in st.session_state.leakage_data 
                                           if d['temperature'] == current_phase['temp'] 
                                           and d['humidity'] == current_phase['humidity']])
            if len(df_current_phase) > 0:
                st.markdown("### 📈 当前阶段统计")
                st.metric("平均值", f"{df_current_phase['current'].mean() * 1000:.2f} mA")
                st.metric("最大值", f"{df_current_phase['current'].max() * 1000:.2f} mA")
                st.metric("最小值", f"{df_current_phase['current'].min() * 1000:.2f} mA")
        else:
            st.info("等待实验开始...")
    
    # 测试标准说明
    with st.expander("📖 测试标准说明"):
        st.markdown("""
        ### IEC 62109-2 泄漏电流测试要求
        
        **测试目的**: 验证光伏关断器在不同环境条件下的绝缘性能
        
        **测试条件**:
        - 常温测试: 25°C, 60%RH
        - 高温测试: 40°C, 60%RH
        - 极高温测试: 60°C, 60%RH
        - 高湿测试: 25°C, 93%RH
        - 高温高湿: 40°C, 93%RH
        
        **判定标准**:
        - 25°C条件下: ≤ 3.5mA
        - 60°C条件下: ≤ 5.0mA
        - 其他温度按线性插值计算
        
        **注意事项**:
        - 每个测试阶段需稳定30秒以上
        - 测试电压为1.1倍额定电压
        - 需记录温度和湿度条件
        """)
    
    # 历史数据分析
    st.markdown("---")
    st.subheader("📊 历史数据分析")
    
    # 获取历史泄漏电流实验数据
    history = supabase.client.table("experiments")\
        .select("*, experiment_data(temperature, humidity, current)")\
        .eq("experiment_type", "leakage")\
        .eq("status", "completed")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    if history.data and any(exp.get('experiment_data') for exp in history.data):
        # 汇总所有历史数据
        all_data = []
        for exp in history.data:
            if exp.get('experiment_data'):
                for data in exp['experiment_data']:
                    all_data.append({
                        'experiment': exp['experiment_name'],
                        'temperature': data['temperature'],
                        'humidity': data['humidity'],
                        'leakage': data['current'] * 1000  # 转换为mA
                    })
        
        if all_data:
            df_history = pd.DataFrame(all_data)
            
            # 创建热力图数据
            pivot_data = df_history.pivot_table(
                values='leakage',
                index='temperature',
                columns='humidity',
                aggfunc='mean'
            )
            
            fig_heatmap = Visualization.create_heatmap(
                pivot_data,
                title="泄漏电流热力图 (mA) - 温度vs湿度"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

if __name__ == "__main__":
    main()