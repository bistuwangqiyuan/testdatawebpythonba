-- 光伏关断器检测数据管理系统数据库架构
-- 适用于Supabase (PostgreSQL)

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 设备信息表
CREATE TABLE IF NOT EXISTS devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    device_serial VARCHAR(50) UNIQUE NOT NULL,
    device_model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    rated_voltage FLOAT,
    rated_current FLOAT,
    rated_power FLOAT,
    manufacture_date DATE,
    calibration_date DATE,
    next_calibration DATE,
    status VARCHAR(20) DEFAULT 'normal' CHECK (status IN ('normal', 'maintenance', 'retired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 2. 实验记录表
CREATE TABLE IF NOT EXISTS experiments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    experiment_type VARCHAR(50) NOT NULL CHECK (experiment_type IN ('dielectric', 'leakage', 'normal', 'abnormal', 'simulation')),
    device_id UUID REFERENCES devices(id),
    operator_id UUID REFERENCES auth.users(id),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'cancelled')),
    result VARCHAR(20) CHECK (result IN ('pass', 'fail', 'pending')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 3. 实验数据表
CREATE TABLE IF NOT EXISTS experiment_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    sequence_number INTEGER,
    current FLOAT,
    voltage FLOAT,
    power FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    device_address INTEGER,
    device_type VARCHAR(50),
    temperature FLOAT,
    humidity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 4. 测试标准表
CREATE TABLE IF NOT EXISTS test_standards (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    standard_code VARCHAR(50) UNIQUE NOT NULL,
    standard_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    parameters JSONB,
    pass_criteria JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 5. 文件管理表
CREATE TABLE IF NOT EXISTS files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(50),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES auth.users(id),
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 6. 用户配置表
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('admin', 'engineer', 'viewer')),
    department VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 7. 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    operation_type VARCHAR(50) NOT NULL,
    operation_detail TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 创建索引以提高查询性能
CREATE INDEX idx_experiment_data_experiment_id ON experiment_data(experiment_id);
CREATE INDEX idx_experiment_data_timestamp ON experiment_data(timestamp);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_type ON experiments(experiment_type);
CREATE INDEX idx_files_experiment_id ON files(experiment_id);
CREATE INDEX idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiment_data_updated_at BEFORE UPDATE ON experiment_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_standards_updated_at BEFORE UPDATE ON test_standards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认测试标准
INSERT INTO test_standards (standard_code, standard_name, test_type, parameters, pass_criteria) VALUES
('IEC-60947-3-DW', '耐压试验 - IEC 60947-3', 'dielectric', 
 '{"test_voltage": "1000V DC + 2×额定电压", "test_duration": 60, "leakage_limit": 5}',
 '{"max_leakage_current": 5, "breakdown": false}'),
 
('IEC-62109-2-LC', '泄漏电流试验 - IEC 62109-2', 'leakage',
 '{"test_voltage": "1.1×额定电压", "temperatures": [25, 40, 60], "humidity": [60, 93]}',
 '{"max_leakage_25C": 3.5, "max_leakage_60C": 5.0}'),
 
('UL-1741-NC', '正常工况试验 - UL 1741', 'normal',
 '{"shutdown_time": 30, "communication_test": true, "remote_control": true}',
 '{"max_shutdown_time": 30, "function_test": "pass"}'),
 
('GB-37408-AC', '异常工况试验 - GB/T 37408', 'abnormal',
 '{"overload_levels": [1.1, 1.5, 2.0], "short_circuit": true, "temperature_range": [-40, 85]}',
 '{"protection_triggered": true, "no_damage": true}');

-- 创建行级安全策略 (RLS)
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE operation_logs ENABLE ROW LEVEL SECURITY;

-- 创建策略允许认证用户访问数据
CREATE POLICY "Allow authenticated users to read devices" ON devices
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow engineers and admins to insert devices" ON devices
    FOR INSERT WITH CHECK (
        auth.uid() IN (
            SELECT id FROM user_profiles WHERE role IN ('engineer', 'admin')
        )
    );

CREATE POLICY "Allow authenticated users to read experiments" ON experiments
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow engineers and admins to manage experiments" ON experiments
    FOR ALL USING (
        auth.uid() IN (
            SELECT id FROM user_profiles WHERE role IN ('engineer', 'admin')
        )
    );

CREATE POLICY "Allow authenticated users to read experiment_data" ON experiment_data
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow engineers and admins to manage experiment_data" ON experiment_data
    FOR ALL USING (
        auth.uid() IN (
            SELECT id FROM user_profiles WHERE role IN ('engineer', 'admin')
        )
    );

-- 注意：实际部署时需要在Supabase控制台中执行这些SQL语句