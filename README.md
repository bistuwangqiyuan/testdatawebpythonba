# 光伏关断器检测数据管理系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个高端、现代化的光伏关断器实验数据管理系统，提供全方位的测试数据管理、可视化分析和标准化测试流程。

## 🌟 主要特性

- **🖥️ 数据展示大屏** - 实时监控和可视化展示实验数据
- **📁 文件管理系统** - 支持Excel数据导入导出，批量文件处理
- **🔬 标准化测试** - 符合IEC、UL等国际标准的测试流程
- **⚡ 实时数据更新** - 基于Supabase的实时数据同步
- **🎨 现代化UI** - 工业风格的深色主题设计
- **🔐 安全认证** - 完整的用户权限管理系统
- **📊 数据分析** - 强大的数据统计和分析功能
- **📱 响应式设计** - 支持多设备访问

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip 包管理器
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd photovoltaic-shutdown-test-system
```

2. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
创建 `.env` 文件并添加以下内容：
```env
PUBLIC_SUPABASE_URL=https://zzyueuweeoakopuuwfau.supabase.co
PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6eXVldXdlZW9ha29wdXV3ZmF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQzODEzMDEsImV4cCI6MjA1OTk1NzMwMX0.y8V3EXK9QVd3txSWdE3gZrSs96Ao0nvpnd0ntZw_dQ4
```

5. **运行应用**
```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动

## 📋 功能模块

### 1. 数据展示大屏
- 实时电流、电压、功率监控
- 设备状态指示器
- 异常告警系统
- 统计分析仪表板

### 2. 实验测试模块
- **耐压实验** - 按照IEC 60947-3标准
- **泄漏电流实验** - 符合IEC 62109-2要求
- **正常工况试验** - 功能和性能测试
- **异常工况试验** - 过载、短路、环境适应性测试

### 3. 数据管理
- Excel/CSV文件导入导出
- 批量数据处理
- 数据验证和清洗
- 历史数据查询

### 4. 实验仿真
- 参数化仿真模型
- 实时仿真监控
- 结果对比分析
- 优化建议生成

## 🏗️ 项目结构

```
photovoltaic-shutdown-test-system/
├── app.py                  # 主应用入口
├── requirements.txt        # Python依赖
├── .env                   # 环境变量配置
├── README.md              # 项目说明文档
├── PRD.md                 # 产品需求文档
├── pages/                 # Streamlit页面
│   ├── 1_🖥️_数据大屏.py
│   ├── 2_📁_文件管理.py
│   ├── 3_🔬_耐压实验.py
│   ├── 4_⚡_泄漏电流实验.py
│   ├── 5_✅_正常工况试验.py
│   ├── 6_⚠️_异常工况试验.py
│   └── 7_🎮_实验仿真.py
├── utils/                 # 工具模块
│   ├── supabase_client.py # Supabase客户端
│   ├── data_processor.py  # 数据处理
│   ├── visualization.py   # 可视化工具
│   └── file_handler.py    # 文件处理
├── data/                  # 示例数据
│   └── *.xlsx            # Excel示例文件
└── assets/               # 静态资源
    └── style.css         # 自定义样式
```

## 💻 技术栈

- **前端框架**: Streamlit 1.29+
- **数据可视化**: Plotly, Altair
- **数据处理**: Pandas, NumPy
- **数据库**: Supabase (PostgreSQL)
- **认证系统**: Supabase Auth
- **文件存储**: Supabase Storage
- **实时更新**: Supabase Realtime

## 🔧 配置说明

### Supabase数据库表

系统需要以下数据表：

1. **experiment_data** - 实验数据表
2. **experiments** - 实验记录表
3. **devices** - 设备信息表
4. **test_standards** - 测试标准表
5. **files** - 文件管理表

详细表结构请参考 [PRD.md](PRD.md) 中的数据库设计章节。

### 用户权限

系统支持三种用户角色：
- **管理员** - 完全访问权限
- **工程师** - 执行测试和查看数据
- **查看者** - 只读权限

## 📊 数据格式

系统支持的数据格式示例：

```
序号  电流(A)  电压(V)  功率(W)  时间戳      设备地址  设备类型
1     0.11     20.36    2.24     2025/5/2   1        未知
2     0.26     20.68    5.38     2025/5/2   1        未知
...
```

## 🛡️ 安全性

- HTTPS加密传输
- 基于JWT的认证系统
- Row Level Security (RLS)
- 定期数据备份
- 操作日志审计

## 📈 性能指标

- 页面加载时间 < 2秒
- 数据查询响应 < 1秒
- 支持10万+数据点实时展示
- 并发用户数 ≥ 50

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持与联系

- 问题反馈：[创建 Issue](https://github.com/your-repo/issues)
- 邮件联系：support@example.com
- 文档中心：[查看文档](docs/)

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 优秀的Python Web框架
- [Supabase](https://supabase.com/) - 强大的开源后端服务
- [Plotly](https://plotly.com/) - 交互式数据可视化库

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！