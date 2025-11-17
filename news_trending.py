#!/usr/bin/env python3
"""
新闻热点榜功能
识别相似新闻，按类别分组，统计报道数量
"""
import pandas as pd
from collections import defaultdict
import re
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Optional

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

def are_similar_articles_api(
    headline1: str,
    nut1: str,
    headline2: str,
    nut2: str,
    outlet1: str = "",
    outlet2: str = "",
    date1: str = "",
    date2: str = "",
) -> Optional[bool]:
    """
    使用 OpenAI API 判断两篇文章是否相似（同一事件的不同报道）
    
    Returns:
        True: 相似（同一事件）
        False: 不相似（不同事件）
        None: API 不可用或失败，使用文本相似度回退
    """
    try:
        import os
        from openai import OpenAI
        
        # 从环境变量或 Streamlit secrets 获取 API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "api" in st.secrets:
                    api_key = st.secrets.get("api", {}).get("openai_api_key")
            except:
                pass
        
        if not api_key:
            return None
        
        # 检查预算（使用 api_classifier 的预算控制）
        try:
            from api_classifier import _budget_allows_call, _record_call
            if not _budget_allows_call():
                return None
        except ImportError:
            pass
        
        client = OpenAI(api_key=api_key)
        
        # 构建改进的 prompt（更好地识别地缘政治相关新闻）
        prompt = f"""You are a news analysis assistant. Determine if these two news articles are about the same event/story, even if reported by different outlets.

**IMPORTANT**: Articles about the same geopolitical event should be grouped together, even if they focus on different aspects or use different wording.

Examples of articles that should be grouped:
- "China-Japan tensions over Taiwan" and "Japan-China relations strained by Taiwan issue" → YES (same event, different wording)
- "China rolls out red carpet for Thailand's king" and "Thailand's king visits China" → YES (same event)
- "US-China trade talks resume" and "Bilateral trade negotiations between US and China" → YES (same event)

Article 1:
Headline: {headline1}
Summary: {nut1}
Outlet: {outlet1}
Date: {date1}

Article 2:
Headline: {headline2}
Summary: {nut2}
Outlet: {outlet2}
Date: {date2}

Are these two articles about the same event/story? Consider:
- Same core event/fact (even if reported from different angles)
- Same time period (within a few days)
- Same key actors/entities (e.g., China, Japan, Taiwan, US, etc.)
- Same geopolitical context (e.g., Taiwan tensions, trade disputes, diplomatic visits)
- Different outlets may report the same story differently (different wording, different focus)
- Articles about the same topic but different aspects should still be grouped (e.g., "China-Japan tensions" and "Japan-China relations strained")

Respond with ONLY "yes" or "no", nothing else."""
        
        # 从环境变量或 Streamlit secrets 获取模型
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "api" in st.secrets:
                model = st.secrets.get("api", {}).get("openai_model", model)
        except:
            pass
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a news analysis assistant. Respond with only 'yes' or 'no'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        # 记录 API 调用
        try:
            from api_classifier import _record_call
            _record_call()
        except:
            pass
        
        # 添加延迟避免 rate limit
        # Trending news 可能有很多次调用，需要更保守的延迟
        import time
        time.sleep(0.2)  # 200ms delay between requests (more conservative for trending)
        
        if "yes" in result:
            return True
        elif "no" in result:
            return False
        else:
            # 如果返回格式不对，返回 None 使用文本相似度回退
            return None
            
    except ImportError:
        return None
    except Exception as e:
        # API 调用失败，返回 None 使用文本相似度回退
        print(f"⚠️ API similarity check failed: {e}")
        return None

def are_similar_articles(row1: pd.Series, row2: pd.Series, threshold: float = 0.7, use_api: bool = True, api_threshold: float = 0.4) -> bool:
    """
    判断两篇文章是否相似（同一事件的不同报道）
    
    使用混合策略：先用文字相似度快速筛选，只有"可能相似"的才用 API 确认
    
    Args:
        row1, row2: 文章数据
        threshold: 文字相似度阈值（高于此值直接判断为相似）
        use_api: 是否使用 API 判断
        api_threshold: API 筛选阈值（只有文字相似度 > 此值的才用 API 确认）
    """
    # 提取标题和内容
    headline1 = str(row1.get('Headline', ''))
    headline2 = str(row2.get('Headline', ''))
    nut1 = str(row1.get('Nut Graph', ''))
    nut2 = str(row2.get('Nut Graph', ''))
    outlet1 = str(row1.get('Outlet', ''))
    outlet2 = str(row2.get('Outlet', ''))
    date1 = str(row1.get('Date', ''))
    date2 = str(row2.get('Date', ''))
    
    # ============ 混合策略 ============
    # 步骤 1: 先用文字相似度快速筛选
    headline_sim = similarity_score(headline1, headline2)
    
    # 如果标题相似度很低，直接判断为不相似（快速排除）
    if headline_sim < 0.3:
        return False
    
    # 如果标题相似度很高，直接判断为相似（无需 API）
    if headline_sim >= threshold:
        return True
    
    # 计算组合文字相似度
    text1 = f"{headline1} {nut1}"
    text2 = f"{headline2} {nut2}"
    combined_sim = similarity_score(text1, text2)
    
    # 如果组合相似度很低，直接判断为不相似
    if combined_sim < 0.3:
        return False
    
    # 如果组合相似度很高，直接判断为相似（无需 API）
    if combined_sim >= threshold:
        return True
    
    # 步骤 2: 中间地带（0.4 - 0.7）- 用 API 确认
    # 只对"较可能相似"的文章才用 API，进一步减少 API 调用
    # 降低 api_threshold 从 0.45 到 0.40，让更多边界情况使用 API 判断（提高地缘政治新闻识别）
    if use_api and combined_sim >= max(api_threshold, 0.40):
        api_result = are_similar_articles_api(
            headline1, nut1, headline2, nut2,
            outlet1, outlet2, date1, date2
        )
        if api_result is not None:
            return api_result
    
    # 步骤 3: 如果 API 不可用或失败，使用文字相似度
    return combined_sim >= threshold

def group_similar_news(df: pd.DataFrame, similarity_threshold: float = 0.7, min_group_size: int = 2, use_api: bool = True) -> pd.DataFrame:
    """
    将相似新闻分组（按类别分组，然后在每个类别内进行相似度检查）
    
    Returns:
        DataFrame with 'GroupID' column indicating which articles are similar
    """
    if df.empty:
        return df
    
    df = df.copy()
    df['GroupID'] = -1
    
    # 重置索引以便追踪
    df = df.reset_index(drop=True)
    
    # 先按类别分组，然后在每个类别内进行相似度检查
    # 这样可以确保同一类别内的相似文章被正确分组
    if 'Category' not in df.columns:
        # 如果没有类别列，使用全局分组
        category_groups = [('All', df)]
    else:
        # 按类别分组
        category_groups = [(cat, df[df['Category'] == cat]) for cat in df['Category'].unique()]
    
    group_id = 0
    
    # 对每个类别分别进行相似度检查
    for category, category_df in category_groups:
        if category_df.empty:
            continue
        
        # 保存原始索引
        original_indices = category_df.index.tolist()
        processed = set()
        
        # 在该类别内进行相似度检查
        for i in range(len(category_df)):
            original_i = original_indices[i]
            if original_i in processed:
                continue
            
            # 创建新组
            df.loc[original_i, 'GroupID'] = group_id
            processed.add(original_i)
            
            # 查找相似文章（只在该类别内）
            for j in range(i + 1, len(category_df)):
                original_j = original_indices[j]
                if original_j in processed:
                    continue
                
                if are_similar_articles(
                    category_df.iloc[i],
                    category_df.iloc[j],
                    threshold=similarity_threshold,
                    use_api=use_api
                ):
                    df.loc[original_j, 'GroupID'] = group_id
                    processed.add(original_j)
            
            group_id += 1
    
    return df

def generate_trending_rank(df: pd.DataFrame, top_n: int = 3, min_sources: int = 3) -> pd.DataFrame:
    """
    生成热点榜（按类别分组显示）
    
    Args:
        df: 包含 GroupID 列的 DataFrame
        top_n: 每个类别显示 top N 条新闻
        min_sources: 最少需要多少家媒体报道才算热点（默认 3）
    
    Returns:
        DataFrame with trending information
    """
    if df.empty or 'GroupID' not in df.columns:
        return pd.DataFrame()
    
    # 按类别和 GroupID 分组
    trending_news = []
    
    for category in df['Category'].unique():
        category_df = df[df['Category'] == category]
        
        # 按 GroupID 分组
        for group_id in category_df['GroupID'].unique():
            if group_id == -1:  # 跳过未分组的文章
                continue
            
            group_df = category_df[category_df['GroupID'] == group_id]
            
            # 至少需要 min_sources 家媒体报道
            if len(group_df) < min_sources:
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

