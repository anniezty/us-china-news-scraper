#!/usr/bin/env python3
"""
每日定时任务：抓取数据并上传到 Google Sheets
替代原来的 SQLite 数据库方案
支持本地 cron 和 GitHub Actions
"""
from datetime import datetime, date
from collector import collect
from google_sheets_integration import export_to_sheets, export_to_sheets_append, get_sheets_client
import yaml
import os
import json

# 优先来源（每天定时收集到 Google Sheets）
# 如果设置了 PRIORITY_SOURCES_LIST 环境变量，只收集指定的来源
# 否则默认收集6个优先source（这些source更新频率高，需要定时覆盖）
RAW_PRIORITY_SOURCES = os.getenv("PRIORITY_SOURCES_LIST", "")
if RAW_PRIORITY_SOURCES:
    PRIORITY_SOURCES = [s.strip() for s in RAW_PRIORITY_SOURCES.split(",") if s.strip()]
else:
    # 默认收集6个优先source（这些source收集不全，需要定时覆盖）
    PRIORITY_SOURCES = ["nytimes.com", "scmp.com", "ft.com", "apnews.com", "washingtonpost.com", "reuters.com"]

# Google Sheets 配置（从环境变量或配置文件读取）
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")

# GitHub Actions 支持：从环境变量读取 JSON 字符串
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

def get_credentials_path():
    """获取凭证路径，支持 GitHub Actions"""
    # 如果 GitHub Actions 提供了 JSON 字符串，创建临时文件
    if GOOGLE_CREDENTIALS_JSON:
        import tempfile
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(creds_dict, temp_file)
        temp_file.close()
        return temp_file.name
    # 否则使用本地文件
    return CREDENTIALS_PATH if os.path.exists(CREDENTIALS_PATH) else None

def collect_and_upload_to_sheets(config_path: str = "config_en.yaml", 
                                 spreadsheet_id: str = None,
                                 credentials_path: str = None):
    """
    抓取当天的文章并上传到 Google Sheets
    """
    import sys
    
    # 确保所有输出都刷新到日志文件
    def log_print(*args, **kwargs):
        print(*args, **kwargs)
        sys.stdout.flush()
        sys.stderr.flush()
    
    if not spreadsheet_id:
        spreadsheet_id = SPREADSHEET_ID
    
    if not spreadsheet_id:
        log_print("❌ 错误: 未设置 Google Sheets ID")
        log_print("请设置环境变量 GOOGLE_SHEETS_ID 或在代码中指定")
        return (0, 0)
    
    # 获取凭证路径
    if not credentials_path:
        credentials_path = get_credentials_path()
    
    if not credentials_path or not os.path.exists(credentials_path):
        # 尝试使用环境变量
        if GOOGLE_CREDENTIALS_JSON:
            credentials_path = get_credentials_path()
        else:
            log_print("❌ 错误: 未找到 Google 凭证文件")
            log_print("请设置 GOOGLE_CREDENTIALS_PATH 或 GOOGLE_CREDENTIALS_JSON")
            return (0, 0)
    
    today = date.today()
    today_str = today.isoformat()
    
    log_print(f"[{datetime.now()}] 开始抓取 {today_str} 的文章...")
    log_print(f"来源: {PRIORITY_SOURCES} ({len(PRIORITY_SOURCES)} 个优先outlet)")
    
    # 抓取当天的文章（只收集6个优先source）
    df = collect(
        config_path,
        today_str,
        today_str,
        us_china_only=False,  # 收集所有文章
        limit_sources=PRIORITY_SOURCES
    )
    
    if df.empty:
        log_print(f"[{datetime.now()}] 未找到文章")
        return (0, 0)
    
    log_print(f"[{datetime.now()}] 找到 {len(df)} 篇文章")
    
    # 上传到 Google Sheets
    try:
        # 计算本周的开始日期（周一到下周一，共8天）
        from datetime import timedelta
        days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
        week_start = today - timedelta(days=days_since_monday)  # 本周一
        week_end = week_start + timedelta(days=7)  # 下周一（包含）
        
        # 使用本周日期范围作为 sheet 名称（带 Week 前缀，与现有格式一致）
        sheet_name = f"Week {week_start.isoformat()} to {week_end.isoformat()}"
        
        # 只上传需要的列
        upload_df = df[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]].copy()
        
        log_print(f"[{datetime.now()}] 正在上传到 Google Sheets: {sheet_name}...")
        # 追加模式：合并到本周的 sheet（去重）
        export_to_sheets_append(upload_df, spreadsheet_id, sheet_name, credentials_path)
        
        log_print(f"[{datetime.now()}] ✅ 成功上传 {len(upload_df)} 篇文章到 Google Sheets")
        return (len(upload_df), len(upload_df))
        
    except Exception as e:
        log_print(f"[{datetime.now()}] ❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        return (0, len(df))
    finally:
        # 清理临时文件（如果是 GitHub Actions 创建的）
        if GOOGLE_CREDENTIALS_JSON and credentials_path and credentials_path.startswith('/tmp'):
            try:
                os.unlink(credentials_path)
            except:
                pass

def create_weekly_sheet_from_range(spreadsheet_id: str, date_from: str, date_to: str,
                                   config_path: str = "config_en.yaml",
                                   credentials_path: str = None):
    """
    为指定日期范围收集数据并追加到对应的周 sheet
    
    注意：会计算日期所在的周（周一到下周一），追加到对应的周 sheet，而不是创建新 sheet
    """
    if not credentials_path:
        credentials_path = get_credentials_path()
    
    print(f"📅 处理日期范围: {date_from} 到 {date_to}")
    
    # 计算日期所在的周（周一到下周一）
    from datetime import datetime, timedelta
    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
    # 计算这周的周一
    days_since_monday = date_from_obj.weekday()  # 0=Monday, 6=Sunday
    week_start = date_from_obj - timedelta(days=days_since_monday)  # 本周一
    week_end = week_start + timedelta(days=7)  # 下周一（包含）
    
    # 使用周日期范围作为 sheet 名称（带 Week 前缀，与现有格式一致）
    sheet_name = f"Week {week_start.isoformat()} to {week_end.isoformat()}"
    print(f"📅 日期 {date_from} 属于周: {week_start} 到 {week_end}")
    print(f"📋 将追加到 sheet: {sheet_name}")
    
    # 抓取数据（使用与主函数相同的逻辑：如果设置了PRIORITY_SOURCES_LIST则限制，否则收集所有outlet）
    df = collect(
        config_path,
        date_from,
        date_to,
        us_china_only=False,
        limit_sources=PRIORITY_SOURCES  # 如果为None，则收集所有outlet
    )
    
    if df.empty:
        print("未找到文章")
        return
    
    upload_df = df[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]].copy()
    
    try:
        # 使用追加模式，追加到对应的周 sheet（不是创建新 sheet）
        export_to_sheets_append(upload_df, spreadsheet_id, sheet_name, credentials_path)
        print(f"✅ 成功追加数据到周 sheet: {sheet_name} ({len(upload_df)} 篇文章)")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        # 每周汇总模式
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=6)  # 最近 7 天
        
        if not SPREADSHEET_ID:
            print("请设置环境变量 GOOGLE_SHEETS_ID")
            sys.exit(1)
        
        create_weekly_sheet_from_range(
            SPREADSHEET_ID,
            start_date.isoformat(),
            end_date.isoformat()
        )
    else:
        # 每日模式
        new, total = collect_and_upload_to_sheets()
        print(f"\n完成: {new} 篇新文章，{total} 篇总计")
