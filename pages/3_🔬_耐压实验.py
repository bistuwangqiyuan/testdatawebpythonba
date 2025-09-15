"""
耐压实验页面
按照IEC 60947-3标准进行耐压测试
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
    page_title="耐压实验 - 光伏关断器检测系统",
    page_icon="🔬",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .experiment-header {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .parameter-card {
        background-color: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .status-indicator {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .status-running { background-color: #ff6f00; }
    .status-completed { background-color: #00c853; }
    .status-failed { background-color: #d32f2f; }
</style>
""", unsafe_allow_html=True)

def main():
    # 获取Supabase客户端
    supabase = st.session_state.supabase
    
    # 页面标题
    st.markdown("""
    <div class="experiment-header">
        <h1 style="color: white; margin: 0;">🔬 耐压实验（Dielectric Withstand Test）</h1>
        <p style="color: #e0e0e0; margin: 0;">参考标准: IEC 60947-3, UL 1741 | 测试光伏关断器的绝缘性能</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'experiment_running' not in st.session_state:
        st.session_state.experiment_running = False
    if 'experiment_data' not in st.session_state:
        st.session_state.experiment_data = []
    if 'experiment_start_time' not in st.session_state:
        st.session_state.experiment_start_time = None
    
    # 侧边栏 - 实验参数设置
    with st.sidebar:
        st.subheader("🔧 实验参数设置")
        
        # 获取测试标准
        standards = supabase.get_test_standards('dielectric')
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
                max_value=5000.0,
                value=1000.0 + 2 * rated_voltage,
                step=10.0,
                help=params.get('test_voltage', '1000V DC + 2×额定电压')
            )
            
            test_duration = st.number_input(
                "测试时间 (秒)",
                min_value=1,
                max_value=300,
                value=params.get('test_duration', 60),
                step=1
            )
            
            leakage_limit = st.number_input(
                "漏电流限值 (mA)",
                min_value=0.1,
                max_value=10.0,
                value=float(params.get('leakage_limit', 5.0)),
                step=0.1
            )
            
            ramp_rate = st.number_input(
                "升压速率 (V/s)",
                min_value=10.0,
                max_value=1000.0,
                value=100.0,
                step=10.0
            )
        else:
            st.error("未找到测试标准")
            test_voltage = 3000.0
            test_duration = 60
            leakage_limit = 5.0
            ramp_rate = 100.0
        
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
            value=f"耐压实验_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        
        notes = st.text_area("备注", height=100)
    
    # 主要内容区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 实验控制
        if not st.session_state.experiment_running:
            if st.button("▶️ 开始实验", type="primary", use_container_width=True):
                if device_id:
                    # 创建实验记录
                    exp_data = {
                        "experiment_name": experiment_name,
                        "experiment_type": "dielectric",
                        "device_id": device_id,
                        "operator_id": st.session_state.user.get("id", "guest"),
                        "notes": notes
                    }
                    experiment = supabase.insert_experiment(exp_data)
                    
                    if experiment:
                        st.session_state.experiment_id = experiment['id']
                        st.session_state.experiment_running = True
                        st.session_state.experiment_start_time = time.time()
                        st.session_state.experiment_data = []
                        if "exp_" in experiment['id']:
                            st.success("实验已开始（离线模式）")
                        else:
                            st.success("实验已开始")
                        st.rerun()
                    else:
                        # 使用临时ID继续实验
                        st.session_state.experiment_id = f"temp_exp_{int(time.time())}"
                        st.session_state.experiment_running = True
                        st.session_state.experiment_start_time = time.time()
                        st.session_state.experiment_data = []
                        st.warning("实验已开始（离线模式）")
                        st.rerun()
                else:
                    st.error("请选择测试设备")
        else:
            col_stop, col_pause = st.columns(2)
            with col_stop:
                if st.button("⏹️ 停止实验", type="secondary", use_container_width=True):
                    st.session_state.experiment_running = False
                    # 更新实验状态
                    supabase.client.table("experiments").update({
                        "status": "completed",
                        "end_time": datetime.now().isoformat()
                    }).eq("id", st.session_state.experiment_id).execute()
                    st.success("实验已停止")
        
        # 实时数据显示
        if st.session_state.experiment_running:
            # 模拟实验进度
            elapsed_time = time.time() - st.session_state.experiment_start_time
            
            # 计算当前阶段
            ramp_time = test_voltage / ramp_rate
            if elapsed_time < ramp_time:
                phase = "升压阶段"
                current_voltage = elapsed_time * ramp_rate
            elif elapsed_time < ramp_time + test_duration:
                phase = "保持阶段"
                current_voltage = test_voltage
            else:
                phase = "完成"
                current_voltage = test_voltage
                st.session_state.experiment_running = False
            
            # 生成模拟数据
            current_time = datetime.now()
            leakage_current = np.random.normal(2.5, 0.5) * (current_voltage / test_voltage)
            leakage_current = max(0, min(leakage_current, leakage_limit))
            
            data_point = {
                'experiment_id': st.session_state.experiment_id,
                'sequence_number': len(st.session_state.experiment_data) + 1,
                'voltage': current_voltage,
                'current': leakage_current / 1000,  # 转换为A
                'power': current_voltage * leakage_current / 1000,
                'timestamp': current_time,
                'device_address': 1,
                'device_type': 'PVRSD'
            }
            
            st.session_state.experiment_data.append(data_point)
            
            # 每10个数据点保存一次
            if len(st.session_state.experiment_data) % 10 == 0:
                supabase.insert_experiment_data(st.session_state.experiment_data[-10:])
            
            # 显示当前状态
            st.markdown(f"""
            ### 实验状态: <span class="status-indicator status-running"></span>{phase}
            """, unsafe_allow_html=True)
            
            # 进度条
            if phase == "升压阶段":
                progress = elapsed_time / ramp_time
            elif phase == "保持阶段":
                progress = (elapsed_time - ramp_time) / test_duration
            else:
                progress = 1.0
            
            st.progress(progress)
            
            # 实时数据图表
            if len(st.session_state.experiment_data) > 1:
                df = pd.DataFrame(st.session_state.experiment_data)
                
                # 电压和漏电流曲线
                fig = Visualization.create_multi_axis_chart(
                    df,
                    x_col='timestamp',
                    y1_cols=['voltage'],
                    y2_cols=['current'],
                    title="耐压实验实时曲线"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 每秒刷新
            time.sleep(1)
            st.rerun()
    
    with col2:
        # 实时指标
        st.subheader("📊 实时指标")
        
        if st.session_state.experiment_running and st.session_state.experiment_data:
            current_data = st.session_state.experiment_data[-1]
            
            # 当前电压
            voltage_gauge = Visualization.create_gauge_chart(
                value=current_data['voltage'],
                title="测试电压",
                min_val=0,
                max_val=test_voltage * 1.2,
                threshold=test_voltage,
                unit="V"
            )
            st.plotly_chart(voltage_gauge, use_container_width=True)
            
            # 漏电流
            leakage_gauge = Visualization.create_gauge_chart(
                value=current_data['current'] * 1000,
                title="漏电流",
                min_val=0,
                max_val=leakage_limit * 1.2,
                threshold=leakage_limit,
                unit="mA"
            )
            st.plotly_chart(leakage_gauge, use_container_width=True)
            
            # 测试结果
            if current_data['current'] * 1000 > leakage_limit:
                st.error("⚠️ 漏电流超限!")
                result = "fail"
            else:
                st.success("✅ 测试正常")
                result = "pass"
            
            # 更新实验结果
            if phase == "完成":
                supabase.client.table("experiments").update({
                    "result": result
                }).eq("id", st.session_state.experiment_id).execute()
        else:
            st.info("等待实验开始...")
    
    # 历史记录
    st.markdown("---")
    st.subheader("📋 历史实验记录")
    
    # 获取历史实验
    history = supabase.client.table("experiments")\
        .select("*, devices(device_serial, device_model)")\
        .eq("experiment_type", "dielectric")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    if history.data:
        history_df = pd.DataFrame(history.data)
        
        # 格式化显示
        display_df = pd.DataFrame({
            '实验名称': history_df['experiment_name'],
            '设备': [d.get('devices', {}).get('device_serial', '') if d.get('devices') else '' for d in history.data],
            '状态': history_df['status'],
            '结果': history_df['result'],
            '开始时间': pd.to_datetime(history_df['start_time']).dt.strftime('%Y-%m-%d %H:%M'),
            '操作': history_df['id']
        })
        
        # 显示表格
        for idx, row in display_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 2, 1])
            
            with col1:
                st.text(row['实验名称'])
            with col2:
                st.text(row['设备'])
            with col3:
                status_color = {
                    'running': '🟡',
                    'completed': '🟢',
                    'cancelled': '🔴'
                }.get(row['状态'], '⚫')
                st.text(f"{status_color} {row['状态']}")
            with col4:
                result_color = {
                    'pass': '✅',
                    'fail': '❌',
                    'pending': '⏳'
                }.get(row['结果'], '❓')
                st.text(f"{result_color} {row['结果'] or '未判定'}")
            with col5:
                st.text(row['开始时间'])
            with col6:
                if st.button("查看", key=f"view_{row['操作']}"):
                    st.session_state.selected_experiment = row['操作']
                    st.switch_page("pages/1_🖥️_数据大屏.py")
    else:
        st.info("暂无历史记录")

if __name__ == "__main__":
    main()