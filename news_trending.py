#!/usr/bin/env python3
"""
新闻热点榜功能
识别相似新闻，按类别分组，统计报道数量
"""
import pandas as pd
from collections import defaultdict
import re
from difflib import SequenceMatcher
from typing import List, Tuple, Dict

def clean_text(text: str) -> str:
    """清理文本，用于相似度比较"""
    if not text:
        return ""
    # 移除标点、转换为小写
    text = re.sub(r'[^\w\s]', '', str(text).lower())
    # 移除多余空格
    text = ' '.join(text.split())
    return text

def similarity_score(text1: str, text2: str) -> float:
    """计算两个文本的相似度（0-1）"""
    if not text1 or not text2:
        return 0.0
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)
    if not clean1 or not clean2:
        return 0.0
    return SequenceMatcher(None, clean1, clean2).ratio()

def are_similar_articles(row1: pd.Series, row2: pd.Series, threshold: float = 0.6) -> bool:
    """
    判断两篇文章是否相似（同一事件的不同报道）
    
    使用标题和 Nut Graph 的相似度
    """
    # 提取标题和内容
    headline1 = str(row1.get('Headline', ''))
    headline2 = str(row2.get('Headline', ''))
    nut1 = str(row1.get('Nut Graph', ''))
    nut2 = str(row2.get('Nut Graph', ''))
    
    # 计算标题相似度
    headline_sim = similarity_score(headline1, headline2)
    
    # 计算内容相似度（如果标题相似度不够，再检查内容）
    if headline_sim < threshold:
        # 组合标题和内容
        text1 = f"{headline1} {nut1}"
        text2 = f"{headline2} {nut2}"
        combined_sim = similarity_score(text1, text2)
        return combined_sim >= threshold
    
    return headline_sim >= threshold

def group_similar_news(df: pd.DataFrame, similarity_threshold: float = 0.6) -> pd.DataFrame:
    """
    将相似新闻分组
    
    Returns:
        DataFrame with 'GroupID' column indicating which articles are similar
    """
    if df.empty:
        return df
    
    df = df.copy()
    df['GroupID'] = -1
    
    # 重置索引以便追踪
    df = df.reset_index(drop=True)
    
    group_id = 0
    processed = set()
    
    for i in range(len(df)):
        if i in processed:
            continue
        
        # 创建新组
        df.loc[i, 'GroupID'] = group_id
        processed.add(i)
        
        # 查找相似文章
        for j in range(i + 1, len(df)):
            if j in processed:
                continue
            
            if are_similar_articles(df.iloc[i], df.iloc[j], similarity_threshold):
                df.loc[j, 'GroupID'] = group_id
                processed.add(j)
        
        group_id += 1
    
    return df

def generate_trending_rank(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """
    生成热点榜
    
    Args:
        df: 包含 GroupID 列的 DataFrame
        top_n: 每个类别显示 top N 条新闻
    
    Returns:
        DataFrame with trending information
    """
    if df.empty or 'GroupID' not in df.columns:
        return pd.DataFrame()
    
    # 按 GroupID 和 Category 分组
    trending_news = []
    
    for category in df['Category'].unique():
        category_df = df[df['Category'] == category]
        
        # 按 GroupID 分组
        for group_id in category_df['GroupID'].unique():
            group_df = category_df[category_df['GroupID'] == group_id]
            
            if len(group_df) < 2:  # 至少需要2家媒体报道
                continue
            
            # 统计信息
            source_count = len(group_df)
            outlets = group_df['Outlet'].unique().tolist()
            
            # 选择代表性的标题（最长的或第一个）
            representative = group_df.iloc[0]
            
            # 获取所有 URL
            urls = group_df['URL'].dropna().unique().tolist()
            
            # 获取日期范围
            dates = pd.to_datetime(group_df['Date'], errors='coerce').dropna()
            date_range = None
            if len(dates) > 0:
                date_range = dates.min().strftime('%Y-%m-%d')
            
            trending_news.append({
                'Category': category,
                'GroupID': group_id,
                'Headline': representative['Headline'],
                'SourceCount': source_count,
                'Outlets': ', '.join(outlets),
                'OutletList': outlets,
                'URLs': urls,
                'Date': date_range,
                'URL': urls[0] if urls else None
            })
    
    if not trending_news:
        return pd.DataFrame()
    
    trending_df = pd.DataFrame(trending_news)
    
    # 按类别和报道数量排序
    trending_df = trending_df.sort_values(
        ['Category', 'SourceCount'], 
        ascending=[True, False]
    )
    
    # 每个类别取 top N
    top_trending = []
    for category in trending_df['Category'].unique():
        category_trending = trending_df[trending_df['Category'] == category].head(top_n)
        top_trending.append(category_trending)
    
    if top_trending:
        return pd.concat(top_trending, ignore_index=True)
    else:
        return pd.DataFrame()

def format_trending_display(trending_df: pd.DataFrame) -> str:
    """格式化热点榜显示"""
    if trending_df.empty:
        return "暂无热点新闻"
    
    output = []
    current_category = None
    
    for _, row in trending_df.iterrows():
        if row['Category'] != current_category:
            current_category = row['Category']
            output.append(f"\n### 📊 {current_category}\n")
        
        output.append(f"**🔥 {row['SourceCount']} 家媒体报道**: {row['Headline'][:100]}...")
        output.append(f"   - 媒体: {row['Outlets']}")
        if row.get('Date'):
            output.append(f"   - 日期: {row['Date']}")
        output.append("")
    
    return "\n".join(output)

