"""每周选题 Agent（通用模板）。

本质：调用 API 问模型 -> 执行工具 -> 回喂结果。
用法：python agent/topics.py
环境变量：
  DEEPSEEK_API_KEY  必需
  SITE_FEED         站点 RSS（默认占位）
  SITE_BRIEF        站点定位，一句话（给模型理解主题）
  DEVTO_USERNAME    可选，你的 Dev.to 用户名（配置后启用 Dev.to 反馈工具）
  DEVTO_API_KEY     可选，配置后可见 Dev.to 阅读量（否则只有赞/评论）
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
DEVTO_USERNAME = os.getenv("DEVTO_USERNAME", "")
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY", "")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_existing_titles",
            "description": "读取博客已有的文章标题，用于避免选题重复",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "devto_feedback",
            "description": "读取 Dev.to 文章的阅读 / 点赞 / 评论数据，用于复盘哪类内容有效",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def devto_feedback() -> str:
    if not DEVTO_USERNAME:
        return "（未配置 DEVTO_USERNAME，跳过 Dev.to 反馈）"
    headers = {"User-Agent": "topics-agent/1.0", "Accept": "application/vnd.forem.api-v1+json"}
    if DEVTO_API_KEY:
        url = "https://dev.to/api/articles/me?per_page=50"  # 带 key 才有 page_views_count
        headers["api-key"] = DEVTO_API_KEY
    else:
        url = f"https://dev.to/api/articles?username={DEVTO_USERNAME}&per_page=50"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        arts = json.loads(r.read().decode("utf-8", "ignore"))
    arts = [a for a in arts if a.get("published_at")]
    arts.sort(key=lambda a: a.get("public_reactions_count", 0), reverse=True)
    lines = []
    for a in arts:
        views = a.get("page_views_count")
        head = f"阅读 {views} | " if views is not None else ""
        lines.append(f"- {a.get('title')} | {head}赞 {a.get('public_reactions_count', 0)} | 评论 {a.get('comments_count', 0)}")
    return "\n".join(lines) or "（Dev.to 暂无已发布文章）"


def run_tool(name: str, args: dict) -> str:
    if name == "list_existing_titles":
        req = urllib.request.Request(FEED, headers={"User-Agent": "topics-agent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            xml = r.read().decode("utf-8", "ignore")
        titles = [t.strip() for t in re.findall(r"<title>(.*?)</title>", xml, re.S)]
        return "\n".join(titles[1:])  # 跳过 channel 自己的标题
    if name == "devto_feedback":
        return devto_feedback()
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
第二步：用工具 devto_feedback 看 Dev.to 上哪些文章反响好（没数据就跳过）。
第三步：先写一段简短「反馈复盘」：从数据看哪类标题 / 主题有效、下一步加倍押注什么。
第四步：给出 5 个新选题，每个包含——中文标题 / 目标关键词 / 类型（引流 | 转化 | 护城河）/ 变现钩子（一句话）。

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
