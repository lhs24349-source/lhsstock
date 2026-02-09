import json
import os
import pandas as pd
from datetime import datetime
import time

# 크롤링 모듈 import (RSS 피드 대신 직접 크롤링 사용)
from src.news_crawler import NewsCrawler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
FEEDS_FILE = os.path.join(DATA_DIR, 'feeds.json')
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')
STATS_FILE = os.path.join(DATA_DIR, 'stats.json')


class DataManager:
    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        if not os.path.exists(FEEDS_FILE):
            with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        if not os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        if not os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"visitors": 0}, f)

    def get_feeds(self):
        with open(FEEDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_feed(self, name, url, category):
        feeds = self.get_feeds()
        new_feed = {"name": name, "url": url, "category": category}
        feeds.append(new_feed)
        with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(feeds, f, indent=4, ensure_ascii=False)
        return True

    def remove_feed(self, url):
        feeds = self.get_feeds()
        feeds = [f for f in feeds if f['url'] != url]
        with open(FEEDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(feeds, f, indent=4, ensure_ascii=False)
        return True

    def fetch_and_update_news(self):
        """
        크롤링을 통해 뉴스를 수집하고 업데이트합니다.
        기존 RSS 피드 방식 대신 직접 웹페이지 크롤링을 사용합니다.
        """
        existing_news = self.load_news()
        existing_links = {item['link'] for item in existing_news}
        
        # 크롤러를 사용하여 뉴스 수집
        crawler = NewsCrawler()
        crawled_news = crawler.fetch_all_news(max_per_source=30)
        
        # 기존에 없는 새 뉴스만 필터링
        new_items = []
        for item in crawled_news:
            if item['link'] not in existing_links:
                new_items.append(item)
                existing_links.add(item['link'])
        
        # 새 뉴스와 기존 뉴스 합치기
        all_news = new_items + existing_news
        
        # 발행일 기준 내림차순 정렬
        try:
            all_news.sort(key=lambda x: x.get('fetched_at', ''), reverse=True)
        except:
            pass  # 정렬 실패시 그대로 유지
        
        # 최대 1000개 뉴스만 유지
        all_news = all_news[:1000]
        
        with open(NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_news, f, indent=4, ensure_ascii=False)
        
        print(f"뉴스 업데이트 완료: 새로운 뉴스 {len(new_items)}개 추가됨")
        return len(new_items)

    def load_news(self):
        try:
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_stats(self):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"visitors": 0}

    def increment_visitor_count(self):
        stats = self.load_stats()
        stats["visitors"] += 1
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f)
        return stats["visitors"]
