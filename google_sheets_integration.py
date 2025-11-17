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
    追加 DataFrame 到 Google Sheets（跨 sheet 去重后追加，并按日期排序）
    
    Args:
        df: 要追加的 DataFrame
        spreadsheet_id: Google Sheets 的 ID
        sheet_name: Sheet 名称
        credentials_path: Google 凭证文件路径
        sort_by_date: 是否按日期排序（从早到晚）
    """
    client = get_sheets_client(credentials_path)
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # 跨 sheet 去重：收集所有 sheet 中的 URL（用于防止重复添加新数据）
    # 注意：排除当前 sheet，因为我们要合并到当前 sheet，会在合并后单独处理当前 sheet 的去重
    all_existing_urls = set()
    current_sheet_urls = set()  # 当前 sheet 的 URL（用于后续合并时去重）
    if 'URL' in df.columns:
        for sheet in spreadsheet.worksheets():
            try:
                sheet_data = sheet.get_all_values()
                # 跳过空白 sheet（只有标题行或完全没有数据）
                if len(sheet_data) <= 1:
                    continue
                # 确保有标题行且至少有一行数据
                if len(sheet_data[0]) == 0:
                    continue
                sheet_df = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])
                # 确保有 URL 列且有实际数据
                if 'URL' not in sheet_df.columns:
                    continue
                urls = sheet_df['URL'].dropna()
                # 如果没有任何 URL，跳过（可能是空白 sheet）
                if len(urls) == 0:
                    continue
                # 如果是当前 sheet，单独记录（用于后续合并时去重）
                if sheet_name and sheet.title == sheet_name:
                    current_sheet_urls.update(urls)
                else:
                    # 其他 sheet 的 URL 用于跨 sheet 去重
                    all_existing_urls.update(urls)
            except Exception as e:
                print(f"⚠️ 读取 sheet '{sheet.title}' 时出错: {e}")
                continue
        
        # 过滤掉已存在的 URL（只过滤新数据，不影响现有数据）
        # 注意：这里只过滤其他 sheet 的 URL，不包含当前 sheet
        original_count = len(df)
        df = df[~df['URL'].isin(all_existing_urls)]
        if len(df) < original_count:
            print(f"📝 跨 sheet 去重：过滤掉 {original_count - len(df)} 篇已存在的文章（其他 sheet 中）")
    
    # 选择或创建 sheet
    if sheet_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            # 如果 sheet 已存在，读取现有数据
            existing_data = worksheet.get_all_values()
            if len(existing_data) > 1:
                original_row_count = len(existing_data) - 1  # 减去标题行
                existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
                
                # 保护措施：检查读取的数据量
                if len(existing_df) != original_row_count:
                    print(f"⚠️ 警告：读取的数据行数不匹配！期望 {original_row_count} 行，实际 {len(existing_df)} 行")
                
                # 确保列名和顺序匹配，避免数据丢失
                # 使用新数据的列名和顺序作为标准
                expected_columns = df.columns.tolist()
                # 如果现有数据的列名不匹配，尝试对齐
                if list(existing_df.columns) != expected_columns:
                    print(f"⚠️ 列名不匹配！现有列: {list(existing_df.columns)}, 期望列: {expected_columns}")
                    # 记录原始行数
                    before_alignment = len(existing_df)
                    # 尝试重新对齐列
                    existing_df_aligned = pd.DataFrame()
                    for col in expected_columns:
                        if col in existing_df.columns:
                            existing_df_aligned[col] = existing_df[col]
                        else:
                            existing_df_aligned[col] = None  # 缺失的列填充为 None
                    existing_df = existing_df_aligned
                    # 保护措施：检查对齐后行数是否一致
                    if len(existing_df) != before_alignment:
                        print(f"⚠️ 警告：列对齐后行数变化！对齐前 {before_alignment} 行，对齐后 {len(existing_df)} 行")
                        # 如果行数减少，尝试恢复
                        if len(existing_df) < before_alignment:
                            print(f"❌ 错误：列对齐导致数据丢失！停止操作，不清空 sheet")
                            raise ValueError(f"列对齐导致数据丢失：{before_alignment} 行 -> {len(existing_df)} 行")
                
                # 确保列顺序一致（不会导致行数减少）
                existing_df = existing_df[expected_columns]
                
                # 保护措施：最终检查
                if len(existing_df) != original_row_count:
                    print(f"❌ 错误：数据处理后行数不匹配！原始 {original_row_count} 行，处理后 {len(existing_df)} 行")
                    raise ValueError(f"数据处理导致数据丢失：{original_row_count} 行 -> {len(existing_df)} 行")
                # 合并现有数据和新数据
                # 注意：df 已经跨 sheet 去重（不包含其他 sheet 的 URL），但可能包含当前 sheet 的 URL
                # 所以需要过滤掉新数据中已在当前 sheet 存在的 URL
                if current_sheet_urls and 'URL' in df.columns:
                    before_filter = len(df)
                    df = df[~df['URL'].isin(current_sheet_urls)]
                    if len(df) < before_filter:
                        print(f"📝 当前 sheet 去重：过滤掉 {before_filter - len(df)} 篇已存在的文章（当前 sheet 中）")
                
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                # 在当前 sheet 内去重（清理 existing_df 本身可能存在的重复）
                if 'URL' in combined_df.columns:
                    before_dedup = len(combined_df)
                    # 改进：清理 URL 格式（去除空格、统一格式）避免误判为重复
                    combined_df['URL_cleaned'] = combined_df['URL'].astype(str).str.strip()
                    # 使用清理后的 URL 去重
                    combined_df = combined_df.drop_duplicates(subset=['URL_cleaned'], keep='first')
                    # 删除临时列
                    combined_df = combined_df.drop('URL_cleaned', axis=1)
                    after_dedup = len(combined_df)
                    if before_dedup > after_dedup:
                        print(f"📝 Sheet 内去重：移除 {before_dedup - after_dedup} 篇重复文章（清理现有数据中的重复）")
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
            # 确保列名和顺序匹配
            expected_columns = df.columns.tolist()
            if list(existing_df.columns) != expected_columns:
                print(f"⚠️ 列名不匹配！现有列: {list(existing_df.columns)}, 期望列: {expected_columns}")
                existing_df_aligned = pd.DataFrame()
                for col in expected_columns:
                    if col in existing_df.columns:
                        existing_df_aligned[col] = existing_df[col]
                    else:
                        existing_df_aligned[col] = None
                existing_df = existing_df_aligned
            existing_df = existing_df[expected_columns]
            # 合并现有数据和新数据
            # 注意：df 已经跨 sheet 去重，但可能包含当前 sheet 的 URL
            # 需要过滤掉新数据中已在当前 sheet 存在的 URL
            if 'URL' in df.columns:
                # 从 existing_df 中获取当前 sheet 的 URL
                current_sheet_urls_from_existing = set(existing_df['URL'].dropna()) if 'URL' in existing_df.columns else set()
                before_filter = len(df)
                df = df[~df['URL'].isin(current_sheet_urls_from_existing)]
                if len(df) < before_filter:
                    print(f"📝 当前 sheet 去重：过滤掉 {before_filter - len(df)} 篇已存在的文章（当前 sheet 中）")
            
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # 在当前 sheet 内去重（清理 existing_df 本身可能存在的重复）
            if 'URL' in combined_df.columns:
                before_dedup = len(combined_df)
                # 改进：清理 URL 格式（去除空格、统一格式）避免误判为重复
                combined_df['URL_cleaned'] = combined_df['URL'].astype(str).str.strip()
                # 使用清理后的 URL 去重
                combined_df = combined_df.drop_duplicates(subset=['URL_cleaned'], keep='first')
                # 删除临时列
                combined_df = combined_df.drop('URL_cleaned', axis=1)
                after_dedup = len(combined_df)
                if before_dedup > after_dedup:
                    print(f"📝 Sheet 内去重：移除 {before_dedup - after_dedup} 篇重复文章（清理现有数据中的重复）")
        else:
            combined_df = df.copy()
    
    # 如果没有新数据，只重新排序
    if df.empty:
        if len(existing_data) > 1:
            existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
            print(f"⚠️ 所有数据已存在（跨 sheet 去重），重新排序现有数据...")
            if sort_by_date and 'Date' in existing_df.columns:
                _sort_sheet_by_date(worksheet, existing_df, existing_data[0])
                print(f"✅ 已按日期排序完成")
            return
        else:
            print(f"⚠️ 没有新数据可追加")
            return
    
    # 保护措施：在清空 sheet 前，检查 combined_df 是否包含所有现有数据
    if len(existing_data) > 1:
        original_row_count = len(existing_data) - 1  # 减去标题行
        if len(combined_df) < original_row_count:
            print(f"❌ 错误：合并后数据量减少！原始 {original_row_count} 行，合并后 {len(combined_df)} 行")
            print(f"   停止操作，不清空 sheet，避免数据丢失")
            raise ValueError(f"合并导致数据丢失：{original_row_count} 行 -> {len(combined_df)} 行")
    
    # 按日期排序（从早到晚）
    if sort_by_date and 'Date' in combined_df.columns:
        try:
            # 尝试解析日期（支持多种格式）
            combined_df['Date_parsed'] = pd.to_datetime(
                combined_df['Date'], 
                errors='coerce',
                format='mixed'  # 支持多种日期格式
            )
            # 先按日期排序，然后删除临时列
            combined_df = combined_df.sort_values('Date_parsed', ascending=True, na_position='last')
            combined_df = combined_df.drop('Date_parsed', axis=1)
            print(f"✅ 已按日期排序（从早到晚）")
        except Exception as e:
            print(f"⚠️ 日期排序失败: {e}，使用原始顺序")
            import traceback
            traceback.print_exc()
    
    # 清空 sheet 并重新写入（保留标题行）
    worksheet.clear()
    if len(existing_data) > 0:
        worksheet.append_row(existing_data[0])  # 写入标题行
    else:
        worksheet.append_row(combined_df.columns.tolist())
    
    # 写入数据（分批写入）
    if not combined_df.empty:
        batch_size = 100
        rows_written = 0
        for i in range(0, len(combined_df), batch_size):
            batch = combined_df.iloc[i:i+batch_size]
            values = batch.values.tolist()
            worksheet.append_rows(values)
            rows_written += len(batch)
        
        # 保护措施：检查写入的数据量
        if rows_written != len(combined_df):
            print(f"⚠️ 警告：写入的数据量不匹配！期望 {len(combined_df)} 行，实际写入 {rows_written} 行")
        
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

