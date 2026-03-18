{
  "project_title": "大模型驱动的PPT自动生成系统技术方案文档",
  "version": "1.0",
  "author": "AI Assistant",
  "document_sections": [
    {
      "section_name": "一、 项目概述",
      "content": "本项目旨在通过大语言模型（LLM）的逻辑生成能力，结合自动化办公库（python-pptx）及前端现代框架，实现从用户输入主题到在线预览、下载PPT的完整闭环。解决用户在制作PPT时构思慢、排版难的痛点。"
    },
    {
      "section_name": "二、 系统架构设计",
      "architecture_layers": [
        {
          "layer": "前端展示层 (Frontend)",
          "function": "负责用户需求采集（主题、风格、受众）、PPT在线高仿真预览（Reveal.js）、以及最终文件的下载触发。"
        },
        {
          "layer": "后端逻辑层 (Backend)",
          "function": "采用 FastAPI 或 Flask 框架，负责业务编排、Prompt 模板管理、异步任务调度及文件流处理。"
        },
        {
          "layer": "模型接口层 (LLM API)",
          "function": "调用 OpenAI GPT-4、Claude 或国产大模型（如智谱、通义千问），将非结构化指令转化为结构化的 JSON 内容。"
        },
        {
          "layer": "文件处理层 (File Service)",
          "function": "使用 python-pptx 库将结构化数据填充至预设母版，并处理图片插入及样式设置。"
        }
      ]
    },
    {
      "section_name": "三、 核心技术栈推荐",
      "stack": {
        "frontend": "Vue 3 / React + Element Plus / Ant Design + Reveal.js (预览组件)",
        "backend": "Python 3.9+ + FastAPI (高性能异步框架)",
        "llm_engine": "OpenAI API (GPT-4o) / LangChain (链式调用)",
        "ppt_library": "python-pptx (底层文件生成)",
        "task_queue": "Celery + Redis (处理耗时生成请求)"
      }
    },
    {
      "section_name": "四、 核心实现流程",
      "workflow_steps": [
        {
          "step": "1. 结构化生成",
          "description": "通过精心设计的 Prompt，强制要求 LLM 返回固定格式的 JSON 数据（包含 Title、Slide 内容列表、Image Prompt 等）。"
        },
        {
          "step": "2. 母版解析与填充",
          "description": "后端读取预设的 .pptx 模板，利用 python-pptx 遍历 JSON，将内容注入到对应的 Placeholder（占位符）中。"
        },
        {
          "step": "3. 仿真预览转换",
          "description": "为保证前端性能，不直接渲染 PPTX 文件，而是将生成的 JSON 同步给前端 Reveal.js 组件进行 Web 渲染预览。"
        },
        {
          "step": "4. 异步生成与下载",
          "description": "后端生成物理文件并存储，返回下载 URL，用户点击下载按钮获取文件。"
        }
      ]
    },
    {
      "section_name": "五、 关键 Prompt 设计示例",
      "prompt_logic": "你是一位PPT专家。请根据用户主题：'{{topic}}'，生成一份专业的PPT JSON数据。结构必须严格遵循：{ 'title': '', 'slides': [ { 'page_title': '', 'content': [], 'image_description': '' } ] }。"
    },
    {
      "section_name": "六、 预览与下载优化方案",
      "preview_options": [
        {
          "option": "基于 JSON 的中间态预览 (响应最快)",
          "pros": "前端根据 LLM 返回的 JSON，直接用 HTML/CSS 模拟出一个 PPT 的样子（类似幻灯片卡片）。用户满意后，再点击“生成并下载”触发后端生成 .pptx。",
          "cons": "与最终生成的 PPT 样式可能存在微小差异。"
        }
      ]
    },
    {
      "section_name": "七、 进阶功能规划",
      "future_features": [
        "AI 自动配图：结合 DALL-E 3 根据页面内容自动生成背景图。",
        "多模板切换：提供商务、极简、教育等多种 PPT 母版供用户选择。",
        "在线二次编辑：用户可以在预览界面直接修改文字，实时同步至 JSON 结构。"
      ]
    }
  ]
}