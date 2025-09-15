"""
文件处理模块
提供文件上传、下载和管理功能
"""

import pandas as pd
import io
import os
from typing import List, Dict, Optional, Tuple
import streamlit as st
from datetime import datetime
import logging
import zipfile
import json

logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理类"""
    
    ALLOWED_EXTENSIONS = ['xlsx', 'xls', 'csv', 'json']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate_file(cls, file) -> Tuple[bool, str]:
        """
        验证上传的文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            (是否有效, 错误信息)
        """
        if file is None:
            return False, "未选择文件"
        
        # 检查文件扩展名
        file_ext = file.name.split('.')[-1].lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(cls.ALLOWED_EXTENSIONS)}"
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > cls.MAX_FILE_SIZE:
            return False, f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB (最大: {cls.MAX_FILE_SIZE / 1024 / 1024}MB)"
        
        return True, ""
    
    @staticmethod
    def read_excel_file(file) -> pd.DataFrame:
        """
        读取Excel文件
        
        Args:
            file: 文件对象
            
        Returns:
            DataFrame
        """
        try:
            # 尝试读取所有工作表
            excel_file = pd.ExcelFile(file)
            
            # 如果只有一个工作表，直接读取
            if len(excel_file.sheet_names) == 1:
                df = pd.read_excel(file, sheet_name=0)
            else:
                # 让用户选择工作表
                sheet_name = st.selectbox(
                    "选择工作表",
                    excel_file.sheet_names
                )
                df = pd.read_excel(file, sheet_name=sheet_name)
            
            return df
            
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            raise
    
    @staticmethod
    def read_csv_file(file, encoding='utf-8') -> pd.DataFrame:
        """
        读取CSV文件
        
        Args:
            file: 文件对象
            encoding: 文件编码
            
        Returns:
            DataFrame
        """
        try:
            df = pd.read_csv(file, encoding=encoding)
            return df
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                df = pd.read_csv(file, encoding='gbk')
                return df
            except Exception as e:
                logger.error(f"读取CSV文件失败: {e}")
                raise
    
    @staticmethod
    def export_to_excel(
        dataframes: Dict[str, pd.DataFrame],
        filename: str = None
    ) -> bytes:
        """
        导出数据到Excel文件
        
        Args:
            dataframes: {sheet_name: dataframe} 字典
            filename: 文件名
            
        Returns:
            文件字节流
        """
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 获取工作表对象
                worksheet = writer.sheets[sheet_name]
                
                # 自动调整列宽
                for i, col in enumerate(df.columns):
                    column_width = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, column_width)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, encoding='utf-8') -> bytes:
        """
        导出数据到CSV文件
        
        Args:
            df: DataFrame
            encoding: 编码
            
        Returns:
            文件字节流
        """
        return df.to_csv(index=False, encoding=encoding).encode(encoding)
    
    @staticmethod
    def export_to_json(data: Dict) -> bytes:
        """
        导出数据到JSON文件
        
        Args:
            data: 数据字典
            
        Returns:
            文件字节流
        """
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    @staticmethod
    def create_download_link(
        file_bytes: bytes,
        filename: str,
        file_type: str = "application/octet-stream",
        button_text: str = "下载文件"
    ):
        """
        创建文件下载链接
        
        Args:
            file_bytes: 文件字节流
            filename: 文件名
            file_type: MIME类型
            button_text: 按钮文本
        """
        st.download_button(
            label=button_text,
            data=file_bytes,
            file_name=filename,
            mime=file_type
        )
    
    @staticmethod
    def batch_process_files(files: List) -> List[pd.DataFrame]:
        """
        批量处理文件
        
        Args:
            files: 文件列表
            
        Returns:
            DataFrame列表
        """
        dataframes = []
        errors = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(files):
            try:
                status_text.text(f"处理文件: {file.name}")
                
                # 根据文件类型读取
                if file.name.endswith(('.xlsx', '.xls')):
                    df = FileHandler.read_excel_file(file)
                elif file.name.endswith('.csv'):
                    df = FileHandler.read_csv_file(file)
                else:
                    errors.append(f"{file.name}: 不支持的文件类型")
                    continue
                
                dataframes.append((file.name, df))
                
            except Exception as e:
                errors.append(f"{file.name}: {str(e)}")
            
            # 更新进度
            progress_bar.progress((i + 1) / len(files))
        
        progress_bar.empty()
        status_text.empty()
        
        # 显示错误信息
        if errors:
            st.error("以下文件处理失败:")
            for error in errors:
                st.error(f"• {error}")
        
        return dataframes
    
    @staticmethod
    def create_zip_file(files: Dict[str, bytes]) -> bytes:
        """
        创建ZIP压缩文件
        
        Args:
            files: {filename: file_bytes} 字典
            
        Returns:
            ZIP文件字节流
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_bytes in files.items():
                zip_file.writestr(filename, file_bytes)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    @staticmethod
    def preview_dataframe(
        df: pd.DataFrame,
        max_rows: int = 100,
        show_stats: bool = True
    ):
        """
        预览DataFrame
        
        Args:
            df: DataFrame
            max_rows: 最大显示行数
            show_stats: 是否显示统计信息
        """
        st.subheader(f"数据预览 (前{min(len(df), max_rows)}行)")
        st.dataframe(df.head(max_rows), use_container_width=True)
        
        if show_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总行数", f"{len(df):,}")
            with col2:
                st.metric("总列数", f"{len(df.columns):,}")
            with col3:
                st.metric("内存占用", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            with col4:
                null_count = df.isnull().sum().sum()
                st.metric("空值数量", f"{null_count:,}")
            
            # 显示列信息
            with st.expander("列信息"):
                col_info = pd.DataFrame({
                    '列名': df.columns,
                    '数据类型': df.dtypes,
                    '非空值数': df.count(),
                    '唯一值数': [df[col].nunique() for col in df.columns],
                    '空值数': df.isnull().sum()
                })
                st.dataframe(col_info, use_container_width=True)
    
    @staticmethod
    def save_uploaded_file(uploaded_file, directory: str = "uploads") -> str:
        """
        保存上传的文件到本地
        
        Args:
            uploaded_file: 上传的文件对象
            directory: 保存目录
            
        Returns:
            保存的文件路径
        """
        # 创建目录
        os.makedirs(directory, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(directory, filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path