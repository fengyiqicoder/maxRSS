#!/usr/bin/env python3
"""
maxRSS - 极简个人 RSS 发布工具
"""

import json
import os
import re
import sys
import argparse
import uuid
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print("❌ 错误：找不到 config.json")
        print("请复制 config.example.json 为 config.json 并修改")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_existing_feeds(feed_path):
    """加载已有的 feed 条目"""
    if not feed_path.exists():
        return []
    
    # 解析现有 RSS 文件
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(feed_path)
        root = tree.getroot()
        items = []
        for item in root.findall('.//item'):
            entry = {
                'title': item.findtext('title', ''),
                'link': item.findtext('link', ''),
                'description': item.findtext('description', ''),
                'pubDate': item.findtext('pubDate', ''),
                'guid': item.findtext('guid', ''),
            }
            # 尝试获取 content:encoded
            content = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            if content is not None:
                entry['content'] = content.text
            items.append(entry)
        return items
    except Exception as e:
        print(f"⚠️  读取现有 feed 失败: {e}")
        return []


def markdown_to_html(text):
    """将 Markdown 转换为 HTML"""
    if not text:
        return ''
    # 如果已经是 HTML（包含 HTML 标签），直接返回
    if re.search(r'<(p|div|h[1-6]|ol|ul|li|br|hr|a|img|table)\b', text):
        return text

    try:
        import markdown
        return markdown.markdown(text, extensions=['tables', 'fenced_code'])
    except ImportError:
        pass

    lines = text.split('\n')
    html_parts = []
    in_list = False
    paragraph = []

    def flush_paragraph():
        if paragraph:
            html_parts.append('<p>' + '<br/>'.join(paragraph) + '</p>')
            paragraph.clear()

    for line in lines:
        stripped = line.strip()

        # 空行：结束当前段落
        if not stripped:
            flush_paragraph()
            if in_list:
                html_parts.append('</ol>')
                in_list = False
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.+?)(?:\s*#*\s*)?$', stripped)
        if m:
            flush_paragraph()
            if in_list:
                html_parts.append('</ol>')
                in_list = False
            level = len(m.group(1))
            content = m.group(2)
            html_parts.append(f'<h{level}>{content}</h{level}>')
            continue

        # 分隔线
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            flush_paragraph()
            html_parts.append('<hr/>')
            continue

        # 有序列表
        m = re.match(r'^\d+[.、]\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if not in_list:
                html_parts.append('<ol>')
                in_list = True
            html_parts.append(f'<li>{m.group(1)}</li>')
            continue

        # 普通段落行
        if in_list:
            html_parts.append('</ol>')
            in_list = False
        paragraph.append(stripped)

    flush_paragraph()
    if in_list:
        html_parts.append('</ol>')

    html = '\n'.join(html_parts)
    # 行内格式：粗体、链接、图片
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1"/>', html)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    return html


def generate_rss(config, items):
    """生成 RSS XML"""
    max_items = config.get('max_items', 50)
    now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')
    feed_url = f"{config['link']}/feed.xml"

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">',
        '<channel>',
        f'<title>{xml_escape(config["title"])}</title>',
        f'<link>{xml_escape(config["link"])}</link>',
        f'<description>{xml_escape(config["description"])}</description>',
        f'<language>{xml_escape(config.get("language", "zh-CN"))}</language>',
        f'<lastBuildDate>{now}</lastBuildDate>',
        f'<atom:link href="{xml_escape(feed_url)}" rel="self" type="application/rss+xml"/>',
    ]

    for item in items[:max_items]:
        # guid: 有效 URL 直接用，否则加 isPermaLink="false"
        guid = item.get('guid', '')
        if guid and guid != '#':
            guid_text = guid
        elif item.get('link') and item['link'] != '#':
            guid_text = item['link']
        else:
            guid_text = f"maxrss-{uuid.uuid4().hex[:12]}"

        is_url = guid_text.startswith('http://') or guid_text.startswith('https://')
        guid_attr = '' if is_url else ' isPermaLink="false"'

        lines.append('<item>')
        lines.append(f'<title><![CDATA[ {item["title"]} ]]></title>')
        lines.append(f'<link>{xml_escape(item.get("link", ""))}</link>')
        lines.append(f'<guid{guid_attr}>{xml_escape(guid_text)}</guid>')
        lines.append(f'<pubDate>{item["pubDate"]}</pubDate>')
        lines.append(f'<description><![CDATA[ {item.get("description", "")} ]]></description>')

        if item.get('content'):
            html_content = markdown_to_html(item['content'])
            lines.append(f'<content:encoded><![CDATA[ {html_content} ]]></content:encoded>')

        lines.append('</item>')

    lines.append('</channel>')
    lines.append('</rss>')

    return '\n'.join(lines).encode('utf-8')


def publish_item(config, title, url, desc, content=None):
    """发布一条新内容"""
    feeds_dir = Path(__file__).parent / "feeds"
    feeds_dir.mkdir(exist_ok=True)
    feed_path = feeds_dir / "feed.xml"
    
    # 加载已有条目
    items = load_existing_feeds(feed_path)
    
    # 创建新条目（如果没有有效 URL，自动生成唯一 guid）
    item_guid = url if url and url != '#' else f"maxrss-{uuid.uuid4().hex[:12]}"
    new_item = {
        'title': title,
        'link': url,
        'description': desc,
        'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800'),
        'guid': item_guid,
    }
    if content:
        new_item['content'] = content
    
    # 添加到开头
    items.insert(0, new_item)
    
    # 生成 RSS
    rss_content = generate_rss(config, items)
    
    # 保存
    with open(feed_path, 'wb') as f:
        f.write(rss_content)
    
    print(f"✅ 已发布: {title}")
    print(f"📡 RSS: {config['link']}/feed.xml")


def interactive_mode(config):
    """交互模式"""
    print("📝 交互模式 - 输入内容（Ctrl+C 取消）\n")
    
    try:
        title = input("标题: ").strip()
        if not title:
            print("❌ 标题不能为空")
            return
        
        url = input("链接: ").strip()
        if not url:
            url = "#"
        
        print("描述（多行输入，空行结束）:")
        desc_lines = []
        while True:
            line = input()
            if line == "":
                break
            desc_lines.append(line)
        desc = "\n".join(desc_lines)
        
        publish_item(config, title, url, desc)
        
    except KeyboardInterrupt:
        print("\n\n已取消")
        return


def main():
    parser = argparse.ArgumentParser(description='maxRSS - 发布内容到个人 RSS')
    parser.add_argument('-t', '--title', help='文章标题')
    parser.add_argument('-u', '--url', help='文章链接')
    parser.add_argument('-d', '--desc', help='文章描述')
    parser.add_argument('-c', '--content', help='完整内容（HTML）')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.interactive:
        interactive_mode(config)
    elif args.title:
        publish_item(
            config,
            title=args.title,
            url=args.url or "#",
            desc=args.desc or "",
            content=args.content
        )
    else:
        parser.print_help()
        print("\n💡 提示: 使用 -i 进入交互模式")


if __name__ == '__main__':
    main()
