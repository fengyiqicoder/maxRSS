#!/bin/bash
# maxRSS 推送脚本 - 简化版

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: ./push.sh \"标题\" [链接] [描述]"
    echo "  示例: ./push.sh \"好文章\" \"https://example.com\" \"这是一篇好文章\""
    echo ""
    echo "或使用交互模式:"
    echo "  python publish.py -i"
    exit 1
fi

TITLE="$1"
URL="${2:-#}"
DESC="${3:-}"

# 发布
python3 publish.py -t "$TITLE" -u "$URL" -d "$DESC"

# 询问是否推送到 GitHub
read -p "推送到 GitHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "add: $TITLE"
    git push origin main
    echo "✅ 已推送到 GitHub"
fi
