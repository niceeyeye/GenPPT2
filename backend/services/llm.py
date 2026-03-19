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
        model = os.getenv("DOUBAO_MODEL")
        print(f"Debug: Doubao Config - Key: {'set' if key else 'not set'}, Model: {model}, URL: {base_url}")
        if not key: 
            print("Error: Doubao API Key is missing.")
            return None, None
        if not model:
            print("Error: Doubao Model (Endpoint ID) is missing.")
            return None, None
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
    你是一位顶级的 PPT 设计大师和内容架构师，擅长制作具有苹果发布会风格（Vibe）的现代演示文稿。请根据用户主题：'{topic}'，生成一份深度结构化的 PPT JSON 数据。
    
    ### 核心内容设计逻辑 (借鉴 Banana Slides)：
    1. **叙事性结构**：不要只是堆砌事实。按照“痛点引入 -> 解决方案 -> 核心价值 -> 未来展望”的逻辑线组织 slides。
    2. **高信息密度卡片**：将复杂概念拆解为 3-4 个互补的卡片。每个卡片的 `title` 要有力（Action-oriented），`description` 要精炼且富有洞见。
    3. **视觉层次感**：
       - `title_only`：用于金句、关键转折点或大标题页。
       - `cards`：用于并列的功能、特性或团队展示。
       - `timeline`：用于演进历程、实施步骤或工作流。
       - `content_list`：用于详细的清单或深度的理论拆解。

    ### 视觉美学要求：
    - **配色方案**：严禁使用老土的配色。根据主题选择如 `Midnight Navy & Electric Cyan`、`Minimal White & Cyber Orange` 等现代配色。
    - **背景风格**：`bg_style` 必须精准匹配主题调性（`gradient`, `solid`, `mesh`）。

    ### JSON 结构严格要求：
    {{
        "title": "润色后的高冲击力主标题",
        "subtitle": "副标题，体现演示文稿的核心价值主张",
        "theme_color": "主色调（Hex格式）",
        "accent_color": "强调色（Hex格式）",
        "bg_style": "gradient | solid | mesh",
        "slides": [
            {{
                "page_title": "极简且有力的页面标题",
                "subtitle": "可选的页面金句或逻辑补充",
                "layout_type": "cards | timeline | title_only | content_list",
                "content": [
                    {{
                        "title": "要点标题（动词开头为佳）",
                        "description": "高度概括的内容，避免废话"
                    }}
                ]
            }}
        ]
    }}
    
    ### 质量控制：
    - 生成 6-10 页，确保每一页在逻辑上都是下一页的基石。
    - 严禁输出 Markdown 代码块标签，只返回纯 JSON。
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
    Polishes the topic using a professional designer's perspective.
    """
    print(f"--- Polish Topic Start (Provider: {provider}) ---")
    client, model = get_client_and_model(provider, api_key)
    if not client or not model:
        print("Error: No client or model found for polishing.")
        return topic # Fallback

    print(f"Calling {provider} for polishing with model {model}...")
    
    prompt = f"""
    作为一名专业的演示文稿（PPT）架构师和文案专家，请对用户提供的主题进行深度润色。
    
    ### 目标：
    1. **吸引力**：使标题更具冲击力和吸引力，能够瞬间抓住听众注意力。
    2. **专业度**：使用行业术语或更具深度的表达，提升整体格调。
    3. **逻辑性**：确保标题隐含清晰的演示逻辑或核心价值主张。
    
    ### 润色原则：
    - 保持简洁：不超过 20 个字。
    - 针对性：根据主题性质（商业、技术、教育等）调整语调。
    - 动作导向：尽量包含能够引发行动或思考的词汇。
    
    ### 待润色主题：
    '{topic}'
    
    ### 仅返回润色后的最终标题文本，不要包含任何解释、引号或前缀。
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位顶级 PPT 文案专家，只输出润色后的标题文本。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.8,
            timeout=30.0 # Add a timeout to prevent hanging forever
        )
        result = response.choices[0].message.content.strip().strip("'\"")
        print(f"Polishing result: {result}")
        return result
    except Exception as e:
        print(f"Error during polishing: {str(e)}")
        return topic


def modify_ppt_content(current_content: dict, instruction: str, provider: str = "openai", api_key: str = None) -> dict:
    """
    Modifies an existing PPT content JSON based on user instruction.
    """
    client, model = get_client_and_model(provider, api_key)
    if not client or not model:
        raise ValueError("未检测到有效的 API Key 或模型配置。")

    print(f"Calling {provider} API to modify outline with instruction: {instruction}")

    prompt = f"""
    你是一个专业的 PPT 架构师。下面是当前的 PPT 结构数据（JSON 格式）：
    ```json
    {json.dumps(current_content, ensure_ascii=False)}
    ```
    
    用户的修改指令是："{instruction}"
    
    请严格按照用户的指令修改上述 JSON 数据。你可以增加、删除、修改 slides，或者调整主题颜色、布局等。
    请保持原有的 JSON 结构完全不变（必须包含 title, subtitle, theme_color, accent_color, bg_style, slides 等字段）。
    如果用户要求增加一页，请确保新页面的结构和原有页面一致（包含 page_title, subtitle, layout_type, content 数组）。
    
    严禁输出任何 Markdown 格式的包裹（如 ```json ），只能输出纯合法的 JSON 字符串。
    """

    try:
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个只输出合法 JSON 字符串的 AI。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "timeout": 60.0
        }
        
        # Enable json_object format for OpenAI and Gemini
        if provider in ["openai", "gemini"]:
            kwargs["response_format"] = { "type": "json_object" }
            
        response = client.chat.completions.create(**kwargs)
        result_text = response.choices[0].message.content.strip()
        
        # Clean up potential markdown formatting if the model ignored instructions
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return json.loads(result_text.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse modified JSON. Raw text: {result_text}")
        raise ValueError("AI 返回的数据格式不正确，无法解析为 JSON。") from e
    except Exception as e:
        print(f"Error during modifying outline: {str(e)}")
        raise ValueError(f"调用 AI 服务失败: {str(e)}") from e

