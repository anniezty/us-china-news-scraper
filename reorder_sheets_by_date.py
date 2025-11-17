#!/usr/bin/env python3
"""
重新排序 Google Sheets 中的所有 sheet，按日期排序
"""
import os
import sys
from google_sheets_integration import get_sheets_client
import pandas as pd
import gspread

# Google Sheets 配置
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "1Cltg8pq-jhtgR6_lysW-gNIe9JSKOh2vCT4Pxo7pcpA")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")

def reorder_sheet_by_date(spreadsheet_id: str, sheet_name: str, credentials_path: str = None):
    """
    重新排序指定 sheet，按日期排序（从早到晚）
    """
    try:
        client = get_sheets_client(credentials_path)
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # 读取所有数据
        existing_data = worksheet.get_all_values()
        if len(existing_data) <= 1:
            print(f"⚠️ Sheet '{sheet_name}' 没有数据，跳过")
            return False
        
        # 创建 DataFrame
        headers = existing_data[0]
        df = pd.DataFrame(existing_data[1:], columns=headers)
        
        if 'Date' not in df.columns:
            print(f"⚠️ Sheet '{sheet_name}' 没有 'Date' 列，跳过")
            return False
        
        print(f"📋 Sheet '{sheet_name}': 读取到 {len(df)} 行数据")
        
        # 按日期排序
        try:
            df['Date_parsed'] = pd.to_datetime(
                df['Date'], 
                errors='coerce',
                format='mixed'
            )
            df = df.sort_values('Date_parsed', ascending=True, na_position='last')
            df = df.drop('Date_parsed', axis=1)
            print(f"✅ 已按日期排序（从早到晚）")
        except Exception as e:
            print(f"⚠️ 日期排序失败: {e}")
            return False
        
        # 清空 sheet 并重新写入
        worksheet.clear()
        worksheet.append_row(headers)
        
        # 分批写入
        batch_size = 100
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = batch.values.tolist()
            worksheet.append_rows(values)
        
        print(f"✅ Sheet '{sheet_name}': 已重新排序并写入 {len(df)} 行数据")
        return True
        
    except gspread.exceptions.WorksheetNotFound:
        print(f"⚠️ Sheet '{sheet_name}' 不存在，跳过")
        return False
    except Exception as e:
        print(f"❌ Sheet '{sheet_name}' 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def reorder_all_sheets(spreadsheet_id: str, credentials_path: str = None):
    """
    重新排序所有 sheet
    """
    try:
        client = get_sheets_client(credentials_path)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        all_sheets = spreadsheet.worksheets()
        print(f"📊 找到 {len(all_sheets)} 个 sheet")
        print()
        
        success_count = 0
        for sheet in all_sheets:
            sheet_name = sheet.title
            print(f"处理 Sheet: {sheet_name}")
            if reorder_sheet_by_date(spreadsheet_id, sheet_name, credentials_path):
                success_count += 1
            print()
        
        print(f"✅ 完成：成功处理 {success_count}/{len(all_sheets)} 个 sheet")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not SPREADSHEET_ID:
        print("❌ 错误: 未设置 Google Sheets ID")
        print("请设置环境变量 GOOGLE_SHEETS_ID")
        sys.exit(1)
    
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ 错误: 未找到 Google 凭证文件: {CREDENTIALS_PATH}")
        print("请设置环境变量 GOOGLE_CREDENTIALS_PATH")
        sys.exit(1)
    
    print("=" * 70)
    print("🔄 开始重新排序 Google Sheets 中的所有数据")
    print("=" * 70)
    print()
    
    # 如果提供了 sheet 名称作为参数，只处理该 sheet
    if len(sys.argv) > 1:
        sheet_name = sys.argv[1]
        print(f"只处理 Sheet: {sheet_name}")
        reorder_sheet_by_date(SPREADSHEET_ID, sheet_name, CREDENTIALS_PATH)
    else:
        print("处理所有 Sheet")
        reorder_all_sheets(SPREADSHEET_ID, CREDENTIALS_PATH)
    
    print()
    print("=" * 70)
    print("✅ 完成")
    print("=" * 70)

