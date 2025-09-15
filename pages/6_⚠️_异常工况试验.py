"""
异常工况试验页面
按照GB/T 37408标准进行异常条件测试
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from utils.supabase_client import get_supabase_client
from utils.visualization import Visualization
from utils.data_processor import DataProcessor

# 页面配置
st.set_page_config(
    page_title="异常工况试验 - 光伏关断器检测系统",
    page_icon="⚠️",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .experiment-header {
        background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .fault-card {
        background-color: #1e1e1e;
        border: 2px solid #d32f2f;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }
    .fault-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background-color: #d32f2f;
    }
    .fault-card.active {
        border-color: #ff6f00;
        animation: pulse-border 2s infinite;
    }
    @keyframes pulse-border {
        0% { border-color: #ff6f00; }
        50% { border-color: #ff9800; }
        100% { border-color: #ff6f00; }
    }
    .protection-status {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.5rem;
    }
    .protection-triggered {
        background-color: #00c853;
        color: white;
    }
    .protection-failed {
        background-color: #d32f2f;
        color: white;
    }
    .fault-indicator {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        vertical-align: middle;
    }
    .fault-active {
        background-color: #ff6f00;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)

# 异常测试项目定义
FAULT_TESTS = {
    "overload": {
        "name": "过载测试",
        "description": "测试不同过载水平下的保护功能",
        "levels": [
            {"name": "110%额定电流", "factor": 1.1, "duration": 60, "should_trip": False},
            {"name": "150%额定电流", "factor": 1.5, "duration": 30, "should_trip": True},
            {"name": "200%额定电流", "factor": 2.0, "duration": 10, "should_trip": True}
        ]
    },
    "short_circuit": {
        "name": "短路测试",
        "description": "测试输出短路和输入短路保护",
        "types": [
            {"name": "输出短路", "location": "output", "response_time": 0.1},
            {"name": "输入短路", "location": "input", "response_time": 0.05},
            {"name": "接地故障", "location": "ground", "response_time": 0.2}
        ]
    },
    "temperature": {
        "name": "温度异常测试",
        "description": "测试高低温环境下的运行和保护",
        "conditions": [
            {"name": "低温启动", "temp": -40, "test": "startup"},
            {"name": "高温运行", "temp": 85, "test": "operation"},
            {"name": "温度循环", "temp_range": [-40, 85], "cycles": 10}
        ]
    },
    "voltage": {
        "name": "电压异常测试",
        "description": "测试过压、欠压和电压波动",
        "conditions": [
            {"name": "过压保护", "voltage": 1.2, "should_protect": True},
            {"name": "欠压保护", "voltage": 0.8, "should_protect": True},
            {"name": "电压骤变", "voltage_change": 0.3, "response_time": 1.0}
        ]
    }
}

def main():
    # 获取Supabase客户端
    supabase = st.session_state.supabase
    
    # 页面标题
    st.markdown("""
    <div class="experiment-header">
        <h1 style="color: white; margin: 0;">⚠️ 异常工况试验（Abnormal Condition Test）</h1>
        <p style="color: #ffebee; margin: 0;">参考标准: GB/T 37408 | 测试保护功能和故障响应</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'abnormal_test_running' not in st.session_state:
        st.session_state.abnormal_test_running = False
    if 'current_fault_test' not in st.session_state:
        st.session_state.current_fault_test = None
    if 'fault_test_results' not in st.session_state:
        st.session_state.fault_test_results = {}
    if 'protection_triggered' not in st.session_state:
        st.session_state.protection_triggered = False
    
    # 侧边栏 - 测试配置
    with st.sidebar:
        st.subheader("🔧 测试配置")
        
        # 获取测试标准
        standards = supabase.get_test_standards('abnormal')
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
            
            # 获取设备参数
            device = next(d for d in devices if d['id'] == device_id)
            rated_current = device.get('rated_current', 10)
            rated_voltage = device.get('rated_voltage', 1000)
            rated_power = device.get('rated_power', 10000)
        else:
            st.warning("请先添加设备")
            device_id = None
            rated_current = 10
            rated_voltage = 1000
            rated_power = 10000
        
        st.markdown("---")
        
        # 故障测试选择
        st.markdown("### 🚨 故障测试项目")
        selected_fault_tests = []
        for test_id, test_info in FAULT_TESTS.items():
            if st.checkbox(test_info['name'], value=True, key=f"fault_{test_id}"):
                selected_fault_tests.append((test_id, test_info))
        
        # 安全设置
        st.markdown("### ⚡ 安全设置")
        emergency_stop_enabled = st.checkbox("启用紧急停止", value=True)
        auto_recovery = st.checkbox("故障清除后自动恢复", value=False)
        
        # 实验信息
        experiment_name = st.text_input(
            "实验名称",
            value=f"异常工况试验_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
    
    # 主要内容区域
    if not st.session_state.abnormal_test_running:
        # 测试前检查和说明
        st.subheader("⚠️ 测试前安全检查")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 安全注意事项
            - ⚡ 测试将产生异常电流和电压
            - 🔥 可能产生高温，请确保通风良好
            - 👷 操作人员必须穿戴防护装备
            - 🚨 确保紧急停止按钮可用
            - 📏 保持安全距离
            """)
        
        with col2:
            st.markdown("""
            ### 测试前检查清单
            - ✅ 设备接地良好
            - ✅ 测试区域已隔离
            - ✅ 消防设备就位
            - ✅ 数据记录系统正常
            - ✅ 通信系统正常
            """)
        
        st.warning("⚠️ 警告：异常工况测试具有一定危险性，请确保所有安全措施到位！")
        
        # 显示选中的测试项目
        if selected_fault_tests:
            st.markdown("---")
            st.subheader("📋 待测试项目")
            
            for test_id, test_info in selected_fault_tests:
                st.markdown(f"""
                <div class="fault-card">
                    <h4>🚨 {test_info['name']}</h4>
                    <p>{test_info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 确认开始测试
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("⚠️ 确认开始异常测试", type="primary", use_container_width=True):
                    if device_id:
                        # 创建实验记录
                        exp_data = {
                            "experiment_name": experiment_name,
                            "experiment_type": "abnormal",
                            "device_id": device_id,
                            "operator_id": st.session_state.user.get("id", "guest"),
                            "notes": f"异常测试: {', '.join([t[1]['name'] for t in selected_fault_tests])}"
                        }
                        experiment = supabase.insert_experiment(exp_data)
                        
                        if experiment:
                            st.session_state.abnormal_experiment_id = experiment['id']
                            st.session_state.abnormal_test_running = True
                            st.session_state.fault_test_queue = selected_fault_tests
                            st.session_state.current_fault_index = 0
                            st.session_state.current_fault_test = selected_fault_tests[0]
                            st.session_state.fault_start_time = time.time()
                            st.session_state.current_sub_test = 0
                            st.success("异常工况测试已开始")
                            st.rerun()
                    else:
                        st.error("请选择测试设备")
        else:
            st.info("请在侧边栏选择至少一个故障测试项目")
    
    else:
        # 测试进行中
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 紧急停止按钮
            if emergency_stop_enabled:
                if st.button("🛑 紧急停止", type="secondary", use_container_width=True):
                    st.session_state.abnormal_test_running = False
                    st.session_state.protection_triggered = True
                    st.error("紧急停止已触发！")
                    
                    # 更新实验状态
                    supabase.client.table("experiments").update({
                        "status": "cancelled",
                        "result": "emergency_stop",
                        "end_time": datetime.now().isoformat()
                    }).eq("id", st.session_state.abnormal_experiment_id).execute()
                    
                    time.sleep(2)
                    st.rerun()
            
            # 当前测试信息
            current_test_id, current_test_info = st.session_state.current_fault_test
            st.markdown(f"### 🚨 当前测试: {current_test_info['name']}")
            
            # 根据不同的故障类型执行测试
            if current_test_id == "overload":
                # 过载测试
                levels = current_test_info['levels']
                current_level = levels[st.session_state.current_sub_test]
                
                st.markdown(f"""
                <div class="fault-card active">
                    <span class="fault-indicator fault-active"></span>
                    <b>测试条件:</b> {current_level['name']}<br>
                    <b>测试电流:</b> {rated_current * current_level['factor']:.1f} A<br>
                    <b>持续时间:</b> {current_level['duration']} 秒<br>
                    <b>预期结果:</b> {'应触发保护' if current_level['should_trip'] else '正常运行'}
                </div>
                """, unsafe_allow_html=True)
                
                # 模拟过载数据
                elapsed = time.time() - st.session_state.fault_start_time
                test_current = rated_current * current_level['factor'] + np.random.normal(0, rated_current * 0.05)
                test_voltage = rated_voltage * (1 - 0.05 * (current_level['factor'] - 1))  # 电压随负载略降
                test_power = test_current * test_voltage
                
                # 显示实时数据
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    current_gauge = Visualization.create_gauge_chart(
                        value=test_current,
                        title="测试电流",
                        min_val=0,
                        max_val=rated_current * 2.5,
                        threshold=rated_current * 1.2,
                        unit="A"
                    )
                    st.plotly_chart(current_gauge, use_container_width=True)
                
                with col_m2:
                    st.metric("测试电压", f"{test_voltage:.1f} V", f"{test_voltage - rated_voltage:.1f} V")
                    st.metric("测试功率", f"{test_power:.1f} W", f"{test_power - rated_power:.1f} W")
                
                with col_m3:
                    st.metric("已运行时间", f"{elapsed:.1f} 秒")
                    remaining = current_level['duration'] - elapsed
                    st.metric("剩余时间", f"{max(0, remaining):.1f} 秒")
                
                # 判断保护是否触发
                if current_level['should_trip'] and elapsed > current_level['duration'] * 0.3:
                    if np.random.random() < 0.95:  # 95%概率正确触发
                        st.session_state.protection_triggered = True
                        st.success("✅ 保护已正确触发!")
                        result = "passed"
                    else:
                        st.error("❌ 保护未触发!")
                        result = "failed"
                    
                    # 保存结果
                    if current_test_id not in st.session_state.fault_test_results:
                        st.session_state.fault_test_results[current_test_id] = {}
                    st.session_state.fault_test_results[current_test_id][current_level['name']] = result
                
                # 检查是否完成当前级别
                if elapsed >= current_level['duration'] or st.session_state.protection_triggered:
                    st.session_state.current_sub_test += 1
                    st.session_state.fault_start_time = time.time()
                    st.session_state.protection_triggered = False
                    
                    if st.session_state.current_sub_test >= len(levels):
                        # 当前测试完成，移到下一个
                        st.session_state.current_fault_index += 1
                        st.session_state.current_sub_test = 0
                        
                        if st.session_state.current_fault_index < len(st.session_state.fault_test_queue):
                            st.session_state.current_fault_test = st.session_state.fault_test_queue[st.session_state.current_fault_index]
                        else:
                            # 所有测试完成
                            st.session_state.abnormal_test_running = False
                            st.balloons()
                    
                    time.sleep(2)  # 恢复时间
                    st.rerun()
            
            elif current_test_id == "short_circuit":
                # 短路测试
                types = current_test_info['types']
                current_type = types[st.session_state.current_sub_test]
                
                st.markdown(f"""
                <div class="fault-card active">
                    <span class="fault-indicator fault-active"></span>
                    <b>故障类型:</b> {current_type['name']}<br>
                    <b>故障位置:</b> {current_type['location']}<br>
                    <b>预期响应时间:</b> < {current_type['response_time']} 秒
                </div>
                """, unsafe_allow_html=True)
                
                # 模拟短路测试
                elapsed = time.time() - st.session_state.fault_start_time
                
                if elapsed < 2:
                    st.info("准备注入故障...")
                elif elapsed < 2 + current_type['response_time']:
                    st.warning(f"⚡ {current_type['name']}故障已注入!")
                    
                    # 显示故障电流
                    fault_current = rated_current * np.random.uniform(10, 20)  # 短路电流为额定的10-20倍
                    st.metric("故障电流", f"{fault_current:.0f} A", f"+{fault_current - rated_current:.0f} A")
                else:
                    response_time = current_type['response_time'] * np.random.uniform(0.5, 0.9)
                    st.success(f"✅ 保护在 {response_time:.3f} 秒内触发")
                    
                    # 保存结果
                    if current_test_id not in st.session_state.fault_test_results:
                        st.session_state.fault_test_results[current_test_id] = {}
                    st.session_state.fault_test_results[current_test_id][current_type['name']] = f"响应时间: {response_time:.3f}s"
                    
                    # 移到下一个测试
                    st.session_state.current_sub_test += 1
                    st.session_state.fault_start_time = time.time()
                    
                    if st.session_state.current_sub_test >= len(types):
                        st.session_state.current_fault_index += 1
                        st.session_state.current_sub_test = 0
                        
                        if st.session_state.current_fault_index < len(st.session_state.fault_test_queue):
                            st.session_state.current_fault_test = st.session_state.fault_test_queue[st.session_state.current_fault_index]
                        else:
                            st.session_state.abnormal_test_running = False
                    
                    time.sleep(3)
                    st.rerun()
            
            # 其他故障类型的测试逻辑可以类似实现
            
            # 自动刷新
            if st.session_state.abnormal_test_running:
                time.sleep(0.5)
                st.rerun()
        
        with col2:
            # 测试状态面板
            st.subheader("🔍 测试状态")
            
            # 保护状态指示
            if st.session_state.protection_triggered:
                st.markdown('<div class="protection-status protection-triggered">保护已触发</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="protection-status" style="background-color: #424242;">正常运行</div>', unsafe_allow_html=True)
            
            # 测试进度
            st.markdown("### 📊 测试进度")
            completed = st.session_state.current_fault_index
            total = len(st.session_state.fault_test_queue)
            st.progress(completed / total if total > 0 else 0)
            st.text(f"{completed}/{total} 项完成")
            
            # 已完成的测试结果
            if st.session_state.fault_test_results:
                st.markdown("### ✅ 已完成测试")
                for test_id, results in st.session_state.fault_test_results.items():
                    test_name = FAULT_TESTS[test_id]['name']
                    st.markdown(f"**{test_name}**")
                    for sub_test, result in results.items():
                        if isinstance(result, str) and result in ['passed', 'failed']:
                            icon = "✅" if result == "passed" else "❌"
                            st.text(f"  {icon} {sub_test}")
                        else:
                            st.text(f"  📊 {sub_test}: {result}")
    
    # 测试完成后的结果展示
    if not st.session_state.abnormal_test_running and st.session_state.fault_test_results:
        st.markdown("---")
        st.subheader("📋 测试结果汇总")
        
        # 判定总体结果
        all_passed = True
        for test_results in st.session_state.fault_test_results.values():
            for result in test_results.values():
                if isinstance(result, str) and result == 'failed':
                    all_passed = False
                    break
        
        if all_passed:
            st.success("🎉 所有异常保护功能测试通过!")
            final_result = "pass"
        else:
            st.error("❌ 部分保护功能测试未通过，请检查设备")
            final_result = "fail"
        
        # 更新实验结果
        if 'abnormal_experiment_id' in st.session_state:
            supabase.client.table("experiments").update({
                "status": "completed",
                "result": final_result,
                "end_time": datetime.now().isoformat()
            }).eq("id", st.session_state.abnormal_experiment_id).execute()
        
        # 生成测试报告
        with st.expander("📄 查看详细测试报告"):
            for test_id, results in st.session_state.fault_test_results.items():
                test_info = FAULT_TESTS[test_id]
                st.markdown(f"### {test_info['name']}")
                st.markdown(f"_{test_info['description']}_")
                
                # 创建结果表格
                results_list = []
                for sub_test, result in results.items():
                    results_list.append({
                        '测试项': sub_test,
                        '结果': result
                    })
                
                df_results = pd.DataFrame(results_list)
                st.dataframe(df_results, use_container_width=True, hide_index=True)
                st.markdown("---")
        
        # 清理按钮
        if st.button("🔄 开始新的异常测试"):
            st.session_state.fault_test_results = {}
            st.session_state.protection_triggered = False
            st.rerun()

if __name__ == "__main__":
    main()