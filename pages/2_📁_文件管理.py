"""
数据文件管理页面
支持文件上传、下载、预览和管理
"""

import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from utils.supabase_client import get_supabase_client
from utils.file_handler import FileHandler
from utils.data_processor import DataProcessor
import json

# 页面配置
st.set_page_config(
    page_title="文件管理 - 光伏关断器检测系统",
    page_icon="📁",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .file-upload-area {
        border: 2px dashed #3e3e3e;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #1e1e1e;
        transition: all 0.3s ease;
    }
    .file-upload-area:hover {
        border-color: #1a237e;
        background-color: #252525;
    }
    .file-card {
        background-color: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .file-card:hover {
        background-color: #252525;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 获取Supabase客户端
    supabase = st.session_state.supabase
    
    # 页面标题
    st.title("📁 数据文件管理")
    st.markdown("管理实验数据文件，支持Excel、CSV格式的上传、下载和预览")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📤 文件上传", "📥 文件下载", "📊 数据预览", "🗂️ 文件管理"])
    
    with tab1:
        st.subheader("上传实验数据文件")
        
        # 文件上传区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "选择文件上传",
                type=['xlsx', 'xls', 'csv'],
                accept_multiple_files=True,
                help="支持Excel和CSV格式，可同时上传多个文件"
            )
            
            if uploaded_files:
                st.info(f"已选择 {len(uploaded_files)} 个文件")
                
                # 关联到实验
                experiments = supabase.get_experiments(limit=50)
                exp_options = {"新建实验": None}
                if experiments:
                    exp_options.update({
                        f"{exp['experiment_name']} ({exp['id'][:8]})": exp['id'] 
                        for exp in experiments
                    })
                
                selected_exp_option = st.selectbox(
                    "关联到实验",
                    options=list(exp_options.keys())
                )
                
                # 如果选择新建实验
                if selected_exp_option == "新建实验":
                    exp_name = st.text_input("实验名称", value=f"数据导入_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    exp_type = st.selectbox("实验类型", ["normal", "dielectric", "leakage", "abnormal"])
                
                # 上传按钮
                if st.button("开始上传", type="primary", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 创建新实验（如果需要）
                    if selected_exp_option == "新建实验":
                        exp_data = {
                            "experiment_name": exp_name,
                            "experiment_type": exp_type,
                            "operator_id": st.session_state.user.get("id", "guest")
                        }
                        new_exp = supabase.insert_experiment(exp_data)
                        if new_exp:
                            experiment_id = new_exp['id']
                            if "exp_" in experiment_id:
                                st.success(f"创建新实验: {exp_name}（离线模式）")
                            else:
                                st.success(f"创建新实验: {exp_name}")
                        else:
                            # 如果创建失败，使用临时ID继续处理
                            experiment_id = f"temp_exp_{int(time.time())}"
                            st.warning(f"实验创建失败，使用临时ID继续处理: {exp_name}")
                    else:
                        experiment_id = exp_options[selected_exp_option]
                    
                    # 处理每个文件
                    success_count = 0
                    for i, file in enumerate(uploaded_files):
                        try:
                            status_text.text(f"处理文件: {file.name}")
                            
                            # 验证文件
                            is_valid, error_msg = FileHandler.validate_file(file)
                            if not is_valid:
                                st.error(f"{file.name}: {error_msg}")
                                continue
                            
                            # 读取数据
                            if file.name.endswith('.csv'):
                                df = FileHandler.read_csv_file(file)
                            else:
                                df = FileHandler.read_excel_file(file)
                            
                            # 验证数据格式
                            is_valid, errors = DataProcessor.validate_experiment_data(df)
                            if not is_valid:
                                st.error(f"{file.name} 数据验证失败:")
                                for error in errors:
                                    st.error(f"  • {error}")
                                continue
                            
                            # 准备数据
                            data_records = DataProcessor.prepare_for_database(df, experiment_id)
                            
                            # 批量插入数据
                            if supabase.insert_experiment_data(data_records):
                                # 上传文件到存储
                                file_path = f"experiments/{experiment_id}/{file.name}"
                                file_url = supabase.upload_file(file_path, file.getvalue())
                                
                                # 记录文件信息
                                file_record = {
                                    "file_name": file.name,
                                    "file_path": file_path,
                                    "file_size": file.size,
                                    "file_type": file.name.split('.')[-1],
                                    "experiment_id": experiment_id,
                                    "uploaded_by": st.session_state.user.get("id", "guest")
                                }
                                try:
                                    supabase.client.table("files").insert(file_record).execute()
                                    st.success(f"✅ {file.name} 上传成功并保存到数据库")
                                except Exception as db_error:
                                    # 如果数据库表不存在，仍然显示成功，但提示离线模式
                                    if "does not exist" in str(db_error) or "404" in str(db_error):
                                        st.success(f"✅ {file.name} 上传成功（离线模式）")
                                    else:
                                        st.warning(f"⚠️ {file.name} 上传成功，但数据库保存失败: {str(db_error)}")
                                
                                success_count += 1
                            else:
                                st.error(f"❌ {file.name} 数据插入失败")
                            
                        except Exception as e:
                            st.error(f"{file.name} 处理失败: {str(e)}")
                        
                        # 更新进度
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # 记录操作日志
                    supabase.log_operation(
                        "file_upload",
                        f"上传了 {success_count}/{len(uploaded_files)} 个文件到实验 {experiment_id[:8]}"
                    )
                    
                    st.success(f"上传完成！成功处理 {success_count}/{len(uploaded_files)} 个文件")
        
        with col2:
            st.info("""
            **上传说明**
            - 支持 Excel (.xlsx, .xls) 和 CSV 格式
            - 文件大小限制: 50MB
            - 可批量上传多个文件
            - 数据格式要求:
              - 必需列: 电流、电压、功率
              - 可选列: 时间戳、设备地址、设备类型
            """)
            
            # 显示示例数据格式
            with st.expander("查看数据格式示例"):
                sample_data = pd.DataFrame({
                    '序号': [1, 2, 3],
                    '电流': [0.11, 0.26, 0.44],
                    '电压': [20.36, 20.68, 20.22],
                    '功率': [2.24, 5.38, 8.90],
                    '时间戳': ['2025/5/2', '2025/5/2', '2025/5/2'],
                    '设备地址': [1, 1, 1],
                    '设备类型': ['未知', '未知', '未知']
                })
                st.dataframe(sample_data, use_container_width=True)
    
    with tab2:
        st.subheader("下载实验数据")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 选择实验
            experiments = supabase.get_experiments(limit=50)
            if experiments:
                exp_options = {
                    f"{exp['experiment_name']} ({exp['id'][:8]})": exp['id'] 
                    for exp in experiments
                }
                selected_exp = st.selectbox(
                    "选择实验",
                    options=list(exp_options.keys()),
                    key="download_exp"
                )
                experiment_id = exp_options[selected_exp]
                
                # 获取实验数据
                exp_data = supabase.get_experiment_data(experiment_id, limit=10000)
                
                if exp_data:
                    df = pd.DataFrame(exp_data)
                    
                    # 数据预览
                    st.info(f"共 {len(df)} 条数据")
                    st.dataframe(df.head(100), use_container_width=True)
                    
                    # 下载选项
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # 下载为Excel
                        excel_data = FileHandler.export_to_excel({
                            "实验数据": df,
                            "统计信息": pd.DataFrame([DataProcessor.calculate_statistics(df)])
                        })
                        FileHandler.create_download_link(
                            excel_data,
                            f"{selected_exp.split('(')[0].strip()}_数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "📥 下载Excel"
                        )
                    
                    with col2:
                        # 下载为CSV
                        csv_data = FileHandler.export_to_csv(df)
                        FileHandler.create_download_link(
                            csv_data,
                            f"{selected_exp.split('(')[0].strip()}_数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv",
                            "📥 下载CSV"
                        )
                    
                    with col3:
                        # 下载为JSON
                        json_data = FileHandler.export_to_json(df.to_dict(orient='records'))
                        FileHandler.create_download_link(
                            json_data,
                            f"{selected_exp.split('(')[0].strip()}_数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json",
                            "📥 下载JSON"
                        )
                else:
                    st.warning("该实验暂无数据")
            else:
                st.info("暂无实验记录")
        
        with col2:
            st.info("""
            **下载说明**
            - 支持导出为 Excel、CSV、JSON 格式
            - Excel 文件包含数据和统计信息两个工作表
            - 大数据量建议使用 CSV 格式
            """)
    
    with tab3:
        st.subheader("数据预览与分析")
        
        # 从data文件夹读取示例文件
        data_files = []
        if os.path.exists("data"):
            data_files = [f for f in os.listdir("data") if f.endswith(('.xlsx', '.xls', '.csv'))]
        
        if data_files:
            selected_file = st.selectbox(
                "选择示例数据文件",
                options=data_files
            )
            
            if st.button("加载文件", key="preview_load"):
                try:
                    file_path = os.path.join("data", selected_file)
                    
                    # 读取数据
                    if selected_file.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = DataProcessor.process_excel_data(file_path)
                    
                    # 显示文件信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("文件名", selected_file)
                    with col2:
                        st.metric("数据行数", f"{len(df):,}")
                    with col3:
                        file_size = os.path.getsize(file_path) / 1024 / 1024
                        st.metric("文件大小", f"{file_size:.2f} MB")
                    
                    # 数据预览
                    FileHandler.preview_dataframe(df)
                    
                    # 数据验证
                    with st.expander("数据验证结果"):
                        is_valid, errors = DataProcessor.validate_experiment_data(df)
                        if is_valid:
                            st.success("✅ 数据格式验证通过")
                        else:
                            st.error("❌ 数据格式验证失败:")
                            for error in errors:
                                st.error(f"  • {error}")
                    
                    # 数据统计
                    with st.expander("数据统计分析"):
                        stats = DataProcessor.calculate_statistics(df)
                        
                        # 显示统计信息
                        stats_cols = st.columns(3)
                        for i, (key, value) in enumerate(stats.items()):
                            with stats_cols[i % 3]:
                                st.metric(key, f"{value:.2f}")
                    
                except Exception as e:
                    st.error(f"读取文件失败: {str(e)}")
        else:
            st.info("data文件夹中没有找到示例文件")
    
    with tab4:
        st.subheader("文件管理")
        
        # 需要管理员或工程师权限
        if st.session_state.user_profile.get('role') not in ['admin', 'engineer']:
            st.warning("您没有权限管理文件")
            return
        
        # 获取所有文件记录（游客模式简化查询）
        try:
            files = supabase.client.table("files").select("*").order("created_at", desc=True).execute()
        except Exception as e:
            st.warning(f"无法获取文件记录: {e}")
            files = type('obj', (object,), {'data': []})()
        
        if files.data:
            # 搜索和筛选
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("搜索文件名", "")
            
            with col2:
                file_types = list(set(f['file_type'] for f in files.data))
                selected_type = st.selectbox("文件类型", ["全部"] + file_types)
            
            with col3:
                sort_by = st.selectbox("排序方式", ["上传时间", "文件名", "文件大小"])
            
            # 筛选文件
            filtered_files = files.data
            if search_term:
                filtered_files = [f for f in filtered_files if search_term.lower() in f['file_name'].lower()]
            if selected_type != "全部":
                filtered_files = [f for f in filtered_files if f['file_type'] == selected_type]
            
            # 排序
            if sort_by == "文件名":
                filtered_files.sort(key=lambda x: x['file_name'])
            elif sort_by == "文件大小":
                filtered_files.sort(key=lambda x: x['file_size'], reverse=True)
            
            st.info(f"共找到 {len(filtered_files)} 个文件")
            
            # 显示文件列表
            for file in filtered_files:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"📄 **{file['file_name']}**")
                        exp_name = file.get('experiments', {}).get('experiment_name', '未知')
                        st.caption(f"实验: {exp_name}")
                    
                    with col2:
                        upload_time = datetime.fromisoformat(file['upload_time'].replace('Z', '+00:00'))
                        st.caption(f"上传时间: {upload_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        file_size_mb = file['file_size'] / 1024 / 1024
                        st.caption(f"{file_size_mb:.2f} MB")
                    
                    with col4:
                        # 下载按钮
                        if st.button("下载", key=f"download_{file['id']}"):
                            try:
                                file_bytes = supabase.download_file(file['file_path'])
                                if file_bytes:
                                    st.download_button(
                                        label="💾",
                                        data=file_bytes,
                                        file_name=file['file_name'],
                                        key=f"dl_btn_{file['id']}"
                                    )
                            except Exception as e:
                                st.error(f"下载失败: {str(e)}")
                    
                    with col5:
                        # 删除按钮（仅管理员）
                        if st.session_state.user_profile.get('role') == 'admin':
                            if st.button("🗑️", key=f"delete_{file['id']}", help="删除文件"):
                                if st.checkbox(f"确认删除 {file['file_name']}", key=f"confirm_{file['id']}"):
                                    try:
                                        # 从存储中删除
                                        supabase.delete_file(file['file_path'])
                                        # 从数据库中删除记录
                                        supabase.client.table("files").delete().eq("id", file['id']).execute()
                                        st.success("文件已删除")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"删除失败: {str(e)}")
                    
                    st.markdown("---")
        else:
            st.info("暂无文件记录")

if __name__ == "__main__":
    main()