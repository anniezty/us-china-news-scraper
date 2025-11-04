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

def export_to_sheets_append(df: pd.DataFrame, spreadsheet_id: str, sheet_name: str = None, 
                            credentials_path: str = "google_credentials.json", sort_by_date: bool = True):
    """
    追加 DataFrame 到 Google Sheets（去重后追加，并按日期排序）
    
    Args:
        df: 要追加的 DataFrame
        spreadsheet_id: Google Sheets 的 ID
        sheet_name: Sheet 名称
        credentials_path: Google 凭证文件路径
        sort_by_date: 是否按日期排序（从早到晚）
    """
    client = get_sheets_client(credentials_path)
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # 选择或创建 sheet
    if sheet_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            # 如果 sheet 已存在，读取现有数据用于去重
            existing_data = worksheet.get_all_values()
            if len(existing_data) > 1:
                existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
                # 按 URL 去重：只保留新数据中不存在的
                if 'URL' in existing_df.columns and 'URL' in df.columns:
                    existing_urls = set(existing_df['URL'].dropna())
                    df = df[~df['URL'].isin(existing_urls)]
                    if df.empty:
                        print(f"⚠️ 所有数据已存在，重新排序现有数据...")
                        # 即使没有新数据，也重新排序现有数据
                        if sort_by_date and 'Date' in existing_df.columns:
                            _sort_sheet_by_date(worksheet, existing_df, existing_data[0])
                            print(f"✅ 已按日期排序完成")
                        return
                
                # 合并现有数据和新数据
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            else:
                # sheet 存在但只有标题行，直接使用新数据
                combined_df = df.copy()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
            # 新 sheet，直接使用新数据
            combined_df = df.copy()
            existing_data = []  # 新 sheet，没有现有数据
    else:
        worksheet = spreadsheet.sheet1
        existing_data = worksheet.get_all_values()
        if len(existing_data) > 1:
            existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
            if 'URL' in existing_df.columns and 'URL' in df.columns:
                existing_urls = set(existing_df['URL'].dropna())
                df = df[~df['URL'].isin(existing_urls)]
                if df.empty:
                    print(f"⚠️ 所有数据已存在，跳过追加")
                    if sort_by_date and 'Date' in existing_df.columns:
                        _sort_sheet_by_date(worksheet, existing_df, existing_data[0])
                    return
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df.copy()
    
    # 按日期排序（从早到晚）
    if sort_by_date and 'Date' in combined_df.columns:
        try:
            # 尝试解析日期
            combined_df['Date_parsed'] = pd.to_datetime(combined_df['Date'], errors='coerce')
            # 先按日期排序，然后删除临时列
            combined_df = combined_df.sort_values('Date_parsed', ascending=True, na_position='last')
            combined_df = combined_df.drop('Date_parsed', axis=1)
        except Exception as e:
            print(f"⚠️ 日期排序失败: {e}，使用原始顺序")
    
    # 清空 sheet 并重新写入（保留标题行）
    worksheet.clear()
    if len(existing_data) > 0:
        worksheet.append_row(existing_data[0])  # 写入标题行
    else:
        worksheet.append_row(combined_df.columns.tolist())
    
    # 写入数据（分批写入）
    if not combined_df.empty:
        batch_size = 100
        for i in range(0, len(combined_df), batch_size):
            batch = combined_df.iloc[i:i+batch_size]
            values = batch.values.tolist()
            worksheet.append_rows(values)
        
        new_count = len(df)
        total_count = len(combined_df)
        print(f"✅ 已追加 {new_count} 行新数据，总计 {total_count} 行（已按日期排序）到 Google Sheets: {sheet_name}")

def _sort_sheet_by_date(worksheet, df: pd.DataFrame, headers: list):
    """
    对 sheet 按日期排序（辅助函数）
    """
    try:
        # 按日期排序
        if 'Date' in df.columns:
            df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date_parsed', ascending=True, na_position='last')
            df = df.drop('Date_parsed', axis=1)
        
        # 清空并重新写入
        worksheet.clear()
        worksheet.append_row(headers)
        
        batch_size = 100
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = batch.values.tolist()
            worksheet.append_rows(values)
    except Exception as e:
        print(f"⚠️ 排序失败: {e}")

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

