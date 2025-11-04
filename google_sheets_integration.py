#!/usr/bin/env python3
"""
Google Sheets 集成
自动将数据导出到 Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os
import json

# Google Sheets API 权限范围
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client(credentials_path: str = "google_credentials.json"):
    """
    获取 Google Sheets 客户端
    
    支持多种凭证来源（按优先级）：
    1. Streamlit Secrets（如果在 Streamlit 环境中）
    2. 环境变量 GOOGLE_CREDENTIALS_JSON（JSON 字符串）
    3. 本地文件 google_credentials.json
    """
    creds = None
    
    # 方式 1: 尝试从 Streamlit Secrets 读取（仅在 Streamlit 环境中）
    try:
        import streamlit as st
        # 在 Streamlit 环境中，直接检查 secrets
        if hasattr(st, 'secrets'):
            try:
                if 'google_sheets' in st.secrets:
                    creds_dict = st.secrets['google_sheets'].get('credentials')
                    if creds_dict:
                        # 如果是字符串，尝试解析 JSON
                        if isinstance(creds_dict, str):
                            creds_dict = json.loads(creds_dict)
                        elif isinstance(creds_dict, dict):
                            # 已经是字典，直接使用
                            pass
                        else:
                            creds_dict = None
                        
                        if creds_dict:
                            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                            return gspread.authorize(creds)
            except (KeyError, AttributeError, json.JSONDecodeError) as e:
                # Secrets 配置有问题，继续尝试其他方式
                pass
    except (ImportError, FileNotFoundError):
        # 不在 Streamlit 环境或 secrets 文件不存在，继续尝试其他方式
        pass
    
    # 方式 2: 尝试从环境变量读取（JSON 字符串）
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            return gspread.authorize(creds)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️ 环境变量 GOOGLE_CREDENTIALS_JSON 格式错误: {e}")
    
    # 方式 3: 从本地文件读取
    if os.path.exists(credentials_path):
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        return gspread.authorize(creds)
    
    # 如果所有方式都失败
    raise FileNotFoundError(
        f"Google 凭证未找到\n"
        "请选择以下方式之一：\n"
        "1. 在 Streamlit Secrets 中配置 google_sheets.credentials\n"
        "2. 设置环境变量 GOOGLE_CREDENTIALS_JSON\n"
        "3. 创建文件 google_credentials.json"
    )

def export_to_sheets(df: pd.DataFrame, spreadsheet_id: str, sheet_name: str = None, 
                     credentials_path: str = "google_credentials.json"):
    """
    导出 DataFrame 到 Google Sheets
    
    Args:
        df: 要导出的 DataFrame
        spreadsheet_id: Google Sheets 的 ID（从 URL 中获取）
        sheet_name: Sheet 名称（如果为 None，则覆盖第一个 sheet）
        credentials_path: Google 凭证文件路径
    """
    client = get_sheets_client(credentials_path)
    
    # 打开 spreadsheet
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # 选择或创建 sheet
    if sheet_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
    else:
        worksheet = spreadsheet.sheet1
    
    # 清空现有数据（保留标题行）
    worksheet.clear()
    
    # 写入数据
    # 先写入列名
    worksheet.append_row(df.columns.tolist())
    
    # 写入数据（分批写入，避免超时）
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        values = batch.values.tolist()
        worksheet.append_rows(values)
    
    print(f"✅ 已导出 {len(df)} 行数据到 Google Sheets: {sheet_name}")

def create_weekly_sheet(df: pd.DataFrame, spreadsheet_id: str, 
                        credentials_path: str = "google_credentials.json"):
    """
    创建每周的 sheet（按日期命名）
    """
    # 获取日期范围
    if 'Date' in df.columns:
        dates = pd.to_datetime(df['Date'], errors='coerce').dropna()
        if len(dates) > 0:
            start_date = dates.min().strftime("%Y-%m-%d")
            end_date = dates.max().strftime("%Y-%m-%d")
            sheet_name = f"Week {start_date} to {end_date}"
        else:
            sheet_name = f"Week {datetime.now().strftime('%Y-%m-%d')}"
    else:
        sheet_name = f"Week {datetime.now().strftime('%Y-%m-%d')}"
    
    export_to_sheets(df, spreadsheet_id, sheet_name, credentials_path)

def read_from_sheets(spreadsheet_id: str, sheet_name: str = None,
                    credentials_path: str = "google_credentials.json") -> pd.DataFrame:
    """
    从 Google Sheets 读取数据
    """
    client = get_sheets_client(credentials_path)
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    if sheet_name:
        worksheet = spreadsheet.worksheet(sheet_name)
    else:
        worksheet = spreadsheet.sheet1
    
    # 读取所有数据
    data = worksheet.get_all_values()
    
    if len(data) == 0:
        return pd.DataFrame()
    
    # 第一行作为列名
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

