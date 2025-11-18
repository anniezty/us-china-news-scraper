#!/usr/bin/env python3
"""
每日定时任务：抓取数据并上传到 SharePoint List
替代 Google Sheets 方案
支持本地 cron 和 GitHub Actions
"""
from datetime import datetime, date
from collector import collect
from sharepoint_integration import export_to_sharepoint_append, get_sharepoint_client
import yaml
import os

# 优先来源（每天定时收集到 SharePoint）
RAW_PRIORITY_SOURCES = os.getenv("PRIORITY_SOURCES_LIST", "")
if RAW_PRIORITY_SOURCES:
    PRIORITY_SOURCES = [s.strip() for s in RAW_PRIORITY_SOURCES.split(",") if s.strip()]
else:
    PRIORITY_SOURCES = ["nytimes.com", "scmp.com", "ft.com", "apnews.com", "washingtonpost.com", "reuters.com"]

# SharePoint 配置（从环境变量读取）
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "")
SHAREPOINT_USERNAME = os.getenv("SHAREPOINT_USERNAME", "")
SHAREPOINT_PASSWORD = os.getenv("SHAREPOINT_PASSWORD", "")
SHAREPOINT_LIST_NAME = os.getenv("SHAREPOINT_LIST_NAME", "US-China News Articles")


def collect_and_upload_to_sharepoint(config_path: str = "config_en.yaml", 
                                     site_url: str = None,
                                     username: str = None,
                                     password: str = None,
                                     list_name: str = None):
    """
    抓取当天的文章并上传到 SharePoint List
    """
    import sys
    
    # 确保所有输出都刷新到日志文件
    def log_print(*args, **kwargs):
        print(*args, **kwargs)
        sys.stdout.flush()
        sys.stderr.flush()
    
    if not site_url:
        site_url = SHAREPOINT_SITE_URL
    if not username:
        username = SHAREPOINT_USERNAME
    if not password:
        password = SHAREPOINT_PASSWORD
    if not list_name:
        list_name = SHAREPOINT_LIST_NAME
    
    if not all([site_url, username, password, list_name]):
        log_print("❌ 错误: 未设置 SharePoint 配置")
        log_print("请设置环境变量:")
        log_print("  - SHAREPOINT_SITE_URL")
        log_print("  - SHAREPOINT_USERNAME")
        log_print("  - SHAREPOINT_PASSWORD")
        log_print("  - SHAREPOINT_LIST_NAME (可选，默认: US-China News Articles)")
        return (0, 0)
    
    today = date.today()
    today_str = today.isoformat()
    
    log_print(f"[{datetime.now()}] 开始抓取 {today_str} 的文章...")
    log_print(f"来源: {PRIORITY_SOURCES}")
    
    # 抓取当天的文章
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
    
    # 准备上传数据（只包含需要的列）
    upload_df = df[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]].copy()
    
    # 上传到 SharePoint
    try:
        log_print(f"[{datetime.now()}] 正在上传到 SharePoint List: {list_name}...")
        # 追加模式：合并到 List（去重）
        added_count = export_to_sharepoint_append(
            upload_df, 
            list_name, 
            site_url=site_url,
            username=username,
            password=password,
            deduplicate=True
        )
        
        log_print(f"[{datetime.now()}] ✅ 成功上传 {added_count} 篇文章到 SharePoint List: {list_name}")
        return (len(df), added_count)
    except Exception as e:
        log_print(f"[{datetime.now()}] ❌ 上传失败: {e}")
        import traceback
        log_print(traceback.format_exc())
        return (len(df), 0)


if __name__ == "__main__":
    collect_and_upload_to_sharepoint()

