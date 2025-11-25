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

def get_sheets_client(credentials_path: str = None):
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
    # 如果 credentials_path 为 None，使用默认路径
    if credentials_path is None:
        credentials_path = "google_credentials.json"
    
    if credentials_path and os.path.exists(credentials_path):
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
                     credentials_path: str = None):
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
                            credentials_path: str = None, sort_by_date: bool = True):
    """
    追加 DataFrame 到 Google Sheets（新逻辑：检查URL -> 补充新数据 -> 排序）
    
    流程：
    1. 跨 sheet 检查 URL（去重）
    2. 读取当前 sheet 的现有数据
    3. 合并新数据（过滤掉已存在的 URL）
    4. 去重
    5. 排序
    6. 重新写入（确保标题行存在）
    
    Args:
        df: 要追加的 DataFrame
        spreadsheet_id: Google Sheets 的 ID
        sheet_name: Sheet 名称
        credentials_path: Google 凭证文件路径
        sort_by_date: 是否按日期排序（从早到晚）
    """
    client = get_sheets_client(credentials_path)
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # ========== 步骤1: 跨 sheet 检查 URL（去重） ==========
    all_existing_urls = set()
    if 'URL' in df.columns:
        for sheet in spreadsheet.worksheets():
            try:
                sheet_data = sheet.get_all_values()
                if len(sheet_data) <= 1:
                    continue
                if len(sheet_data[0]) == 0:
                    continue
                sheet_df = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])
                if 'URL' not in sheet_df.columns:
                    continue
                urls = sheet_df['URL'].dropna()
                if len(urls) == 0:
                    continue
                # 收集所有 sheet 的 URL（包括当前 sheet，用于后续去重）
                all_existing_urls.update(urls)
            except Exception as e:
                print(f"⚠️ 读取 sheet '{sheet.title}' 时出错: {e}")
                continue
        
        # 过滤掉所有 sheet 中已存在的 URL
        original_count = len(df)
        df = df[~df['URL'].astype(str).str.strip().isin([url.strip() for url in all_existing_urls])]
        if len(df) < original_count:
            print(f"📝 跨 sheet 去重：过滤掉 {original_count - len(df)} 篇已存在的文章")
    
    # ========== 步骤2: 选择或创建 sheet ==========
    if sheet_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            sheet_exists = True
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
            sheet_exists = False
    else:
        worksheet = spreadsheet.sheet1
        sheet_exists = True
    
    # ========== 步骤3: 读取现有数据并合并新数据 ==========
    expected_columns = df.columns.tolist()
    existing_df = pd.DataFrame()
    
    # 无论是新sheet还是已存在的sheet，都尝试读取数据
    try:
        existing_data = worksheet.get_all_values()
        if len(existing_data) > 0:
            existing_headers = existing_data[0]
            
            # 检查标题行是否存在且有效
            has_valid_header = (len(existing_headers) > 0 and 
                              any(str(h).strip() for h in existing_headers) and
                              len(set(str(h).strip() for h in existing_headers if h) & set(expected_columns)) >= 2)
            
            if has_valid_header:
                # 有有效的标题行，读取数据（跳过标题行）
                if len(existing_data) > 1:
                    existing_df = pd.DataFrame(existing_data[1:], columns=existing_headers)
                    # 确保列顺序与期望一致
                    if set(existing_headers) == set(expected_columns):
                        existing_df = existing_df[expected_columns]
                    else:
                        # 列名不完全匹配，对齐
                        aligned_df = pd.DataFrame()
                        for col in expected_columns:
                            if col in existing_headers:
                                aligned_df[col] = existing_df[col]
                            else:
                                aligned_df[col] = None
                        existing_df = aligned_df
                    print(f"📖 读取现有数据: {len(existing_df)} 行")
                else:
                    # 只有标题行，没有数据
                    print(f"ℹ️ Sheet 只有标题行，没有数据")
            else:
                # 标题行无效或不存在，第一行可能是数据
                if len(existing_data) > 0:
                    # 第一行可能是数据，全部当作数据读取
                    existing_df = pd.DataFrame(existing_data, columns=expected_columns[:len(existing_data[0])] if existing_data else expected_columns)
                    # 如果列数不匹配，尝试对齐
                    if len(existing_data[0]) != len(expected_columns):
                        aligned_df = pd.DataFrame()
                        for i, col in enumerate(expected_columns):
                            if i < len(existing_data[0]):
                                # 从第一行开始读取所有数据
                                aligned_df[col] = [row[i] if i < len(row) else "" for row in existing_data]
                            else:
                                aligned_df[col] = None
                        existing_df = aligned_df
                    print(f"⚠️ 标题行无效，将第一行当作数据读取: {len(existing_df)} 行")
        else:
            # Sheet 为空（新sheet）
            print(f"ℹ️ Sheet 为空（新sheet），将创建标题行")
    except Exception as e:
        print(f"⚠️ 读取现有数据时出错: {e}，将当作新sheet处理")
    
    # ========== 步骤4: 合并数据并去重 ==========
    # 确保 existing_df 和 df 的列顺序一致（在合并前）
    if not existing_df.empty:
        # 确保 existing_df 的列顺序与 expected_columns 一致
        if list(existing_df.columns) != expected_columns:
            # 重新排列列顺序
            missing_cols = [col for col in expected_columns if col not in existing_df.columns]
            if missing_cols:
                for col in missing_cols:
                    existing_df[col] = None
            existing_df = existing_df[expected_columns]
            print(f"✅ 已调整现有数据的列顺序")
        
        # 确保 df 的列顺序也一致
        if list(df.columns) != expected_columns:
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                for col in missing_cols:
                    df[col] = None
            df = df[expected_columns]
        
        # 合并现有数据和新数据
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        print(f"📊 合并数据: 现有 {len(existing_df)} 行 + 新 {len(df)} 行 = {len(combined_df)} 行")
    else:
        # 确保 df 的列顺序一致
        if list(df.columns) != expected_columns:
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                for col in missing_cols:
                    df[col] = None
            df = df[expected_columns]
        combined_df = df.copy()
    
    # 去重（基于 URL）- 必须执行，确保没有重复
    if 'URL' in combined_df.columns and not combined_df.empty:
        before_dedup = len(combined_df)
        # 清理 URL 格式（去除空格、统一格式）
        combined_df['URL_cleaned'] = combined_df['URL'].astype(str).str.strip().str.lower()
        # 去除空URL
        combined_df = combined_df[combined_df['URL_cleaned'] != '']
        combined_df = combined_df[combined_df['URL_cleaned'] != 'nan']
        # 去重（保留第一个）
        combined_df = combined_df.drop_duplicates(subset=['URL_cleaned'], keep='first')
        combined_df = combined_df.drop('URL_cleaned', axis=1)
        after_dedup = len(combined_df)
        if before_dedup > after_dedup:
            print(f"📝 URL 去重：移除 {before_dedup - after_dedup} 篇重复文章（基于URL）")
        else:
            print(f"✅ URL 去重检查完成：无重复（{after_dedup} 行）")
    else:
        print(f"⚠️ 警告：无法进行URL去重（URL列不存在或数据为空）")
    
    # ========== 步骤5: 只追加新数据，不清空现有数据（完全安全） ==========
    if df.empty:
        print(f"ℹ️ 没有新数据可追加")
        return
    
    # 确保新数据的列顺序一致
    df = df[expected_columns]
    
    # 检查并确保标题行存在（只检查，不清空）
    try:
        existing_data = worksheet.get_all_values()
        has_header = False
        if len(existing_data) > 0:
            first_row = existing_data[0]
            first_row_set = set(str(c).strip() for c in first_row if c)
            expected_set = set(expected_columns)
            # 如果第一行包含至少3个期望的列名，认为是标题行
            if len(first_row_set & expected_set) >= 3:
                has_header = True
        
        if not has_header:
            # 没有标题行，在第一行插入标题行
            print(f"⚠️ 检测到没有标题行，将在第一行插入标题行")
            worksheet.insert_row(expected_columns, 1)
            print(f"✅ 已插入标题行: {expected_columns}")
        else:
            print(f"✅ 标题行已存在")
    except Exception as e:
        print(f"⚠️ 检查标题行时出错: {e}，尝试插入标题行")
        try:
            existing_data = worksheet.get_all_values()
            if len(existing_data) == 0 or not any(str(c).strip() for c in existing_data[0] if existing_data):
                worksheet.insert_row(expected_columns, 1)
                print(f"✅ 已插入标题行")
        except:
            pass
    
    # 只追加新数据到 sheet 末尾（完全不清空，绝对安全）
    batch_size = 100
    rows_written = 0
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        values = batch.values.tolist()
        worksheet.append_rows(values)
        rows_written += len(batch)
    
    # 检查写入的数据量
    if rows_written != len(df):
        print(f"⚠️ 警告：写入的数据量不匹配！期望 {len(df)} 行，实际写入 {rows_written} 行")
    
    print(f"✅ 完成！已追加 {rows_written} 行新数据到 Google Sheets: {sheet_name}（不清空现有数据，完全安全）")
    print(f"ℹ️ 注意：如需排序，请在 Google Sheets 中手动排序，或使用 reprocess_sheet.py 脚本")

def _sort_sheet_by_date(worksheet, df: pd.DataFrame, headers: list):
    """
    对 sheet 按日期排序（辅助函数）
    注意：此函数已弃用，不再使用清空重写的方式，避免数据丢失
    如需排序，请在 Google Sheets 中手动排序或使用其他安全方式
    """
    # 已弃用：不再清空 sheet 重新写入，避免数据丢失
    # 如果需要排序，请在 Google Sheets 中手动排序
    print(f"⚠️ _sort_sheet_by_date 已弃用，不再执行排序操作（避免数据丢失）")
    return

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
            sheet_name = f"{start_date} to {end_date}"
        else:
            sheet_name = f"{datetime.now().strftime('%Y-%m-%d')}"
    else:
        sheet_name = f"Week {datetime.now().strftime('%Y-%m-%d')}"
    
    export_to_sheets(df, spreadsheet_id, sheet_name, credentials_path)

def read_from_sheets(spreadsheet_id: str, sheet_name: str = None,
                    credentials_path: str = None) -> pd.DataFrame:
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

