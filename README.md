# weekly-topics-agent

> **一个最小 AI Agent：每周自动给你的博客出 5 个选题。**
> 本质就是一个循环 —— **调用 API 问模型 → 执行工具 → 回喂结果**。跑在 **GitHub Actions** 上，免费、定时、免服务器。

## 它做什么

- **工具**：
  - `list_existing_titles`：读你站点的 RSS（`/feed.xml`），拿到已有文章标题 → 避免选题重复；
  - `devto_feedback`：读 Dev.to 文章的阅读 / 点赞 / 评论（可选，复盘哪类内容有效）；
- 让模型（DeepSeek，OpenAI 兼容）据此先写**反馈复盘**，再产出 **5 个选题**（标题 / 关键词 / 类型 / 变现钩子）；
- 结果写入 `weekly/<日期>.md`，**自动提交回仓库**。

## 快速开始

1. **Fork / 用这个模板建仓库**（Public 或 Private 均可）。
2. 加 **Secret**（Settings → Secrets and variables → Actions）：
   - `DEEPSEEK_API_KEY` = 你的 key
3. 加 **Variables**（同页面 → Variables 标签）：
   - `SITE_FEED` = 你站点的 RSS，如 `https://your-site.com/feed.xml`
   - `SITE_BRIEF` = 一句话定位，如 `嵌入式 × AI Agent`
   - `DEVTO_USERNAME` = 你的 Dev.to 用户名（可选，启用反馈工具）
   - `DEVTO_API_KEY`（Secret）= Dev.to → Settings → Extensions → DEV API Keys（可选，填了才有**阅读量**）
4. **Actions → weekly-topics-agent → Run workflow** 跑一次。
5. 之后**每周一自动**出选题。

## 本地跑（可选）

```bash
pip install -r agent/requirements.txt
export DEEPSEEK_API_KEY="sk-..."
export SITE_FEED="https://your-site.com/feed.xml"
export SITE_BRIEF="嵌入式 × AI Agent"
export DEVTO_USERNAME="your-devto-username"   # 可选
python agent/topics.py
```

## 为什么跑在 GitHub Actions

- **免费**（public 无限时长）、**定时**（cron）、**免服务器**；
- runner 在**美国**，直达各 AI API；
- 有仓库权限，能把结果**提交回来**。

## 原则

**Agent 干脏活 / 半成品；人做判断与发布。** 数据、密钥、关键词库保持私有。

## 许可

MIT

---

出处：<https://embedai.com.cn/posts/give-blog-an-agent>
