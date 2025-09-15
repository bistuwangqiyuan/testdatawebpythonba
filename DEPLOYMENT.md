# 部署说明

## Streamlit Cloud 部署

### 1. 环境变量配置

在 Streamlit Cloud 中需要设置以下环境变量：

```
PUBLIC_SUPABASE_URL=https://zzyueuweeoakopuuwfau.supabase.co
PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6eXVldXdlZW9ha29wdXV3ZmF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQzODEzMDEsImV4cCI6MjA1OTk1NzMwMX0.y8V3EXK9QVd3txSWdE3gZrSs96Ao0nvpnd0ntZw_dQ4
```

### 2. 部署步骤

1. 将代码推送到 GitHub 仓库
2. 访问 [Streamlit Cloud](https://share.streamlit.io/)
3. 点击 "New app"
4. 选择 GitHub 仓库
5. 设置主文件路径为 `app.py`
6. 配置环境变量
7. 点击 "Deploy"

### 3. 项目结构

```
photovoltaic-shutdown-test-system/
├── app.py                  # 主应用入口
├── requirements.txt        # Python依赖
├── .streamlit/            # Streamlit配置
│   └── config.toml
├── pages/                 # Streamlit页面
│   ├── 1_🖥️_数据大屏.py
│   ├── 2_📁_文件管理.py
│   ├── 3_🔬_耐压实验.py
│   ├── 4_⚡_泄漏电流实验.py
│   ├── 5_✅_正常工况试验.py
│   ├── 6_⚠️_异常工况试验.py
│   └── 7_🎮_实验仿真.py
├── utils/                 # 工具模块
│   ├── supabase_client.py
│   ├── data_processor.py
│   ├── visualization.py
│   └── file_handler.py
├── data/                  # 示例数据
└── assets/               # 静态资源
    └── style.css
```

### 4. 功能特性

- ✅ 游客模式 - 无需登录即可使用所有功能
- ✅ 实时数据监控
- ✅ 文件上传下载
- ✅ 实验测试功能
- ✅ 仿真平台
- ✅ 数据可视化
- ✅ 响应式设计

### 5. 注意事项

- 确保所有依赖包在 requirements.txt 中正确列出
- 环境变量必须正确配置
- 项目支持离线模式，即使数据库连接失败也能正常运行
