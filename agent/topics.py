"""每周选题 Agent（通用模板）。

本质：调用 API 问模型 -> 执行工具 -> 回喂结果。
用法：python agent/topics.py
环境变量：
  DEEPSEEK_API_KEY  必需
  SITE_FEED         站点 RSS（默认占位）
  SITE_BRIEF        站点定位，一句话（给模型理解主题）
  LLM_BASE_URL / LLM_MODEL  可选（换模型）
"""
import datetime
import json
import os
import re
import urllib.request

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
FEED = os.getenv("SITE_FEED", "https://your-site.com/feed.xml")
BRIEF = os.getenv("SITE_BRIEF", "一个技术博客")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_existing_titles",
            "description": "读取博客已有的文章标题，用于避免选题重复",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


def run_tool(name: str, args: dict) -> str:
    if name == "list_existing_titles":
        req = urllib.request.Request(FEED, headers={"User-Agent": "topics-agent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            xml = r.read().decode("utf-8", "ignore")
        titles = [t.strip() for t in re.findall(r"<title>(.*?)</title>", xml, re.S)]
        return "\n".join(titles[1:])  # 跳过 channel 自己的标题
    return f"unknown tool: {name}"


def agent(user_input: str) -> str:
    messages = [{"role": "user", "content": user_input}]
    while True:
        reply = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = reply.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = run_tool(call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


def build_prompt() -> str:
    return f"""你是「{BRIEF}」方向的技术博客主编。

第一步：用工具 list_existing_titles 看已写过哪些文章（避免重复）。
第二步：给出 5 个新选题，每个包含——中文标题 / 目标关键词 / 类型（引流 | 转化 | 护城河）/ 变现钩子（一句话）。

要求：选在「你的差异化交叉区」，面向想入门或转型的工程师；用 markdown 输出。"""


def main() -> None:
    out = agent(build_prompt())
    today = datetime.date.today().isoformat()
    os.makedirs("weekly", exist_ok=True)
    path = f"weekly/{today}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 选题建议 · {today}\n\n{out}\n")
    print("written:", path)


if __name__ == "__main__":
    main()
