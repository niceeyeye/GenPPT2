import json
import os
import re
from openai import OpenAI
from ..schemas import PPTContent, Slide
from dotenv import load_dotenv

# Get the path to the .env file in the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_path = os.path.join(backend_dir, ".env")

# Load environment variables
if os.path.exists(env_path):
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
else:
    print(f"Warning: .env file not found at {env_path}")

def get_client_and_model(provider: str, api_key: str = None):
    """
    Returns (client, model_name) based on provider.
    Prioritizes passed api_key, otherwise falls back to environment variables.
    """
    provider = provider.lower()
    
    # 1. OpenAI
    if provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        if not key: return None, None
        return OpenAI(api_key=key, base_url=base_url), model

    # 2. Doubao (Volcengine)
    elif provider == "doubao":
        key = api_key or os.getenv("DOUBAO_API_KEY")
        base_url = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        model = os.getenv("DOUBAO_MODEL") # e.g., ep-xxxx
        if not key: return None, None
        return OpenAI(api_key=key, base_url=base_url), model

    # 3. Qwen (DashScope)
    elif provider == "qwen":
        key = api_key or os.getenv("QWEN_API_KEY")
        base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.getenv("QWEN_MODEL", "qwen-plus")
        if not key: return None, None
        return OpenAI(api_key=key, base_url=base_url), model

    # 4. Gemini (Google)
    elif provider == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY")
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not key: return None, None
        return OpenAI(api_key=key, base_url=base_url), model
        
    return None, None

def extract_json(text: str) -> dict:
    """
    Extracts JSON from a string that might contain markdown or extra text.
    Includes simple "repair" for common LLM issues like trailing commas or unescaped newlines.
    """
    text = text.strip()
    
    # Pre-cleaning: Remove potential control characters that can break JSON
    # Keep only common printable ASCII + Chinese range
    # text = re.sub(r'[\x00-\x1F\x7F]', '', text) 

    def try_parse(s: str):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # Try removing trailing commas: [1, 2, ] -> [1, 2]
            s_fixed = re.sub(r',\s*([\]}])', r'\1', s)
            try:
                return json.loads(s_fixed)
            except:
                # Try replacing single quotes with double quotes (sometimes LLMs mess up)
                # This is risky, only do if it looks like single-quoted JSON
                # s_fixed = s.replace("'", '"')
                return None

    # 1. Try direct parsing
    res = try_parse(text)
    if res: return res

    # 2. Try to find JSON block in markdown
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        res = try_parse(match.group(1).strip())
        if res: return res
    
    # 3. Try to find the first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        res = try_parse(json_str)
        if res: return res
        
        # 4. If still fails, it might be truncated (missing closing braces)
        # Try to balance braces
        temp_str = json_str
        open_braces = temp_str.count('{')
        close_braces = temp_str.count('}')
        open_brackets = temp_str.count('[')
        close_brackets = temp_str.count(']')
        
        while open_brackets > close_brackets:
            temp_str += ']'
            close_brackets += 1
        while open_braces > close_braces:
            temp_str += '}'
            close_braces += 1
            
        res = try_parse(temp_str)
        if res: return res
    
    # Final failure: show context for debugging
    error_snippet = text.replace('\n', ' ')
    raise ValueError(f"JSON 解析失败。总长度: {len(text)}。末尾内容: ...{error_snippet[-100:]}")

def generate_ppt_content(topic: str, provider: str = "openai", api_key: str = None) -> PPTContent:
    client, model = get_client_and_model(provider, api_key)

    if not client or not model:
        error_msg = f"未检测到 {provider} 的有效 API Key。请在后端 .env 文件中配置，或在前端页面输入 API Key。"
        print(f"Error: {error_msg}")
        raise ValueError(error_msg)

    print(f"Calling {provider} API with model {model} for topic: {topic}...")
    
    prompt = f"""
    你是一位享誉全球的 PPT 设计大师和文案专家。请根据用户主题：'{topic}'，生成一份极具视觉冲击力和专业度的 PPT JSON 数据。
    
    ### 设计要求：
    1. **配色方案**：根据主题选择一套高级的、符合行业特性的配色（例如：科技蓝、简约白、商务黑、活力橙等）。
    2. **布局多样性**：每一页都要根据内容选择合适的 `layout_type`：
       - `centered`: 适用于标题页或金句页。
       - `bullet_points`: 适用于标准的要点陈述。
       - `two_columns`: 适用于对比或左文右图。
       - `title_only`: 适用于极简的视觉冲击页。
    3. **内容润色**：将生硬的文字润色为更具说服力、更简洁的专业文案。
    4. **页数**：生成 6-10 页幻灯片，包含：标题页、目录页（可选）、内容页、总结/结束页。

    ### JSON 结构要求：
    {{
        "title": "PPT总体标题",
        "theme_color": "十六进制颜色代码",
        "accent_color": "十六进制辅助颜色代码",
        "slides": [
            {{
                "page_title": "页面标题",
                "content": ["润色后的核心要点1", "要点2", "..."],
                "layout_type": "centered | bullet_points | two_columns | title_only",
                "image_description": "极其详尽的、适合 Midjourney 或 DALL-E 风格的配图提示词"
            }}
        ]
    }}
    请只输出合法的 JSON 内容，不要包含任何多余文字。
    """

    try:
        # Some providers don't support response_format="json_object"
        # We'll use it for OpenAI/Gemini but maybe not for all
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that outputs professional PPT outlines in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096 # Prevent truncation
        }
        
        # OpenAI supports it reliably
        if provider == "openai":
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        
        content_str = response.choices[0].message.content
        print(f"Received response from {provider}: {content_str[:100]}...")
        
        data = extract_json(content_str)
        print(f"Successfully parsed JSON from {provider}.")
        return PPTContent(**data)
        
    except Exception as e:
        error_str = str(e)
        print(f"Error calling {provider}: {error_str}")
        
        # Add a more helpful tip for Doubao endpoint errors
        if provider == "doubao" and "404" in error_str:
            error_str += " (提示：豆包/Ark 的 Model ID 需要填写 '推理终端' 的 Endpoint ID，例如 ep-xxx，而不是模型名称)"
        
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Detailed error response: {e.response.text}")
        raise ValueError(error_str) from e

def polish_topic(topic: str, provider: str = "openai", api_key: str = None) -> str:
    """
    Polishes the topic and provides suggestions.
    """
    client, model = get_client_and_model(provider, api_key)
    if not client or not model:
        return topic # Fallback

    prompt = f"作为一个 PPT 文案专家，请将以下 PPT 主题进行润色，使其更具吸引力和专业度。只需返回润色后的主题：'{topic}'"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip().strip("'\"")
    except:
        return topic

