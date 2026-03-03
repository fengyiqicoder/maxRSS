# maxRSS

一个极简的个人 RSS 发布站，基于 GitHub Pages 托管。

## 功能

- 📡 公网可访问的 RSS Feed
- 📝 本地一键推送内容
- 🆓 完全免费（GitHub Pages 托管）
- 🔒 可选的访问控制（通过 secret token）

## 快速开始

### 1. 配置

复制配置模板：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "title": "My RSS Feed",
  "description": "我的私人 RSS",
  "link": "https://你的用户名.github.io/maxRSS",
  "author": "你的名字"
}
```

### 2. 推送内容

```bash
python publish.py --title "文章标题" --url "https://example.com" --desc "文章摘要"
```

或者使用交互模式：

```bash
python publish.py -i
```

### 3. 部署到 GitHub Pages

```bash
git add .
git commit -m "更新 RSS"
git push origin main
```

GitHub Actions 会自动构建并部署到 Pages。

## RSS 地址

部署后，你的 RSS 地址是：

```
https://你的用户名.github.io/maxRSS/feed.xml
```

## 命令行选项

```
python publish.py --help

Options:
  -t, --title TEXT     文章标题
  -u, --url TEXT       文章链接
  -d, --desc TEXT      文章描述/摘要
  -c, --content TEXT   完整内容（HTML）
  -i, --interactive    交互模式
```

## 目录结构

```
maxRSS/
├── README.md
├── config.json           # 你的配置
├── config.example.json   # 配置模板
├── publish.py           # 推送脚本
├── feeds/               # 生成的 RSS 文件
│   └── feed.xml
└── .github/
    └── workflows/
        └── deploy.yml   # GitHub Actions 自动部署
```
