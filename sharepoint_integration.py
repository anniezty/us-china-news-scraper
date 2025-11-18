#!/usr/bin/env python3
"""
SharePoint 集成
自动将数据导出到 SharePoint List
支持实时读取和写入
"""
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from typing import Optional, List, Dict, Any

try:
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.listitems.listitem import ListItem
    HAS_SHAREPOINT = True
except ImportError:
    HAS_SHAREPOINT = False
    print("⚠️ Office365-REST-Python-Client not installed. Install with: pip install Office365-REST-Python-Client")


def get_sharepoint_client(site_url: str = None, username: str = None, password: str = None):
    """
    获取 SharePoint 客户端
    
    支持多种凭证来源（按优先级）：
    1. Streamlit Secrets（如果在 Streamlit 环境中）
    2. 环境变量
    3. 参数传入
    
    Args:
        site_url: SharePoint 站点 URL（例如：https://yourcompany.sharepoint.com/sites/YourSite）
        username: 用户名（公司邮箱）
        password: 密码或应用密码
    
    Returns:
        ClientContext: SharePoint 客户端上下文
    """
    if not HAS_SHAREPOINT:
        raise ImportError("Office365-REST-Python-Client not installed. Install with: pip install Office365-REST-Python-Client")
    
    # 方式 1: 尝试从 Streamlit Secrets 读取
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            if 'sharepoint' in st.secrets:
                sp_config = st.secrets.get('sharepoint', {})
                site_url = site_url or sp_config.get('site_url')
                username = username or sp_config.get('username')
                password = password or sp_config.get('password')
    except (ImportError, AttributeError):
        pass
    
    # 方式 2: 从环境变量读取
    if not site_url:
        site_url = os.getenv("SHAREPOINT_SITE_URL")
    if not username:
        username = os.getenv("SHAREPOINT_USERNAME")
    if not password:
        password = os.getenv("SHAREPOINT_PASSWORD")
    
    if not all([site_url, username, password]):
        raise ValueError(
            "SharePoint 凭证未找到\n"
            "请选择以下方式之一：\n"
            "1. 在 Streamlit Secrets 中配置 sharepoint.site_url, username, password\n"
            "2. 设置环境变量 SHAREPOINT_SITE_URL, SHAREPOINT_USERNAME, SHAREPOINT_PASSWORD\n"
            "3. 通过函数参数传入"
        )
    
    # 创建认证上下文
    ctx_auth = AuthenticationContext(site_url)
    if ctx_auth.acquire_token_for_user(username, password):
        ctx = ClientContext(site_url, ctx_auth)
        return ctx
    else:
        raise ValueError("SharePoint 认证失败，请检查用户名和密码")


def create_list_if_not_exists(ctx: ClientContext, list_name: str, list_description: str = "US-China News Articles"):
    """
    如果 SharePoint List 不存在，则创建它
    
    Args:
        ctx: SharePoint 客户端上下文
        list_name: List 名称
        list_description: List 描述
    """
    try:
        # 尝试获取现有的 List
        target_list = ctx.web.lists.get_by_title(list_name)
        ctx.load(target_list)
        ctx.execute_query()
        print(f"✅ SharePoint List '{list_name}' 已存在")
        return target_list
    except:
        # List 不存在，创建它
        list_creation_information = {
            "Title": list_name,
            "Description": list_description,
            "BaseTemplate": 100  # Custom List
        }
        
        target_list = ctx.web.lists.add(list_creation_information)
        ctx.execute_query()
        
        # 添加字段
        fields_to_add = [
            {"InternalName": "Title", "FieldTypeKind": 2, "Required": True},  # Text
            {"InternalName": "URL", "FieldTypeKind": 2, "Required": True},  # Text
            {"InternalName": "Date", "FieldTypeKind": 4},  # DateTime
            {"InternalName": "Outlet", "FieldTypeKind": 2},  # Text
            {"InternalName": "Headline", "FieldTypeKind": 2},  # Text
            {"InternalName": "NutGraph", "FieldTypeKind": 2},  # Text (Note)
            {"InternalName": "Category", "FieldTypeKind": 2},  # Text
            {"InternalName": "Nested", "FieldTypeKind": 2},  # Text (Yes/No as text)
        ]
        
        for field_info in fields_to_add:
            try:
                field_creation_information = {
                    "Title": field_info["InternalName"],
                    "FieldTypeKind": field_info["FieldTypeKind"],
                    "Required": field_info.get("Required", False)
                }
                target_list.fields.add_field_as_xml(field_creation_information)
            except:
                pass  # 字段可能已存在
        
        ctx.execute_query()
        print(f"✅ 已创建 SharePoint List '{list_name}'")
        return target_list


def export_to_sharepoint(df: pd.DataFrame, list_name: str, site_url: str = None, 
                        username: str = None, password: str = None, 
                        clear_existing: bool = False):
    """
    导出 DataFrame 到 SharePoint List
    
    Args:
        df: 要导出的 DataFrame
        list_name: SharePoint List 名称
        site_url: SharePoint 站点 URL
        username: 用户名
        password: 密码
        clear_existing: 是否清空现有数据（默认 False，追加模式）
    """
    if not HAS_SHAREPOINT:
        raise ImportError("Office365-REST-Python-Client not installed")
    
    ctx = get_sharepoint_client(site_url, username, password)
    
    # 确保 List 存在
    target_list = create_list_if_not_exists(ctx, list_name)
    
    # 清空现有数据（如果需要）
    if clear_existing:
        items = target_list.items
        ctx.load(items)
        ctx.execute_query()
        for item in items:
            item.delete_object()
        ctx.execute_query()
        print(f"✅ 已清空 SharePoint List '{list_name}'")
    
    # 映射 DataFrame 列到 SharePoint 字段
    field_mapping = {
        "URL": "URL",
        "Date": "Date",
        "Outlet": "Outlet",
        "Headline": "Headline",
        "Nut Graph": "NutGraph",
        "Category": "Category",
        "Nested?": "Nested"
    }
    
    # 添加数据
    added_count = 0
    for _, row in df.iterrows():
        try:
            item_properties = {
                "Title": str(row.get("Headline", ""))[:255]  # Title 字段是必需的，限制 255 字符
            }
            
            # 添加其他字段
            for df_col, sp_field in field_mapping.items():
                if df_col in row:
                    value = row[df_col]
                    if pd.notna(value):
                        # 处理日期字段
                        if df_col == "Date" and isinstance(value, (pd.Timestamp, datetime)):
                            item_properties[sp_field] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                        else:
                            item_properties[sp_field] = str(value)
            
            target_list.add_item(item_properties)
            added_count += 1
        except Exception as e:
            print(f"⚠️ 添加项目失败: {e}")
            continue
    
    ctx.execute_query()
    print(f"✅ 已添加 {added_count} 个项目到 SharePoint List '{list_name}'")
    return added_count


def read_from_sharepoint(list_name: str, site_url: str = None, 
                         username: str = None, password: str = None,
                         date_from: datetime = None, date_to: datetime = None,
                         selected_outlets: List[str] = None) -> pd.DataFrame:
    """
    从 SharePoint List 读取数据
    
    Args:
        list_name: SharePoint List 名称
        site_url: SharePoint 站点 URL
        username: 用户名
        password: 密码
        date_from: 开始日期（可选）
        date_to: 结束日期（可选）
        selected_outlets: 选中的 outlets（可选）
    
    Returns:
        pd.DataFrame: 读取的数据
    """
    if not HAS_SHAREPOINT:
        raise ImportError("Office365-REST-Python-Client not installed")
    
    ctx = get_sharepoint_client(site_url, username, password)
    
    try:
        target_list = ctx.web.lists.get_by_title(list_name)
        items = target_list.items
        ctx.load(items)
        ctx.execute_query()
        
        # 转换为 DataFrame
        rows = []
        for item in items:
            row = {
                "URL": item.properties.get("URL", ""),
                "Date": item.properties.get("Date", ""),
                "Outlet": item.properties.get("Outlet", ""),
                "Headline": item.properties.get("Headline", ""),
                "Nut Graph": item.properties.get("NutGraph", ""),
                "Category": item.properties.get("Category", ""),
                "Nested?": item.properties.get("Nested", ""),
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # 应用过滤
        if not df.empty:
            # 日期过滤
            if date_from or date_to:
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                    if date_from:
                        df = df[df["Date"] >= date_from]
                    if date_to:
                        df = df[df["Date"] <= date_to]
            
            # Outlet 过滤
            if selected_outlets:
                if "Outlet" in df.columns:
                    df = df[df["Outlet"].isin(selected_outlets)]
        
        return df
    except Exception as e:
        print(f"⚠️ 读取 SharePoint List 失败: {e}")
        return pd.DataFrame()


def export_to_sharepoint_append(df: pd.DataFrame, list_name: str, site_url: str = None,
                               username: str = None, password: str = None,
                               deduplicate: bool = True):
    """
    追加数据到 SharePoint List（支持去重）
    
    Args:
        df: 要导出的 DataFrame
        list_name: SharePoint List 名称
        site_url: SharePoint 站点 URL
        username: 用户名
        password: 密码
        deduplicate: 是否去重（基于 URL）
    """
    if not HAS_SHAREPOINT:
        raise ImportError("Office365-REST-Python-Client not installed")
    
    ctx = get_sharepoint_client(site_url, username, password)
    
    # 确保 List 存在
    target_list = create_list_if_not_exists(ctx, list_name)
    
    # 如果启用去重，先读取现有数据
    existing_urls = set()
    if deduplicate and 'URL' in df.columns:
        try:
            items = target_list.items
            ctx.load(items)
            ctx.execute_query()
            for item in items:
                url = item.properties.get("URL", "")
                if url:
                    existing_urls.add(url)
        except:
            pass
        
        # 过滤掉已存在的 URL
        original_count = len(df)
        df = df[~df['URL'].isin(existing_urls)]
        if len(df) < original_count:
            print(f"📝 去重：过滤掉 {original_count - len(df)} 篇已存在的文章")
    
    # 添加新数据
    return export_to_sharepoint(df, list_name, site_url, username, password, clear_existing=False)

