#!/usr/bin/env python3
"""
maxRSS - 极简个人 RSS 发布工具
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


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


def generate_rss(config, items):
    """生成 RSS XML"""
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    channel = SubElement(rss, 'channel')
    
    # 频道信息
    SubElement(channel, 'title').text = config['title']
    SubElement(channel, 'description').text = config['description']
    SubElement(channel, 'link').text = config['link']
    SubElement(channel, 'language').text = config.get('language', 'zh-CN')
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')
    SubElement(channel, 'generator').text = 'maxRSS'
    
    # Atom 自链接
    atom_link = SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', f"{config['link']}/feed.xml")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # 条目
    max_items = config.get('max_items', 50)
    for item in items[:max_items]:
        entry = SubElement(channel, 'item')
        SubElement(entry, 'title').text = item['title']
        SubElement(entry, 'link').text = item['link']
        SubElement(entry, 'description').text = item['description']
        SubElement(entry, 'pubDate').text = item['pubDate']
        SubElement(entry, 'guid').text = item['link']
        
        # 如果有完整内容，添加到 content:encoded
        if 'content' in item and item['content']:
            content_encoded = SubElement(entry, '{http://purl.org/rss/1.0/modules/content/}encoded')
            content_encoded.text = item['content']
    
    # 格式化 XML
    rough_string = tostring(rss, encoding='unicode')
    reparsed = parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8')


def publish_item(config, title, url, desc, content=None):
    """发布一条新内容"""
    feeds_dir = Path(__file__).parent / "feeds"
    feeds_dir.mkdir(exist_ok=True)
    feed_path = feeds_dir / "feed.xml"
    
    # 加载已有条目
    items = load_existing_feeds(feed_path)
    
    # 创建新条目
    new_item = {
        'title': title,
        'link': url,
        'description': desc,
        'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800'),
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
