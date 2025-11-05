import streamlit as st
from datetime import date, datetime
import pandas as pd
import yaml, io
from utils import compile_or_regex
from openpyxl.utils import get_column_letter
import os

# Try to import Google Sheets features
try:
    from google_sheets_integration import read_from_sheets, export_to_sheets
    from collector import collect as collect_rss
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    from collector import collect as collect_rss

st.set_page_config(page_title="U.S.-China News Scraper", layout="wide")

st.markdown("## U.S.-China News Scraper")

# Load config and categories
with open("config_en.yaml","r",encoding="utf-8") as f:
    CFG = yaml.safe_load(f) or {}
with open("categories_en.yaml","r",encoding="utf-8") as f:
    CATS = yaml.safe_load(f) or {}
CATEGORIES = CATS.get("categories", {})

# Source multiselect (domain keys from config)
all_sources = list(CFG.get("rss_feeds", {}).keys())
col1, col2 = st.columns([1,1])
with col1:
    start_date = st.date_input("Start date", value=date.today() - pd.Timedelta(days=7))
with col2:
    end_date = st.date_input("End date (<= today)", value=date.today(), min_value=date(2000,1,1), max_value=date.today())
selected_sources = st.multiselect("Sources (whitelist)", options=all_sources, default=all_sources)

# Google Sheets configuration
use_sheets_db = False
spreadsheet_id = None
if HAS_SHEETS:
    st.markdown("---")
    st.markdown("### 📊 Data sources")
    use_sheets_db = st.checkbox("Read historical data from Google Sheets (NYT, SCMP, Reuters)", value=True)
    if use_sheets_db:
        spreadsheet_id = st.text_input(
            "Google Sheets ID", 
            value=os.getenv("GOOGLE_SHEETS_ID", ""),
            placeholder="Paste the ID from your Google Sheets URL",
            help="e.g. https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
        )
        
        if spreadsheet_id:
            st.info("✅ Will read historical data for NYT, SCMP, Reuters from Google Sheets")

run = st.button("Generate & Export", type="primary")

if run:
    if end_date > date.today():
        st.error("End date cannot be in the future.")
    elif start_date > end_date:
        st.error("Start date must be before end date.")
    else:
        with st.spinner("Collecting articles..."):
            # 1. 从 Google Sheets 读取历史数据（如果启用）
            sheets_df = pd.DataFrame()
            if use_sheets_db and spreadsheet_id and HAS_SHEETS:
                try:
                    st.info("📖 Reading historical data from Google Sheets...")
                    # 尝试读取多个可能的 sheet
                    # 简化：读取所有数据，然后过滤日期
                    # 实际可以优化为只读取相关 sheet
                    priority_sources = ["nytimes.com", "scmp.com", "reuters.com"]
                    
                    # 尝试读取所有以 "Week" 开头的 sheet，合并数据
                    try:
                        # 读取所有 Week sheet 的数据
                        import gspread
                        from google.oauth2.service_account import Credentials
                        from google_sheets_integration import get_sheets_client
                        
                        client = get_sheets_client(credentials_path=None)
                        spreadsheet = client.open_by_key(spreadsheet_id)
                        
                        all_sheets_data = []
                        for sheet in spreadsheet.worksheets():
                            # 只读取以 "Week" 开头的 sheet
                            if sheet.title.startswith("Week"):
                                try:
                                    data = sheet.get_all_values()
                                    if len(data) > 1:  # 有数据（标题+数据）
                                        df_part = pd.DataFrame(data[1:], columns=data[0])
                                        all_sheets_data.append(df_part)
                                except Exception as e:
                                    st.warning(f"⚠️ Error reading sheet '{sheet.title}': {e}")
                        
                        # 合并所有 sheet 的数据
                        if all_sheets_data:
                            sheets_df = pd.concat(all_sheets_data, ignore_index=True)
                        else:
                            sheets_df = pd.DataFrame()
                        
                        if not sheets_df.empty and 'Date' in sheets_df.columns:
                            # 过滤日期范围
                            sheets_df['Date'] = pd.to_datetime(sheets_df['Date'], errors='coerce')
                            # 处理日期范围：如果只有日期（没有时间），end_date 应该包含当天的所有时间
                            date_from_dt = pd.to_datetime(start_date).normalize()  # 设置为 00:00:00
                            date_to_dt = pd.to_datetime(end_date).normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # 设置为 23:59:59
                            sheets_df = sheets_df[
                                (sheets_df['Date'] >= date_from_dt) & 
                                (sheets_df['Date'] <= date_to_dt)
                            ]
                            # 确保列名一致
                            if 'Nested?' not in sheets_df.columns:
                                sheets_df['Nested?'] = ''
                            st.success(f"✅ Loaded {len(sheets_df)} historical rows from Google Sheets")
                    except Exception as e:
                        st.warning(f"⚠️ Unable to read Google Sheets: {e}")
                        sheets_df = pd.DataFrame()
                except Exception as e:
                    st.warning(f"⚠️ Failed to read Google Sheets: {e}")
            
            # 2. 从 RSS 实时抓取所有来源
            st.info("🌐 Fetching from RSS in real time...")
            rss_df = collect_rss(
                "config_en.yaml", 
                start_date.isoformat(), 
                end_date.isoformat(), 
                us_china_only=False, 
                limit_sources=selected_sources
            )
            
            # 3. 合并数据
            if not sheets_df.empty and not rss_df.empty:
                # 确保列名一致
                required_cols = ["Nested?","URL","Date","Outlet","Headline","Nut Graph"]
                for col in required_cols:
                    if col not in sheets_df.columns:
                        sheets_df[col] = ""
                    if col not in rss_df.columns:
                        rss_df[col] = ""
                
                # 合并
                df = pd.concat([sheets_df[required_cols], rss_df[required_cols]], ignore_index=True)
                # 去重（按 URL）
                df = df.drop_duplicates(subset=['URL'], keep='first')
                st.success(f"✅ Merged: Google Sheets ({len(sheets_df)}) + RSS ({len(rss_df)}) = total {len(df)} (deduplicated)")
            elif not sheets_df.empty:
                df = sheets_df
                st.success(f"✅ Using Google Sheets data: {len(df)} rows")
            elif not rss_df.empty:
                df = rss_df
                st.success(f"✅ Using RSS data: {len(rss_df)} rows")
            else:
                df = pd.DataFrame()
                st.warning("No articles found")

        if not df.empty:
            # Assign single category per article (first matched)
            compiled = []
            for cat, patt in CATEGORIES.items():
                try:
                    compiled.append((cat, compile_or_regex([patt])))
                except Exception:
                    continue

            def assign_category(row):
                # 尝试使用 API 分类（如果启用）
                try:
                    from api_classifier import classify_with_api, is_api_available
                    if is_api_available():
                        category_list = [cat for cat, _ in compiled] + ["Uncategorized"]
                        api_cat = classify_with_api(
                            row.get('Headline', ''),
                            row.get('Nut Graph', ''),
                            category_list
                        )
                        if api_cat:
                            return api_cat
                except ImportError:
                    pass  # API 分类器未安装，使用正则
                
                # 使用正则表达式分类（默认）
                text = f"{row.get('Headline','')} || {row.get('Nut Graph','')}"
                for cat, rgx in compiled:
                    if rgx.search(text):
                        return cat
                return "Uncategorized"

            df = df.copy()
            df["Category"] = df.apply(assign_category, axis=1)

            # Per-category counts (two-column layout)
            st.markdown("### 📊 Summary")
            
            # 计算总数
            total = len(df)
            unc = df[df["Category"] == "Uncategorized"]
            unc_count = len(unc) if not unc.empty else 0
            
            # 只显示两个关键指标
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📰 Total Articles", total)
            
            with col2:
                st.metric("📂 Categories", len(compiled))
            
            # By category (two columns)
            st.markdown("---")
            st.markdown("#### 📋 By Category")
            
            # 按数量排序
            category_counts = []
            for cat, _ in compiled:
                sub = df[df["Category"] == cat]
                category_counts.append((cat, len(sub)))
            category_counts.sort(key=lambda x: x[1], reverse=True)
            
            # 两列显示
            cols = st.columns(2)
            for idx, (cat, count) in enumerate(category_counts):
                col_idx = idx % 2
                with cols[col_idx]:
                    # Percentage
                    percentage = (count / total * 100) if total > 0 else 0
                    # Progress bar visualization
                    st.markdown(f"**{cat}**")
                    st.progress(min(count / total, 1.0) if total > 0 else 0)
                    st.caption(f"{count} articles ({percentage:.1f}%)")
            
            # Uncategorized 单独显示
            if unc_count > 0:
                st.markdown("---")
                st.markdown(f"**Uncategorized**: {unc_count} articles ({(unc_count/total*100):.1f}%)")
                st.progress(min(unc_count / total, 1.0) if total > 0 else 0)
            
            # Trending (Hot list)
            st.markdown("---")
            st.markdown("## 🔥 Trending News")
            st.markdown("Top stories covered by multiple sources (grouped by category)")
            
            try:
                from news_trending import group_similar_news, generate_trending_rank
                
                # Identify similar news and group
                with st.spinner("Analyzing trending stories..."):
                    df_with_groups = group_similar_news(df.copy(), similarity_threshold=0.6)
                    
                    # Generate trending list
                    trending_df = generate_trending_rank(df_with_groups, top_n=3)
                    
                    if not trending_df.empty:
                        # 获取所有类别
                        categories = sorted(trending_df['Category'].unique())
                        
                        # Use tabs for categories
                        if len(categories) > 1:
                            tabs = st.tabs(categories)
                            for idx, category in enumerate(categories):
                                with tabs[idx]:
                                    category_trending = trending_df[trending_df['Category'] == category]
                                    
                                    for _, row in category_trending.iterrows():
                                        with st.container():
                                            st.markdown(f"### 🔥 Reported by {row['SourceCount']} sources")
                                            st.markdown(f"**{row['Headline']}**")
                                            st.markdown(f"**Outlets**: {row['Outlets']}")
                                            if row.get('Date'):
                                                st.markdown(f"**Date**: {row['Date']}")
                                            
                                            # Show related links
                                            if row.get('URLs') and len(row['URLs']) > 0:
                                                st.markdown("**Related coverage**:")
                                                for url in row['URLs'][:5]:  # 最多显示5个链接
                                                    st.markdown(f"- [Read article]({url})")
                                            
                                            st.markdown("---")
                        else:
                            # Single category
                            category = categories[0]
                            category_trending = trending_df[trending_df['Category'] == category]
                            
                            for _, row in category_trending.iterrows():
                                with st.container():
                                    st.markdown(f"### 🔥 Reported by {row['SourceCount']} sources")
                                    st.markdown(f"**{row['Headline']}**")
                                    st.markdown(f"**Outlets**: {row['Outlets']}")
                                    if row.get('Date'):
                                        st.markdown(f"**Date**: {row['Date']}")
                                    
                                    # Show related links
                                    if row.get('URLs') and len(row['URLs']) > 0:
                                        st.markdown("**Related coverage**:")
                                        for url in row['URLs'][:5]:  # 最多显示5个链接
                                            st.markdown(f"- [Read article]({url})")
                                    
                                    st.markdown("---")
                    else:
                        st.info("No trending news (need at least 2 sources covering the same story)")
            except ImportError as e:
                st.warning(f"⚠️ Trending feature unavailable: {e}")
            except Exception as e:
                st.warning(f"⚠️ Error generating trending list: {e}")
                import traceback
                st.code(traceback.format_exc())
 
            # Build Excel in-memory
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                # All first
                df.to_excel(writer, sheet_name="All", index=False)
                # Autofit for All
                ws_all = writer.sheets.get("All")
                if ws_all is not None:
                    for col_name, max_width in [("Date", 22), ("Outlet", 18), ("Headline", 80)]:
                        if col_name in df.columns:
                            idx = list(df.columns).index(col_name) + 1
                            values = df[col_name].astype(str).tolist() if not df.empty else []
                            width = min(max(len(col_name), max((len(v) for v in values), default=0)) + 2, max_width)
                            ws_all.column_dimensions[get_column_letter(idx)].width = max(width, 10)
                # Categories (single-category assignment)
                for cat, _ in compiled:
                    sub = df[df["Category"] == cat]
                    if not sub.empty:
                        sub = sub[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]]
                        sheet = cat[:31]
                        sub.to_excel(writer, sheet_name=sheet, index=False)
                        ws = writer.sheets.get(sheet)
                        if ws is not None:
                            for col_name, max_width in [("Date", 22), ("Outlet", 18), ("Headline", 80)]:
                                if col_name in sub.columns:
                                    idx = list(sub.columns).index(col_name) + 1
                                    values = sub[col_name].astype(str).tolist()
                                    width = min(max(len(col_name), max((len(v) for v in values), default=0)) + 2, max_width)
                                    ws.column_dimensions[get_column_letter(idx)].width = max(width, 10)
                # Uncategorized
                if not unc.empty:
                    sub = unc[["Nested?","URL","Date","Outlet","Headline","Nut Graph"]]
                    sub.to_excel(writer, sheet_name="Uncategorized", index=False)
                    ws = writer.sheets.get("Uncategorized")
                    if ws is not None:
                        for col_name, max_width in [("Date", 22), ("Outlet", 18), ("Headline", 80)]:
                            if col_name in sub.columns:
                                idx = list(sub.columns).index(col_name) + 1
                                values = sub[col_name].astype(str).tolist()
                                width = min(max(len(col_name), max((len(v) for v in values), default=0)) + 2, max_width)
                                ws.column_dimensions[get_column_letter(idx)].width = max(width, 10)

            buffer.seek(0)
            default_name = f"us_china_news_{start_date}_{end_date}.xlsx"
            st.download_button("⬇️ Download Excel", data=buffer, file_name=default_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

