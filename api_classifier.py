"""
API 分类器 - 可选功能
用于未来需要更精准分类时使用
当前未启用，保留接口供未来扩展
"""
from typing import Optional
import os

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
    # 检查是否启用 API
    if not is_api_available():
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
    
    if provider == "openai":
        return _classify_openai(text, categories)
    elif provider == "anthropic":
        return _classify_anthropic(text, categories)
    else:
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
            return None
        
        client = OpenAI(api_key=api_key)
        
        # 构建提示词
        categories_str = ", ".join(categories)
        prompt = f"""请将以下新闻文章分类到最合适的类别。可用类别：{categories_str}

文章内容：
{text}

请只返回类别名称，不要其他内容。如果无法分类，返回 "Uncategorized"。
"""
        
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
                {"role": "system", "content": "你是一个专业的新闻分类助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        
        # 验证结果是否在类别列表中
        if result in categories:
            return result
        elif result == "Uncategorized":
            return "Uncategorized"
        else:
            return None
            
    except ImportError:
        print("⚠️ OpenAI SDK 未安装，请运行: pip install openai")
        return None
    except Exception as e:
        print(f"⚠️ OpenAI API 调用失败: {e}")
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

