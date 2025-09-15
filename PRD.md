# 光伏关断器检测数据管理系统 - 产品需求文档（PRD）

## 1. 项目概述

### 1.1 项目背景
光伏关断器（Photovoltaic Rapid Shutdown Device, PVRSD）是太阳能光伏系统中的关键安全设备，用于在紧急情况下快速切断光伏阵列的输出，保护人员和设备安全。为了确保光伏关断器的质量和性能，需要进行严格的测试和数据管理。

### 1.2 项目目标
开发一个高端、现代化、工业级的光伏关断器实验数据管理系统，实现：
- 实验数据的可视化展示和实时监控
- 标准化的测试流程管理
- 实验数据的存储、查询和分析
- 符合国际标准的测试仿真功能
- 高效的数据文件管理

### 1.3 目标用户
- 光伏设备测试工程师
- 质量控制人员
- 实验室管理人员
- 数据分析师

## 2. 功能需求

### 2.1 系统架构
- **前端**：基于Python的Web框架（Streamlit）
- **后端**：Supabase（PostgreSQL数据库 + 认证 + 存储）
- **数据可视化**：Plotly、Altair
- **文件处理**：Pandas、OpenPyXL

### 2.2 核心功能模块

#### 2.2.1 用户认证与权限管理
- 用户注册/登录（通过Supabase Auth）
- 角色权限管理（管理员、工程师、查看者）
- 会话管理和安全控制

#### 2.2.2 数据展示大屏
- **实时数据监控**
  - 电流、电压、功率实时曲线
  - 设备状态指示器
  - 异常告警显示
  
- **统计分析仪表板**
  - 测试通过率统计
  - 设备性能趋势分析
  - 故障类型分布
  - 测试效率指标

- **可视化组件**
  - 动态折线图、柱状图、散点图
  - 热力图（设备性能矩阵）
  - 仪表盘（关键性能指标）
  - 3D数据可视化（可选）

#### 2.2.3 数据文件管理
- **文件上传功能**
  - 支持Excel、CSV格式
  - 批量上传
  - 数据格式验证
  - 自动解析和入库

- **文件下载功能**
  - 按条件导出数据
  - 多格式支持（Excel、CSV、PDF报告）
  - 批量下载

- **文件管理**
  - 文件列表展示
  - 文件预览
  - 文件删除和归档
  - 版本控制

#### 2.2.4 实验测试模块

##### 2.2.4.1 耐压实验（Dielectric Withstand Test）
参考标准：IEC 60947-3, UL 1741
- **测试参数设置**
  - 测试电压：1000V DC + 2倍额定电压
  - 测试时间：60秒
  - 漏电流限值：≤5mA
  
- **测试流程**
  - 预检查（设备状态、接线确认）
  - 逐步升压过程
  - 保持测试
  - 降压过程
  - 结果判定

- **数据记录**
  - 实时电压、电流曲线
  - 击穿点记录
  - 测试结果（通过/失败）

##### 2.2.4.2 泄漏电流实验（Leakage Current Test）
参考标准：IEC 62109-2
- **测试参数**
  - 测试电压：1.1倍额定电压
  - 温度条件：25°C、40°C、60°C
  - 湿度条件：标准湿度、高湿度（93%RH）

- **测试内容**
  - 正常条件泄漏电流
  - 高温泄漏电流
  - 高湿泄漏电流
  - 长期稳定性测试

##### 2.2.4.3 正常工况试验
- **功能测试**
  - 关断响应时间（≤30秒）
  - 通信功能测试
  - 远程控制测试
  - 自动重启功能

- **性能测试**
  - 额定功率运行
  - 效率测试
  - 温升测试
  - EMC测试

##### 2.2.4.4 异常工况试验
- **过载测试**
  - 1.1倍、1.5倍、2倍额定电流
  - 持续时间和保护动作

- **短路测试**
  - 输出短路保护
  - 输入短路保护
  - 接地故障保护

- **环境适应性**
  - 高低温循环（-40°C至+85°C）
  - 湿热循环
  - 振动和冲击测试
  - 盐雾测试

#### 2.2.5 实验仿真页面
- **仿真控制面板**
  - 参数设置界面
  - 仿真启动/停止控制
  - 实时进度显示

- **仿真模型**
  - 电路模型可视化
  - 参数动态调整
  - 故障注入仿真

- **结果分析**
  - 仿真数据与实测数据对比
  - 偏差分析
  - 优化建议

#### 2.2.6 报告生成
- 自动生成测试报告（PDF格式）
- 包含所有测试数据和图表
- 符合认证要求的报告模板
- 电子签名功能

### 2.3 非功能需求

#### 2.3.1 性能要求
- 页面加载时间 < 2秒
- 数据查询响应时间 < 1秒
- 支持10万条数据的实时展示
- 并发用户数 ≥ 50

#### 2.3.2 安全要求
- HTTPS加密传输
- 数据加密存储
- 操作日志记录
- 定期数据备份

#### 2.3.3 可用性要求
- 系统可用性 ≥ 99.9%
- 支持移动端响应式设计
- 多语言支持（中文、英文）
- 用户友好的界面设计

#### 2.3.4 兼容性要求
- 支持Chrome、Firefox、Safari、Edge浏览器
- 支持Windows、macOS、Linux操作系统

## 3. 数据库设计

### 3.1 主要数据表

#### 3.1.1 实验数据表（experiment_data）
```sql
- id: UUID (主键)
- experiment_id: UUID (外键，关联到experiments表)
- current: FLOAT (电流，单位：A)
- voltage: FLOAT (电压，单位：V)
- power: FLOAT (功率，单位：W)
- timestamp: TIMESTAMP (时间戳)
- device_address: INTEGER (设备地址)
- device_type: VARCHAR(50) (设备类型)
- temperature: FLOAT (温度，单位：°C)
- humidity: FLOAT (湿度，单位：%RH)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 3.1.2 实验记录表（experiments）
```sql
- id: UUID (主键)
- experiment_name: VARCHAR(100) (实验名称)
- experiment_type: VARCHAR(50) (实验类型)
- operator_id: UUID (外键，关联到users表)
- start_time: TIMESTAMP
- end_time: TIMESTAMP
- status: VARCHAR(20) (进行中/已完成/已取消)
- result: VARCHAR(20) (通过/失败/未判定)
- notes: TEXT (备注)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 3.1.3 设备信息表（devices）
```sql
- id: UUID (主键)
- device_serial: VARCHAR(50) (设备序列号)
- device_model: VARCHAR(50) (设备型号)
- manufacturer: VARCHAR(100) (制造商)
- rated_voltage: FLOAT (额定电压)
- rated_current: FLOAT (额定电流)
- rated_power: FLOAT (额定功率)
- manufacture_date: DATE
- calibration_date: DATE
- next_calibration: DATE
- status: VARCHAR(20) (正常/维修中/已报废)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 3.1.4 测试标准表（test_standards）
```sql
- id: UUID (主键)
- standard_code: VARCHAR(50) (标准编号)
- standard_name: VARCHAR(200) (标准名称)
- test_type: VARCHAR(50) (测试类型)
- parameters: JSONB (测试参数)
- pass_criteria: JSONB (通过标准)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 3.1.5 文件管理表（files）
```sql
- id: UUID (主键)
- file_name: VARCHAR(200)
- file_path: VARCHAR(500)
- file_size: BIGINT
- file_type: VARCHAR(50)
- experiment_id: UUID (外键)
- uploaded_by: UUID (外键)
- upload_time: TIMESTAMP
- created_at: TIMESTAMP
```

## 4. UI/UX设计规范

### 4.1 设计原则
- **工业化设计**：采用深色主题，突出数据可视化
- **现代化风格**：扁平化设计，简洁的图标和动画
- **高端感**：精细的细节处理，专业的配色方案
- **响应式设计**：适配不同屏幕尺寸

### 4.2 配色方案
- 主色调：深蓝色（#1a237e）
- 辅助色：橙色（#ff6f00）、绿色（#00c853）
- 背景色：深灰色（#121212）、浅灰色（#1e1e1e）
- 文字色：白色（#ffffff）、浅灰色（#b0b0b0）

### 4.3 字体规范
- 标题字体：Inter Bold
- 正文字体：Inter Regular
- 数据字体：Roboto Mono

### 4.4 组件设计
- 使用阴影和渐变增加层次感
- 数据卡片采用玻璃态效果
- 按钮和交互元素有悬停动画
- 图表使用平滑过渡动画

## 5. 技术实现细节

### 5.1 前端技术栈
- **框架**：Streamlit 1.29+
- **数据可视化**：Plotly 5.18+, Altair 5.2+
- **数据处理**：Pandas 2.0+, NumPy 1.24+
- **文件处理**：OpenPyXL 3.1+
- **HTTP客户端**：httpx 0.25+

### 5.2 Supabase集成
- **认证**：使用Supabase Auth进行用户管理
- **实时数据**：利用Supabase Realtime订阅数据更新
- **存储**：使用Supabase Storage管理文件
- **数据库**：PostgreSQL with Row Level Security (RLS)

### 5.3 部署方案
- **部署平台**：Streamlit Cloud / AWS / Azure
- **CI/CD**：GitHub Actions
- **监控**：集成应用性能监控（APM）
- **日志**：结构化日志记录

## 6. 项目里程碑

### Phase 1：基础框架搭建（第1-2周）
- 项目初始化和环境配置
- Supabase数据库设计和创建
- 基础UI框架搭建
- 用户认证集成

### Phase 2：核心功能开发（第3-6周）
- 数据展示大屏开发
- 文件管理功能实现
- 四种实验测试页面开发
- 数据导入导出功能

### Phase 3：高级功能和优化（第7-8周）
- 实验仿真功能开发
- 报告生成功能
- UI美化和响应式优化
- 性能优化

### Phase 4：测试和部署（第9-10周）
- 功能测试
- 性能测试
- 安全测试
- 正式部署上线

## 7. 风险评估

### 7.1 技术风险
- Streamlit在处理大量实时数据时的性能限制
- Supabase免费版的使用限制
- 缓解措施：性能优化、数据分页、考虑升级Supabase计划

### 7.2 数据风险
- 实验数据的准确性和完整性
- 数据安全和隐私保护
- 缓解措施：数据验证、加密存储、定期备份

### 7.3 用户体验风险
- 复杂的实验流程可能导致操作困难
- 缓解措施：提供详细的操作指南、交互式教程

## 8. 成功指标

- 系统稳定运行，可用性达到99.9%
- 数据查询响应时间小于1秒
- 用户满意度达到90%以上
- 支持至少50个并发用户
- 测试数据准确率100%
- 报告生成自动化率100%