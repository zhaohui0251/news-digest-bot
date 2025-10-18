#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车公关新闻摘要系统 - 优化版
使用官方RSS源，更稳定可靠
"""

import os
import re
import requests
import feedparser
from datetime import datetime, timedelta
from collections import defaultdict
import time

# ==================== 配置区 ====================

# 媒体RSS源配置（使用官方源）
RSS_SOURCES = {
    '新华社': 'http://www.news.cn/tech/news_tech.xml',
    '央视新闻': 'https://news.cctv.com/rss/china.xml',
    '36氪': 'https://36kr.com/feed',
    '虎嗅': 'https://www.huxiu.com/rss/0.xml',
    '汽车之家': 'https://www.autohome.com.cn/rss/',
    '新浪科技': 'https://tech.sina.com.cn/rss/roll.xml',
    '网易科技': 'https://tech.163.com/special/00097UHL/tech_datalist.xml',
    '腾讯科技': 'https://tech.qq.com/web/rss_web.xml',
    '凤凰科技': 'https://tech.ifeng.com/listpage/11574/0/1/rss.xml',
    'IT之家': 'https://www.ithome.com/rss/',
}

# 关键词分类配置
KEYWORDS = {
    '🚗 汽车行业': [
        '新能源', '电动车', '自动驾驶', '充电桩', '比亚迪', '特斯拉', 
        '理想', '蔚来', '小鹏', '华为汽车', '问界', '智界', '极氪', 
        '销量', '新车', '上市', '发布会', '汽车', '车企', '智驾'
    ],
    '🤖 AI科技': [
        '人工智能', 'AI', '大模型', 'ChatGPT', '芯片', '智能驾驶', 
        '激光雷达', '车联网', '自动化', '算力', '英伟达', '华为鸿蒙',
        '智能座舱', '语音助手', 'GPU'
    ],
    '📊 政策法规': [
        '碳中和', '补贴', '政策', '标准', '法规', '交通', 
        '工信部', '发改委', '新规', '管理办法', '准入', '目录'
    ],
    '🔥 社会热点': [
        '消费', '趋势', '市场', '经济', '投资', '融资', 
        '上市', '财报', '增长', '下滑', '用户', '体验'
    ],
}

# 竞品品牌
COMPETITOR_BRANDS = ['比亚迪', '特斯拉', '理想', '蔚来', '小鹏', '问界', '华为汽车', '极氪', '零跑', '哪吒']

# 负面舆情关键词
NEGATIVE_KEYWORDS = ['召回', '事故', '起火', '维权', '投诉', '质量问题', '安全隐患', '漏洞', '缺陷', '故障']

# ==================== 核心功能函数 ====================

def fetch_rss_news(hours=48):
    """采集所有RSS源的新闻"""
    news_list = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    print(f"📥 开始采集新闻（时间范围：过去{hours}小时）...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for source_name, rss_url in RSS_SOURCES.items():
        try:
            print(f"  - 正在采集: {source_name} ({rss_url})")
            
            # 添加超时和重试机制
            response = requests.get(rss_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"    ⚠️ HTTP状态码: {response.status_code}")
                continue
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print(f"    ⚠️ 未获取到任何条目")
                continue
            
            print(f"    ✓ 获取到 {len(feed.entries)} 条原始数据")
            
            for entry in feed.entries[:30]:
                # 解析发布时间
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_time = datetime(*entry.published_parsed[:6])
                    except:
                        pub_time = datetime.now()
                else:
                    pub_time = datetime.now()
                
                # 只保留最近N小时的新闻
                if pub_time < cutoff_time:
                    continue
                
                # 清理摘要
                summary_text = entry.get('summary', entry.get('description', ''))
                summary_text = re.sub(r'<[^>]+>', '', summary_text)
                summary_text = summary_text.strip()[:300]
                
                # 获取标题
                title = entry.get('title', '').strip()
                if not title:
                    continue
                
                news_item = {
                    'source': source_name,
                    'title': title,
                    'link': entry.get('link', ''),
                    'summary': summary_text,
                    'pub_time': pub_time,
                }
                news_list.append(news_item)
                
        except requests.Timeout:
            print(f"    ⚠️ 采集超时")
        except Exception as e:
            print(f"    ⚠️ 采集失败: {str(e)[:100]}")
            continue
    
    # 按时间倒序排列
    news_list.sort(key=lambda x: x['pub_time'], reverse=True)
    print(f"✅ 采集完成，共获取 {len(news_list)} 条新闻\n")
    return news_list


def classify_news(news_list):
    """根据关键词对新闻进行分类"""
    categorized = defaultdict(list)
    
    print("🔍 开始分类新闻...")
    
    for news in news_list:
        text = news['title'] + ' ' + news['summary']
        matched_category = None
        
        for category, keywords in KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                matched_category = category
                break
        
        news['is_competitor'] = any(brand in text for brand in COMPETITOR_BRANDS)
        news['is_negative'] = any(word in text for word in NEGATIVE_KEYWORDS)
        
        if matched_category:
            categorized[matched_category].append(news)
    
    # 每个分类最多保留10条
    for category in categorized:
        categorized[category] = categorized[category][:10]
    
    # 打印分类统计
    for category, items in categorized.items():
        print(f"  - {category}: {len(items)} 条")
    
    print("✅ 分类完成\n")
    return dict(categorized)


def generate_ai_summary(news_item):
    """使用Gemini API生成AI摘要"""
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # 如果没有API密钥，使用简单摘要
    if not api_key:
        return generate_simple_summary(news_item['summary'], 50)
    
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        
        prompt = f"""请将以下新闻浓缩为50字以内的摘要，突出核心要点：

标题：{news_item['title']}
内容：{news_item['summary']}

要求：
1. 不超过50字
2. 保留关键信息
3. 语言简洁专业"""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 100
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{url}?key={api_key}",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if len(summary) > 50:
                summary = summary[:47] + '...'
            
            return summary
        else:
            return generate_simple_summary(news_item['summary'], 50)
            
    except Exception as e:
        return generate_simple_summary(news_item['summary'], 50)


def generate_simple_summary(text, max_length=50):
    """生成简单摘要（降级方案）"""
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length-3] + '...'


def build_feishu_message(categorized_news):
    """构建飞书消息卡片"""
    today = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    total_count = sum(len(items) for items in categorized_news.values())
    
    print("📝 开始构建飞书消息...")
    
    content = f"📰 **每日新闻摘要** | {today}\n"
    content += f"共采集 **{total_count}** 条重点资讯\n\n"
    content += "---\n\n"
    
    for category, news_items in categorized_news.items():
        if not news_items:
            continue
            
        content += f"## {category} ({len(news_items)}条)\n\n"
        
        for idx, news in enumerate(news_items, 1):
            summary = generate_ai_summary(news)
            
            tags = []
            if news.get('is_competitor'):
                tags.append('🎯竞品')
            if news.get('is_negative'):
                tags.append('⚠️预警')
            
            tag_str = ' '.join(tags) + ' ' if tags else ''
            
            content += f"{idx}. {tag_str}**{news['title']}**\n"
            content += f"   📝 {summary}\n"
            content += f"   🔗 [查看原文]({news['link']}) | 来源：{news['source']}\n\n"
        
        content += "\n"
    
    content += "---\n"
    content += "💡 *本摘要由AI自动生成，如有疑问请查看原文*\n"
    
    print("✅ 消息构建完成\n")
    
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "content": f"📰 每日新闻摘要 | {today}",
                    "tag": "plain_text"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                }
            ]
        }
    }


def send_to_feishu(message):
    """发送消息到飞书群"""
    webhook_url = os.environ.get('FEISHU_WEBHOOK')
    
    if not webhook_url:
        print("❌ 错误：未配置飞书Webhook地址")
        return False
    
    print("📤 开始发送到飞书...")
    
    try:
        response = requests.post(
            webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 消息发送成功！\n")
                return True
            else:
                print(f"❌ 发送失败: {result}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("🚀 汽车公关新闻摘要系统 - 启动")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    # 采集新闻（扩大到48小时）
    news_list = fetch_rss_news(hours=48)
    
    if not news_list:
        print("⚠️ 未采集到新闻，任务结束")
        return
    
    # 分类过滤
    categorized_news = classify_news(news_list)
    
    if not categorized_news:
        print("⚠️ 没有符合条件的新闻，任务结束")
        return
    
    # 构建消息
    message = build_feishu_message(categorized_news)
    
    # 发送到飞书
    success = send_to_feishu(message)
    
    print("=" * 60)
    if success:
        print("🎉 任务执行成功！")
    else:
        print("❌ 任务执行失败，请检查配置")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
