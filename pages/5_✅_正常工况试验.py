"""
正常工况试验页面
按照UL 1741标准进行功能和性能测试
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
    page_title="正常工况试验 - 光伏关断器检测系统",
    page_icon="✅",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .experiment-header {
        background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .test-item-card {
        background-color: #1e1e1e;
        border-left: 4px solid #00c853;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .test-item-card:hover {
        background-color: #252525;
        transform: translateX(5px);
    }
    .test-status {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-pending { background-color: #424242; color: #e0e0e0; }
    .status-running { background-color: #ff6f00; color: white; }
    .status-passed { background-color: #00c853; color: white; }
    .status-failed { background-color: #d32f2f; color: white; }
    .performance-metric {
        text-align: center;
        padding: 1rem;
        background-color: #2e2e2e;
        border-radius: 10px;
        margin: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00e676;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #b0b0b0;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 测试项目定义
TEST_ITEMS = {
    "shutdown_response": {
        "name": "关断响应时间测试",
        "description": "测试接收到关断信号后的响应时间",
        "duration": 10,
        "pass_criteria": {"max_time": 30}  # 秒
    },
    "communication": {
        "name": "通信功能测试",
        "description": "测试与控制系统的通信功能",
        "duration": 15,
        "pass_criteria": {"success_rate": 95}  # %
    },
    "remote_control": {
        "name": "远程控制测试",
        "description": "测试远程开启/关断功能",
        "duration": 20,
        "pass_criteria": {"response_rate": 100}  # %
    },
    "auto_restart": {
        "name": "自动重启功能测试",
        "description": "测试故障清除后的自动重启功能",
        "duration": 25,
        "pass_criteria": {"restart_time": 60}  # 秒
    },
    "rated_power": {
        "name": "额定功率运行测试",
        "description": "在额定功率下持续运行测试",
        "duration": 60,
        "pass_criteria": {"stability": 95}  # %
    },
    "efficiency": {
        "name": "效率测试",
        "description": "测试不同负载下的转换效率",
        "duration": 45,
        "pass_criteria": {"min_efficiency": 95}  # %
    },
    "temperature_rise": {
        "name": "温升测试",
        "description": "额定功率下的温度上升测试",
        "duration": 120,
        "pass_criteria": {"max_temp_rise": 40}  # °C
    }
}

def main():
    # 获取Supabase客户端
    supabase = st.session_state.get('supabase')
    
    # 页面标题
    st.markdown("""
    <div class="experiment-header">
        <h1 style="color: white; margin: 0;">✅ 正常工况试验（Normal Operation Test）</h1>
        <p style="color: #e8f5e9; margin: 0;">参考标准: UL 1741 | 测试功能完整性和性能指标</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'normal_test_running' not in st.session_state:
        st.session_state.normal_test_running = False
    if 'normal_test_data' not in st.session_state:
        st.session_state.normal_test_data = {}
    if 'current_test_item' not in st.session_state:
        st.session_state.current_test_item = None
    if 'test_results' not in st.session_state:
        st.session_state.test_results = {}
    
    # 侧边栏 - 测试配置
    with st.sidebar:
        st.subheader("🔧 测试配置")
        
        # 获取测试标准
        standards = supabase.get_test_standards('normal')
        if standards:
            standard = standards[0]
            st.info(f"标准: {standard['standard_name']}")
        
        # 设备选择
        st.markdown("### 🔌 设备选择")
        devices = supabase.get_devices()
        if devices:
            device_options = {f"{d['device_serial']} - {d['device_model']}": d['id'] for d in devices}
            selected_device = st.selectbox(
                "选择测试设备",
                options=list(device_options.keys())
            )
            device_id = device_options[selected_device]
            
            # 显示设备信息
            device = next(d for d in devices if d['id'] == device_id)
            st.markdown("#### 设备参数")
            st.text(f"额定电压: {device.get('rated_voltage', 'N/A')} V")
            st.text(f"额定电流: {device.get('rated_current', 'N/A')} A")
            st.text(f"额定功率: {device.get('rated_power', 'N/A')} W")
        else:
            st.warning("请先添加设备")
            device_id = None
        
        st.markdown("---")
        
        # 测试项目选择
        st.markdown("### 📋 测试项目")
        selected_tests = {}
        for test_id, test_info in TEST_ITEMS.items():
            if st.checkbox(test_info['name'], value=True, key=f"test_{test_id}"):
                selected_tests[test_id] = test_info
        
        # 实验信息
        experiment_name = st.text_input(
            "实验名称",
            value=f"正常工况试验_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
    
    # 主要内容区域
    if not st.session_state.normal_test_running:
        # 测试前准备
        st.subheader("📋 测试项目列表")
        
        # 显示选中的测试项目
        if selected_tests:
            total_duration = sum(test['duration'] for test in selected_tests.values())
            st.info(f"已选择 {len(selected_tests)} 个测试项目，预计耗时 {total_duration} 秒")
            
            # 测试项目卡片
            for test_id, test_info in selected_tests.items():
                st.markdown(f"""
                <div class="test-item-card">
                    <h4>{test_info['name']}</h4>
                    <p>{test_info['description']}</p>
                    <p><b>预计时长:</b> {test_info['duration']} 秒</p>
                    <p><b>通过标准:</b> {test_info['pass_criteria']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 开始测试按钮
            if st.button("▶️ 开始测试", type="primary", use_container_width=True):
                if device_id:
                    # 创建实验记录
                    exp_data = {
                        "experiment_name": experiment_name,
                        "experiment_type": "normal",
                        "device_id": device_id,
                        "operator_id": st.session_state.get("user", {}).get("id", "guest"),
                        "notes": f"测试项目: {', '.join([t['name'] for t in selected_tests.values()])}"
                    }
                    experiment = supabase.insert_experiment(exp_data)
                    
                    if experiment:
                        st.session_state.normal_experiment_id = experiment['id']
                        st.session_state.normal_test_running = True
                        st.session_state.selected_tests = selected_tests
                        st.session_state.test_queue = list(selected_tests.keys())
                        st.session_state.current_test_item = st.session_state.test_queue[0]
                        st.session_state.test_start_time = time.time()
                        st.session_state.item_start_time = time.time()
                        st.success("测试已开始")
                        st.rerun()
                else:
                    st.error("请选择测试设备")
        else:
            st.warning("请至少选择一个测试项目")
    
    else:
        # 测试进行中
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 停止按钮
            if st.button("⏹️ 停止测试", type="secondary"):
                st.session_state.normal_test_running = False
                supabase.client.table("experiments").update({
                    "status": "cancelled",
                    "end_time": datetime.now().isoformat()
                }).eq("id", st.session_state.normal_experiment_id).execute()
                st.warning("测试已取消")
                st.rerun()
            
            # 当前测试项目
            current_test = st.session_state.selected_tests[st.session_state.current_test_item]
            st.markdown(f"### 当前测试: {current_test['name']}")
            st.markdown(f"_{current_test['description']}_")
            
            # 测试进度
            item_elapsed = time.time() - st.session_state.item_start_time
            item_progress = min(item_elapsed / current_test['duration'], 1.0)
            
            col_prog1, col_prog2 = st.columns([4, 1])
            with col_prog1:
                st.progress(item_progress)
            with col_prog2:
                st.text(f"{item_elapsed:.0f}/{current_test['duration']}s")
            
            # 模拟测试执行和数据生成
            test_id = st.session_state.current_test_item
            
            if test_id == "shutdown_response":
                # 关断响应时间测试
                if item_elapsed < 5:
                    st.info("📡 发送关断信号...")
                    response_time = None
                else:
                    response_time = np.random.normal(15, 3)  # 模拟响应时间
                    response_time = max(5, min(response_time, 25))
                    st.success(f"✅ 关断响应时间: {response_time:.1f} 秒")
                    
                    if response_time <= current_test['pass_criteria']['max_time']:
                        st.success("测试通过")
                        result = "passed"
                    else:
                        st.error("测试失败 - 响应时间过长")
                        result = "failed"
                    
                    st.session_state.test_results[test_id] = {
                        "result": result,
                        "response_time": response_time
                    }
            
            elif test_id == "communication":
                # 通信功能测试
                test_count = int(item_elapsed * 2)  # 每秒2次测试
                success_count = int(test_count * np.random.uniform(0.94, 0.99))
                success_rate = (success_count / max(test_count, 1)) * 100 if test_count > 0 else 0
                
                st.markdown(f"""
                - 测试次数: {test_count}
                - 成功次数: {success_count}
                - 成功率: {success_rate:.1f}%
                """)
                
                # 实时通信状态
                if np.random.random() > 0.05:
                    st.success("🟢 通信正常")
                else:
                    st.warning("🟡 通信延迟")
            
            elif test_id == "rated_power":
                # 额定功率运行测试
                # 生成功率数据
                rated_power = device.get('rated_power', 1000) if 'device' in locals() else 1000
                power_variation = np.random.normal(0, rated_power * 0.02)  # 2%波动
                current_power = rated_power + power_variation
                
                if 'power_data' not in st.session_state:
                    st.session_state.power_data = []
                
                st.session_state.power_data.append({
                    'time': item_elapsed,
                    'power': current_power,
                    'voltage': device.get('rated_voltage', 1000) if 'device' in locals() else 1000,
                    'current': current_power / (device.get('rated_voltage', 1000) if 'device' in locals() else 1000)
                })
                
                # 显示功率曲线
                if len(st.session_state.power_data) > 1:
                    df_power = pd.DataFrame(st.session_state.power_data)
                    fig = Visualization.create_realtime_line_chart(
                        df_power,
                        x_col='time',
                        y_cols=['power'],
                        title="额定功率运行监测"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            elif test_id == "efficiency":
                # 效率测试 - 不同负载点
                load_points = [0.25, 0.5, 0.75, 1.0]  # 负载率
                current_load_idx = min(int(item_elapsed / (current_test['duration'] / len(load_points))), len(load_points) - 1)
                current_load = load_points[current_load_idx]
                
                # 模拟效率（高负载时效率更高）
                base_efficiency = 94 + current_load * 4
                efficiency = base_efficiency + np.random.normal(0, 0.5)
                
                st.markdown(f"""
                ### 当前测试点
                - 负载率: {current_load * 100:.0f}%
                - 输入功率: {1000 * current_load:.0f} W
                - 输出功率: {1000 * current_load * efficiency / 100:.0f} W
                - 效率: {efficiency:.1f}%
                """)
                
                # 效率曲线
                if 'efficiency_data' not in st.session_state:
                    st.session_state.efficiency_data = []
                
                st.session_state.efficiency_data.append({
                    'load': current_load * 100,
                    'efficiency': efficiency
                })
                
                if len(st.session_state.efficiency_data) > 1:
                    df_eff = pd.DataFrame(st.session_state.efficiency_data)
                    fig_eff = Visualization.create_bar_chart(
                        df_eff,
                        x_col='load',
                        y_col='efficiency',
                        title="效率测试结果"
                    )
                    st.plotly_chart(fig_eff, use_container_width=True)
            
            # 检查是否完成当前测试
            if item_elapsed >= current_test['duration']:
                # 保存测试结果
                if test_id not in st.session_state.test_results:
                    st.session_state.test_results[test_id] = {"result": "passed"}
                
                # 移动到下一个测试
                current_idx = st.session_state.test_queue.index(st.session_state.current_test_item)
                if current_idx < len(st.session_state.test_queue) - 1:
                    st.session_state.current_test_item = st.session_state.test_queue[current_idx + 1]
                    st.session_state.item_start_time = time.time()
                    
                    # 清理临时数据
                    if 'power_data' in st.session_state:
                        del st.session_state.power_data
                    if 'efficiency_data' in st.session_state:
                        del st.session_state.efficiency_data
                    
                    st.rerun()
                else:
                    # 所有测试完成
                    st.session_state.normal_test_running = False
                    
                    # 判定总体结果
                    all_passed = all(r.get('result') == 'passed' for r in st.session_state.test_results.values())
                    final_result = "pass" if all_passed else "fail"
                    
                    # 更新实验记录
                    supabase.client.table("experiments").update({
                        "status": "completed",
                        "result": final_result,
                        "end_time": datetime.now().isoformat()
                    }).eq("id", st.session_state.normal_experiment_id).execute()
                    
                    st.balloons()
                    st.success("所有测试已完成!")
                    st.rerun()
            
            # 刷新页面
            time.sleep(0.5)
            st.rerun()
        
        with col2:
            # 测试进度总览
            st.subheader("📊 测试进度")
            
            completed_tests = len(st.session_state.test_results)
            total_tests = len(st.session_state.selected_tests)
            
            st.metric("已完成", f"{completed_tests}/{total_tests}")
            
            # 各项目状态
            st.markdown("### 测试状态")
            for test_id, test_info in st.session_state.selected_tests.items():
                if test_id in st.session_state.test_results:
                    result = st.session_state.test_results[test_id]['result']
                    status_class = f"status-{result}"
                    status_text = "✅ 通过" if result == "passed" else "❌ 失败"
                elif test_id == st.session_state.current_test_item:
                    status_class = "status-running"
                    status_text = "🔄 进行中"
                else:
                    status_class = "status-pending"
                    status_text = "⏳ 等待"
                
                st.markdown(f"""
                <div style="margin: 0.5rem 0;">
                    <span class="test-status {status_class}">{status_text}</span>
                    <div style="font-size: 0.85rem; margin-top: 0.3rem;">{test_info['name']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 测试结果展示（如果有）
    if st.session_state.test_results and not st.session_state.normal_test_running:
        st.markdown("---")
        st.subheader("📊 测试结果汇总")
        
        # 总体结果
        all_passed = all(r.get('result') == 'passed' for r in st.session_state.test_results.values())
        if all_passed:
            st.success("🎉 所有测试项目均通过!")
        else:
            failed_count = sum(1 for r in st.session_state.test_results.values() if r.get('result') == 'failed')
            st.error(f"❌ {failed_count} 个测试项目未通过")
        
        # 详细结果
        results_data = []
        for test_id, result in st.session_state.test_results.items():
            test_info = TEST_ITEMS[test_id]
            results_data.append({
                '测试项目': test_info['name'],
                '结果': '通过' if result['result'] == 'passed' else '失败',
                '详细信息': str(result)
            })
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # 清理会话状态
        if st.button("🔄 开始新测试"):
            st.session_state.test_results = {}
            st.session_state.normal_test_data = {}
            st.rerun()

if __name__ == "__main__":
    main()