"""
API 分类器 - 可选功能
用于未来需要更精准分类时使用
当前未启用，保留接口供未来扩展
"""
from typing import Optional
import os
import json
from datetime import date
from pathlib import Path

USAGE_TRACK_PATH = Path(
    os.getenv(
        "API_USAGE_TRACK_PATH",
        Path.home() / ".us_china_picker" / "api_usage.json"
    )
)


def _ensure_usage_dir() -> None:
    try:
        USAGE_TRACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _load_usage() -> dict:
    if not USAGE_TRACK_PATH.exists():
        return {}
    try:
        with USAGE_TRACK_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_usage(data: dict) -> None:
    try:
        _ensure_usage_dir()
        with USAGE_TRACK_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _get_budget_config() -> tuple[float, float]:
    """Get budget and cost per call from environment or Streamlit secrets."""
    budget = 0.0
    cost_per_call = 0.001  # Default: $0.001 per call
    
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "api" in st.secrets:
            api_config = st.secrets.get("api", {})
            budget_str = api_config.get("daily_budget_usd", "")
            cost_str = api_config.get("cost_per_call_usd", "")
            
            if budget_str:
                try:
                    budget = float(budget_str)
                except (ValueError, TypeError):
                    pass
            
            if cost_str:
                try:
                    cost_per_call = float(cost_str)
                except (ValueError, TypeError):
                    pass
    except:
        pass
    
    # Fallback to environment variables
    if budget == 0.0:
        budget_str = os.getenv("API_DAILY_BUDGET_USD", "").strip()
        if budget_str:
            try:
                budget = float(budget_str)
            except ValueError:
                pass
    
    if cost_per_call == 0.001:
        cost_str = os.getenv("API_COST_PER_CALL_USD", "0.001").strip()
        if cost_str:
            try:
                cost_per_call = float(cost_str)
            except ValueError:
                pass
    
    if cost_per_call <= 0:
        cost_per_call = 0.001
    
    return budget, cost_per_call

def _budget_allows_call() -> bool:
    """Return False when daily budget is depleted."""
    budget, cost_per_call = _get_budget_config()
    
    if budget <= 0:
        return True  # No budget limit
    
    usage = _load_usage()
    today = date.today().isoformat()
    calls = usage.get(today, 0)
    current_cost = calls * cost_per_call
    
    if current_cost >= budget:
        print("⚠️ API daily budget reached, skipping API classification.")
        return False
    return True

def get_budget_status() -> dict:
    """Get current budget status for display."""
    budget, cost_per_call = _get_budget_config()
    usage = _load_usage()
    today = date.today().isoformat()
    calls = usage.get(today, 0)
    current_cost = calls * cost_per_call
    
    return {
        "budget": budget,
        "cost_per_call": cost_per_call,
        "calls_today": calls,
        "cost_today": current_cost,
        "remaining": budget - current_cost if budget > 0 else float('inf'),
        "has_budget": budget > 0
    }

def estimate_cost(num_articles: int) -> dict:
    """Estimate API cost for classifying given number of articles."""
    _, cost_per_call = _get_budget_config()
    estimated_cost = num_articles * cost_per_call
    
    budget_status = get_budget_status()
    can_afford = True
    if budget_status["has_budget"]:
        remaining = budget_status["remaining"]
        can_afford = estimated_cost <= remaining
    
    return {
        "estimated_cost": estimated_cost,
        "num_articles": num_articles,
        "cost_per_call": cost_per_call,
        "can_afford": can_afford,
        "remaining_budget": budget_status["remaining"] if budget_status["has_budget"] else None
    }


def _record_call() -> None:
    try:
        usage = _load_usage()
        today = date.today().isoformat()
        usage[today] = usage.get(today, 0) + 1
        _save_usage(usage)
    except Exception:
        pass

def classify_with_api(headline: str, nut_graph: str, 
                      categories: list[str],
                      provider: str = None) -> Optional[str]:
    """
    使用 API 进行文章分类
    
    Args:
        headline: 文章标题
        nut_graph: 文章摘要
        categories: 可用类别列表
        provider: API 提供商 (openai, anthropic)，如果为 None 则自动检测
    
    Returns:
        分类名称，如果无法分类则返回 None
    """
    # Debug: Log function entry
    import sys
    print(f"🔍 classify_with_api() called: headline='{headline[:50]}...'", file=sys.stderr, flush=True)
    
    # 检查是否启用 API
    api_available = is_api_available()
    print(f"🔍 is_api_available() returned: {api_available}", file=sys.stderr, flush=True)
    if not api_available:
        print("❌ API not available, returning None", file=sys.stderr, flush=True)
        return None
    
    # 自动检测 provider（如果未指定）
    if provider is None:
        provider = os.getenv("API_PROVIDER", "openai")
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "api" in st.secrets:
                provider = st.secrets.get("api", {}).get("provider", provider)
        except:
            pass
    
    text = f"{headline}\n\n{nut_graph}"
    
    print(f"🔍 Provider: {provider}", file=sys.stderr, flush=True)
    
    if provider == "openai":
        print("🔍 Calling _classify_openai()", file=sys.stderr, flush=True)
        result = _classify_openai(text, categories)
        print(f"🔍 _classify_openai() returned: {result}", file=sys.stderr, flush=True)
        return result
    elif provider == "anthropic":
        print("🔍 Calling _classify_anthropic()", file=sys.stderr, flush=True)
        result = _classify_anthropic(text, categories)
        print(f"🔍 _classify_anthropic() returned: {result}", file=sys.stderr, flush=True)
        return result
    else:
        print(f"❌ Unknown provider: {provider}, returning None", file=sys.stderr, flush=True)
        return None

def _classify_openai(text: str, categories: list[str]) -> Optional[str]:
    """使用 OpenAI API 分类"""
    try:
        from openai import OpenAI
        
        # 从环境变量或 Streamlit secrets 获取 API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 尝试从 Streamlit secrets 读取（如果是在 Streamlit 环境中）
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "api" in st.secrets:
                    api_key = st.secrets.get("api", {}).get("openai_api_key")
            except:
                pass
        
        if not api_key:
            import sys
            print("❌ API key not found", file=sys.stderr, flush=True)
            return None
        if not _budget_allows_call():
            import sys
            print("❌ Budget limit reached, skipping API call", file=sys.stderr, flush=True)
            return None
        
        # Debug: Log API call attempt
        import sys
        print(f"🔍 Attempting API call with key: {api_key[:10]}...", file=sys.stderr, flush=True)
        
        client = OpenAI(api_key=api_key)
        
        # 构建类别说明
        category_descriptions = {
            "Administration": "US government administration, White House, Congress, Senate, House of Representatives, presidential orders, congressional actions. Focus on White House/Congress/Trump/Biden, not all agencies.",
            "Trade & Commerce": "Trade policies, tariffs, trade deals, USTR, Section 301, WTO, market access, exports, imports, supply chains between US and China.",
            "Shipping": "Shipping, ports, containers, shipbuilding, maritime logistics.",
            "Chips": "Semiconductors, chips, lithography, ASML, SMIC, TSMC, EDA, wafers, foundries, Nvidia.",
            "Science & AI": "Artificial intelligence, AI, machine learning, generative AI, foundation models, LLMs, frontier models, AI safety, AI governance, A100, H100, AI chips, ChatGPT, OpenAI, Anthropic.",
            "Tech & National Security": "Export controls, entity list, CFIUS, critical technology, cybersecurity, espionage related to technology.",
            "Biotech": "Biotechnology, biopharma, pharmaceuticals, drugs, vaccines, gene editing, CRISPR, synthetic biology, biosecurity, clinical trials, FDA, NMPA, mRNA.",
            "Climate & Energy": "Climate policy, climate targets, net zero, carbon neutrality/emissions/tax/pricing, renewable energy, clean energy, solar, photovoltaic, wind turbines, hydrogen, EVs, electric vehicles, batteries, charging infrastructure, grid modernization, energy transition.",
            "Critical Minerals": "Rare earth elements, critical minerals, lithium, cobalt, nickel, graphite.",
            "Business & Investment": "Foreign direct investment (FDI), investments, mergers, acquisitions, IPOs, private equity, venture capital, sanctions risk in business context.",
            "Digital Currencies": "Digital yuan, CBDC, stablecoins, cryptocurrency regulation.",
            "US Multilateralism": "US collaboration with other countries/blocks: G7, G20, NATO, AUKUS, Quad, IMF, World Bank, OECD, EU, ASEAN, UN, UNSC, BRICS, SCO, APEC, CPTPP, RCEP, AU, OAS, joint statements/communiqués, trilateral, multilateral, ministerial meetings.",
            "Geopolitics": "Adversarial/competition dynamics: deterrence, containment, counter-strategies, sanctions, arms sales/transfers, weapons, military aid, security pacts, alignment, rivalry, competition, great power competition, Indo-Pacific, strategic competition, confrontation.",
            "China-Russia": "China-Russia relations, Sino-Russian cooperation, Moscow, sanction evasion between China and Russia.",
            "Taiwan": "Taiwan, Taipei, Taiwan Strait, cross-strait relations, TTW (Taiwan Travel Act), TSMC in Taiwan context.",
            "Military & Maritime": "PLA (People's Liberation Army), navy, missiles, maritime patrols, gray zone operations, freedom of navigation.",
            "Influence & Espionage": "Influence operations, spies, espionage, propaganda, disinformation.",
            "China's Economy": "China's domestic economy, GDP, deflation, stimulus, property sector, real estate in China.",
            "Higher Education": "Strictly university/academic context: university/college students, professors, faculty, researchers, programs, partnerships, collaborations, funding, grants, visas, warnings, bans, cuts. Must involve university/college context.",
            "Human Rights": "Human rights issues, Xinjiang, Uyghurs, Hong Kong rights, Tibet.",
            "Fentanyl": "Fentanyl, precursors, cartels, pills, opioids.",
            "Inside China": "China's domestic politics: NPC, Party Congress, provincial policies, SOEs, regulators, State Council, local policies.",
            "Uncategorized": "Articles that don't fit into any of the above categories."
        }
        
        # 构建类别说明文本
        categories_with_desc = []
        for cat in categories:
            desc = category_descriptions.get(cat, cat)
            categories_with_desc.append(f"- {cat}: {desc}")
        categories_explanation = "\n".join(categories_with_desc)
        
        # 构建改进的提示词（包含类别说明和示例）
        prompt = f"""You are a professional news classification assistant specializing in US-China relations.

Available categories with descriptions:
{categories_explanation}

Classification rules:
1. Choose the MOST SPECIFIC category that best fits the article
2. If an article could fit multiple categories, choose the PRIMARY focus
3. If the article doesn't clearly fit any category, return "Uncategorized"
4. Pay attention to context - for example, "Higher Education" requires university/college context
5. "Administration" focuses on White House/Congress, not all government agencies

Examples (from your labeled data - 75 real examples covering all 22 categories):
- "Trump orders tariff pause after Xi makes rare call" → Administration
- "US reaches interim trade agreement with China on tariffs" → Administration
- "Trump signs executive order creating $500 billion AI infrastructure fund" → Administration
- "With potential $20B deal, Trump takes a different approach than Biden to ZTE, Huawei" → Administration
- "China biotech faces new U.S. restrictions" → Biotech
- "Chinese scientists say U.S. military has funded over 2,000 drug-resistant 'superbugs'" → Biotech
- "China's Wuxi AppTec says FDA proposed ban on its tests would harm American patients" → Business & Investment
- "Chinese EV makers still undercutting Tesla on price in Europe despite tariffs" → Business & Investment
- "China accuses McKinsey of illegally surveilling" → Business & Investment
- "America Inc. is stepping back from China" → Business & Investment
- "China turns to imports as economic malaise weighs on domestic oil" → China's Economy
- "China's economy grew 5% last year. So why is everyone complaining?" → China's Economy
- "China's factory exports soar despite Trump's tariff war" → China's Economy
- "Chinese cities slashing GDP goals" → China's Economy
- "Russia seeks deeper China energy ties to compensate for Ukraine war losses" → China-Russia
- "Where Russia and China's worldviews collide" → China-Russia
- "Moscow and Beijing strengthen their space partnership as a geopolitical challenge to the West" → China-Russia
- "Russian firms seek Chinese help to skirt Western export controls" → China-Russia
- "U.S. export controls on AI chips are riddled with loopholes" → Chips
- "Tiny Dutch company key to America's chip war with China" → Chips
- "U.S. expands chips ban to China" → Chips
- "China now makes most of the world's gallium but can't use it in advanced chips" → Chips
- "Analysis: U.S. lead in clean-tech manufacturing is fading" → Climate & Energy
- "China's BYD and Huawei team up to build more EVs, in bid to take over the world" → Climate & Energy
- "Opinion: How Trump is making China green and America dirty" → Climate & Energy
- "Trump reportedly set to kill off EV tax credit" → Climate & Energy
- "Copper trade shows China is gearing up for fight with Trump" → Critical Minerals
- "Can America reduce its dependence on Chinese-made batteries?" → Critical Minerals
- "Unplugged: The rise of China's battery supremacy" → Critical Minerals
- "A 2,000-page report on China's role in African cobalt mining reveals the next front in the U.S.-China competition for strategic minerals" → Critical Minerals
- "China could use digital yuan to evade U.S. sanctions" → Digital Currencies
- "China begins crackdown on crypto" → Digital Currencies
- "As fentanyl crisis rages, Congress wants China's help" → Fentanyl
- "Biden's outreach to China on fentanyl has produced results, but much more needs to be done" → Fentanyl
- "Russia's war tests limits of China's global ambitions" → Geopolitics
- "China to showcase deepening Russia ties at WWII parade" → Geopolitics
- "Beijing's bad bet on Russia" → Geopolitics
- "Vietnam and Philippines seek to counter Beijing through cooperation" → Geopolitics
- "Universities reject House requests for information on foreign ties, citing 'chilling effect'" → Higher Education
- "MIT suspends deal with Chinese AI institute" → Higher Education
- "Chinese national charged with economic espionage while studying in the U.S." → Higher Education
- "Opinion: America has to get real about the Hong Kong protests" → Human Rights
- "US sanctions four Chinese and Hong Kong officials linked to crackdown" → Human Rights
- "Chinese influence operations are evolving. Here's how." → Influence & Espionage
- "How China is taking over international organizations, quietly" → Influence & Espionage
- "What Microsoft's breach tells us about China's hacking strategy" → Influence & Espionage
- "China takes on a bigger role in Africa's security problems" → Influence & Espionage
- "China's leaders meet, scrambling to shore up economy" → Inside China
- "How China uses propaganda to boost its international image" → Inside China
- "China cracks down on illegal fundraising" → Inside China
- "China's stimulus pledges face credibility problem" → Inside China
- "US-China military dialogue shows signs of life" → Military & Maritime
- "China launches third aircraft carrier" → Military & Maritime
- "Chinese military conducts drills around Taiwan after US congressman's visit" → Military & Maritime
- "Navy plans to homeport new Virginia-class submarine in Guam" → Military & Maritime
- "China claims breakthrough in quantum computing" → Science & AI
- "U.S. and China are racing to develop AI. The stakes are high." → Science & AI
- "How China pulled so far ahead on industrial policy" → Science & AI
- "China sends large fleet to escort ships through contested waters" → Shipping
- "Why China is building up its bulk carrier fleet" → Shipping
- "China's port infrastructure investments in Africa are surging" → Shipping
- "Taiwan tensions simmer as China again flies warplanes nearby" → Taiwan
- "Tsai visits U.S. ally in Pacific amid China pressure" → Taiwan
- "Biden signs bill boosting US support for Taiwan's WHO status" → Taiwan
- "Opinion: Taiwan's democracy is under assault from within and without" → Taiwan
- "U.S. and allies try to build firewall against Chinese hacking" → Tech & National Security
- "Justice Department cracks down on Chinese telecom fraud schemes" → Tech & National Security
- "China's grip on supply chain for AI chips extends to Texas factory" → Trade & Commerce
- "U.S. moves to block imports of goods made with Chinese forced labor" → Trade & Commerce
- "Trump imposes 145% tariff on Chinese-made goods" → Trade & Commerce
- "How Trump's tariffs could reshape the global economy" → Trade & Commerce
- "NATO leaders to focus on shared challenges from China" → US Multilateralism
- "Japan-Australia defense pact sends message to China" → US Multilateralism
- "U.S. and allies announce new sanctions on Chinese firms" → US Multilateralism
- "Blinken rallies partners in Pacific against China" → US Multilateralism

Article to classify:
{text}

Return ONLY the category name, nothing else. If unsure, return "Uncategorized".
"""
        
        # 从环境变量或 Streamlit secrets 获取模型
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "api" in st.secrets:
                model = st.secrets.get("api", {}).get("openai_model", model)
        except:
            pass
        
        # Make actual API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的新闻分类助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        
        # Record API call (for budget tracking)
        # Note: In Streamlit Cloud, the file system is temporary, so budget tracking
        # may reset on each deployment/restart. This is expected behavior.
        try:
            _record_call()
        except Exception as e:
            # Silently fail budget tracking if file system is not available
            # (e.g., in Streamlit Cloud with temporary file system)
            pass
        
        # Debug: Log successful API call
        import sys
        print(f"✅ API call successful: result='{result}'", file=sys.stderr, flush=True)
        
        # Add adaptive delay to avoid hitting TPM rate limits
        # 200,000 TPM = ~3,333 tokens/second = ~6-7 requests/second
        # For small batches (< 100), use shorter delay
        # For large batches (>= 100), use longer delay to be safer
        import time
        # Default: 150ms for safety, but can be reduced for small batches
        # This balances speed vs. rate limit risk
        time.sleep(0.15)  # 150ms delay between requests
        
        # 验证结果是否在类别列表中
        if result in categories:
            return result
        elif result == "Uncategorized":
            return "Uncategorized"
        else:
            # Debug: Log invalid result
            import sys
            print(f"⚠️ API returned invalid category: '{result}' (not in categories list)", file=sys.stderr, flush=True)
            return None
            
    except ImportError:
        import sys
        print("❌ OpenAI SDK not installed, run: pip install openai", file=sys.stderr, flush=True)
        return None
    except Exception as e:
        import sys
        import traceback
        error_msg = f"❌ OpenAI API call failed: {e}"
        print(error_msg, file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        return None

def _classify_anthropic(text: str, categories: list[str]) -> Optional[str]:
    """使用 Anthropic API 分类"""
    try:
        from anthropic import Anthropic
        
        # 从环境变量或 Streamlit secrets 获取 API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # 尝试从 Streamlit secrets 读取（如果是在 Streamlit 环境中）
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "api" in st.secrets:
                    api_key = st.secrets.get("api", {}).get("anthropic_api_key")
            except:
                pass
        
        if not api_key:
            return None
        if not _budget_allows_call():
            return None
        
        client = Anthropic(api_key=api_key)
        
        categories_str = ", ".join(categories)
        prompt = f"""请将以下新闻文章分类到最合适的类别。可用类别：{categories_str}

文章内容：
{text}

请只返回类别名称，不要其他内容。如果无法分类，返回 "Uncategorized"。
"""
        
        # 从环境变量或 Streamlit secrets 获取模型
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "api" in st.secrets:
                model = st.secrets.get("api", {}).get("anthropic_model", model)
        except:
            pass
        
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.content[0].text.strip()
        _record_call()
        
        if result in categories:
            return result
        elif result == "Uncategorized":
            return "Uncategorized"
        else:
            return None
            
    except ImportError:
        print("⚠️ Anthropic SDK 未安装，请运行: pip install anthropic")
        return None
    except Exception as e:
        print(f"⚠️ Anthropic API 调用失败: {e}")
        return None

def is_api_available() -> bool:
    """检查 API 分类是否可用"""
    # 优先从 Streamlit secrets 读取（如果存在）
    api_enabled = False
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "api" in st.secrets:
            api_config = st.secrets.get("api", {})
            # 支持字符串 "true"/"false" 或布尔值 true/false
            classifier_enabled = api_config.get("classifier_enabled", False)
            if isinstance(classifier_enabled, str):
                api_enabled = classifier_enabled.lower() == "true"
            else:
                api_enabled = bool(classifier_enabled)
    except:
        pass
    
    # 如果 Streamlit secrets 中没有，则从环境变量读取
    if not api_enabled:
        api_enabled = os.getenv("API_CLASSIFIER_ENABLED", "false").lower() == "true"
    
    if not api_enabled:
        return False
    
    # 检查 API key 是否存在
    provider = os.getenv("API_PROVIDER", "openai")
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "api" in st.secrets:
            provider = st.secrets.get("api", {}).get("provider", provider)
    except:
        pass
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "api" in st.secrets:
                    api_key = st.secrets.get("api", {}).get("openai_api_key")
            except:
                pass
        return bool(api_key)
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "api" in st.secrets:
                    api_key = st.secrets.get("api", {}).get("anthropic_api_key")
            except:
                pass
        return bool(api_key)
    
    return False

