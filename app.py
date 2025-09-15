"""
光伏关断器检测数据管理系统
主应用入口
"""

import streamlit as st
import os
from dotenv import load_dotenv
from utils.supabase_client import get_supabase_client
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="光伏关断器检测数据管理系统",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "光伏关断器检测数据管理系统 v1.0"
    }
)

# 自定义CSS样式
def load_css():
    st.markdown("""
    <style>
    /* 全局样式 */
    .stApp {
        background-color: #121212;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* 主要内容区域 */
    .main {
        padding: 2rem;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* 卡片样式 */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #2e2e2e;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: #1a237e;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #283593;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: #2e2e2e;
        border: 1px solid #3e3e3e;
        color: #ffffff;
    }
    
    /* 数据表格样式 */
    .dataframe {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* 警告和错误样式 */
    .stAlert {
        background-color: #2e2e2e;
        border: 1px solid #3e3e3e;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background-color: #ff6f00;
    }
    
    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2e2e2e;
        color: #b0b0b0;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1a237e;
        color: #ffffff;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e1e1e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3e3e3e;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4e4e4e;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化会话状态
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = None
    if 'supabase' not in st.session_state:
        st.session_state.supabase = get_supabase_client()

# 登录页面
def login_page():
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">⚡ 光伏关断器检测数据管理系统</h1>
        <p style="font-size: 1.2rem; color: #b0b0b0;">高端工业级实验数据管理平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("用户登录")
                email = st.text_input("邮箱", placeholder="请输入邮箱")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登录", use_container_width=True)
                
                if submitted:
                    if email and password:
                        result = st.session_state.supabase.sign_in(email, password)
                        if result['success']:
                            st.session_state.authenticated = True
                            st.session_state.user = result['user']
                            # 获取用户配置文件
                            profile = st.session_state.supabase.get_user_profile(result['user'].id)
                            st.session_state.user_profile = profile
                            st.success("登录成功！")
                            st.rerun()
                        else:
                            st.error(f"登录失败：{result['error']}")
                    else:
                        st.error("请填写所有字段")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("用户注册")
                full_name = st.text_input("姓名", placeholder="请输入姓名")
                email = st.text_input("邮箱", placeholder="请输入邮箱", key="reg_email")
                password = st.text_input("密码", type="password", placeholder="请输入密码（至少6位）", key="reg_password")
                password_confirm = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
                submitted = st.form_submit_button("注册", use_container_width=True)
                
                if submitted:
                    if all([full_name, email, password, password_confirm]):
                        if password != password_confirm:
                            st.error("两次输入的密码不一致")
                        elif len(password) < 6:
                            st.error("密码长度至少为6位")
                        else:
                            result = st.session_state.supabase.sign_up(email, password, full_name)
                            if result['success']:
                                st.success("注册成功！请登录")
                            else:
                                st.error(f"注册失败：{result['error']}")
                    else:
                        st.error("请填写所有字段")

# 主页面
def main_page():
    # 侧边栏
    with st.sidebar:
        st.markdown("### 🏭 光伏关断器检测系统")
        st.markdown("---")
        
        # 用户信息
        if st.session_state.user_profile:
            st.markdown(f"👤 **用户**: {st.session_state.user_profile.get('full_name', '未知')}")
            st.markdown(f"🔑 **角色**: {st.session_state.user_profile.get('role', 'viewer')}")
            st.markdown("---")
        
        # 导航菜单
        st.markdown("### 📊 功能模块")
        
        # 登出按钮
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.supabase.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.user_profile = None
            st.rerun()
    
    # 主页内容
    st.title("🏠 系统主页")
    
    # 系统概览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 今日实验数",
            value="12",
            delta="3"
        )
    
    with col2:
        st.metric(
            label="✅ 通过率",
            value="91.7%",
            delta="2.3%"
        )
    
    with col3:
        st.metric(
            label="🔧 活跃设备",
            value="8",
            delta="1"
        )
    
    with col4:
        st.metric(
            label="📁 数据文件",
            value="156",
            delta="12"
        )
    
    st.markdown("---")
    
    # 快速访问
    st.subheader("⚡ 快速访问")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🖥️ 数据大屏", use_container_width=True, help="查看实时数据监控大屏"):
            st.switch_page("pages/1_🖥️_数据大屏.py")
    
    with col2:
        if st.button("📁 文件管理", use_container_width=True, help="管理实验数据文件"):
            st.switch_page("pages/2_📁_文件管理.py")
    
    with col3:
        if st.button("🔬 开始实验", use_container_width=True, help="开始新的实验测试"):
            st.switch_page("pages/3_🔬_耐压实验.py")
    
    st.markdown("---")
    
    # 最近实验
    st.subheader("📋 最近实验记录")
    
    # 获取最近的实验记录
    experiments = st.session_state.supabase.get_experiments(limit=5)
    
    if experiments:
        # 创建表格数据
        exp_data = []
        for exp in experiments:
            exp_data.append({
                "实验名称": exp.get('experiment_name', ''),
                "类型": exp.get('experiment_type', ''),
                "状态": exp.get('status', ''),
                "结果": exp.get('result', ''),
                "开始时间": exp.get('start_time', ''),
                "设备": exp.get('devices', {}).get('device_serial', '') if exp.get('devices') else ''
            })
        
        st.dataframe(exp_data, use_container_width=True)
    else:
        st.info("暂无实验记录")
    
    # 系统信息
    with st.expander("ℹ️ 系统信息"):
        st.markdown("""
        **版本**: v1.0.0  
        **更新日期**: 2024-01-15  
        **技术支持**: support@pvtest.com  
        **文档**: [查看用户手册](https://docs.pvtest.com)
        """)

# 主函数
def main():
    load_css()
    init_session_state()
    
    if st.session_state.authenticated:
        main_page()
    else:
        login_page()

if __name__ == "__main__":
    main()