"""
뉴스 크롤러 모듈

네이버 금융, 다음 금융 등에서 주식 관련 뉴스를 크롤링합니다.
RSS 피드 대신 직접 웹페이지를 파싱하여 더 안정적인 뉴스 수집이 가능합니다.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re


class NewsCrawler:
    """뉴스 크롤링을 담당하는 클래스"""
    
    def __init__(self):
        # 웹 요청시 사용할 헤더 (봇 차단 방지)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        # 요청 간 딜레이 (서버 부하 방지)
        self.request_delay = 1
    
    def fetch_naver_finance_news(self, max_items=30):
        """
        네이버 금융 뉴스를 크롤링합니다.
        
        Args:
            max_items: 최대 수집할 뉴스 개수
            
        Returns:
            뉴스 항목 리스트 [{title, link, summary, published, source, category}, ...]
        """
        news_items = []
        
        # 네이버 금융 뉴스 카테고리별 URL
        categories = {
            '시장': 'https://finance.naver.com/news/mainnews.naver',
            '종목': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
            '공시': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=259',
        }
        
        for category_name, url in categories.items():
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.encoding = 'euc-kr'  # 네이버 금융은 EUC-KR 인코딩 사용
                
                if response.status_code != 200:
                    print(f"Warning: {category_name} 페이지 요청 실패 (status: {response.status_code})")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 뉴스 리스트 파싱
                news_list = soup.select('li.newsList, ul.newsList li, dd')
                
                for item in news_list:
                    if len(news_items) >= max_items:
                        break
                        
                    # 제목과 링크 추출
                    link_tag = item.select_one('a')
                    if not link_tag:
                        continue
                    
                    title = link_tag.get_text(strip=True)
                    if not title or len(title) < 5:  # 너무 짧은 제목은 건너뜀
                        continue
                    
                    href = link_tag.get('href', '')
                    
                    # 상대 경로를 절대 경로로 변환
                    if href.startswith('/'):
                        link = f"https://finance.naver.com{href}"
                    elif href.startswith('http'):
                        link = href
                    else:
                        continue
                    
                    # 날짜 추출 (있는 경우)
                    date_tag = item.select_one('.wdate, .date, span.gray03')
                    published = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime('%Y-%m-%d %H:%M')
                    
                    # 요약 추출 (있는 경우)
                    summary_tag = item.select_one('.lead, p')
                    summary = summary_tag.get_text(strip=True) if summary_tag else ''
                    
                    news_items.append({
                        'title': title,
                        'link': link,
                        'summary': summary[:200] if summary else '',
                        'published': published,
                        'source': '네이버 금융',
                        'category': category_name,
                        'fetched_at': datetime.now().isoformat()
                    })
                
                time.sleep(self.request_delay)  # 서버 부하 방지
                
            except Exception as e:
                print(f"Error crawling {category_name}: {e}")
                continue
        
        return news_items
    
    def fetch_naver_main_news(self, max_items=20):
        """
        네이버 금융 메인 뉴스 (시황/전망)를 크롤링합니다.
        
        Args:
            max_items: 최대 수집할 뉴스 개수
            
        Returns:
            뉴스 항목 리스트
        """
        news_items = []
        url = 'https://finance.naver.com/news/mainnews.naver'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'euc-kr'
            
            if response.status_code != 200:
                print(f"Warning: 메인 뉴스 페이지 요청 실패")
                return news_items
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 메인 뉴스 영역 파싱
            articles = soup.select('.mainNewsList li, .news_list li')
            
            for article in articles[:max_items]:
                link_tag = article.select_one('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                
                if href.startswith('/'):
                    link = f"https://finance.naver.com{href}"
                elif href.startswith('http'):
                    link = href
                else:
                    continue
                
                if not title or len(title) < 5:
                    continue
                
                # 날짜 추출
                date_tag = article.select_one('.wdate, .date')
                published = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime('%Y-%m-%d %H:%M')
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'summary': '',
                    'published': published,
                    'source': '네이버 금융',
                    'category': '시황',
                    'fetched_at': datetime.now().isoformat()
                })
            
        except Exception as e:
            print(f"Error crawling main news: {e}")
        
        return news_items
    
    def fetch_daum_finance_news(self, max_items=20):
        """
        다음 금융 뉴스를 크롤링합니다.
        
        Args:
            max_items: 최대 수집할 뉴스 개수
            
        Returns:
            뉴스 항목 리스트
        """
        news_items = []
        url = 'https://finance.daum.net/news/category/economic'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Warning: 다음 금융 뉴스 요청 실패")
                return news_items
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 리스트 파싱
            articles = soup.select('.newsWrap li, article')
            
            for article in articles[:max_items]:
                link_tag = article.select_one('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href', '')
                
                if not link.startswith('http'):
                    link = f"https://finance.daum.net{link}"
                
                if not title or len(title) < 5:
                    continue
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'summary': '',
                    'published': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'source': '다음 금융',
                    'category': '경제',
                    'fetched_at': datetime.now().isoformat()
                })
            
        except Exception as e:
            print(f"Error crawling Daum finance news: {e}")
        
        return news_items
    
    def fetch_hankyung_news(self, max_items=15):
        """
        한국경제 증권 뉴스를 크롤링합니다.
        
        Args:
            max_items: 최대 수집할 뉴스 개수
            
        Returns:
            뉴스 항목 리스트
        """
        news_items = []
        url = 'https://www.hankyung.com/finance/stock'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Warning: 한경 뉴스 요청 실패")
                return news_items
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 리스트 파싱
            articles = soup.select('.news-list li, article.news-item, .article-list li')
            
            for article in articles[:max_items]:
                link_tag = article.select_one('a')
                if not link_tag:
                    continue
                
                title_tag = article.select_one('h3, .news-tit, .tit')
                title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
                link = link_tag.get('href', '')
                
                if not link.startswith('http'):
                    link = f"https://www.hankyung.com{link}"
                
                if not title or len(title) < 5:
                    continue
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'summary': '',
                    'published': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'source': '한국경제',
                    'category': '증권',
                    'fetched_at': datetime.now().isoformat()
                })
            
        except Exception as e:
            print(f"Error crawling Hankyung news: {e}")
        
        return news_items
    
    def fetch_all_news(self, max_per_source=20):
        """
        모든 소스에서 뉴스를 수집합니다.
        
        Args:
            max_per_source: 소스별 최대 수집 개수
            
        Returns:
            전체 뉴스 항목 리스트
        """
        all_news = []
        
        print("네이버 금융 뉴스 수집 중...")
        all_news.extend(self.fetch_naver_finance_news(max_per_source))
        
        print("네이버 금융 메인 뉴스 수집 중...")
        all_news.extend(self.fetch_naver_main_news(max_per_source // 2))
        
        print("한국경제 뉴스 수집 중...")
        all_news.extend(self.fetch_hankyung_news(max_per_source // 2))
        
        # 중복 제거 (링크 기준)
        seen_links = set()
        unique_news = []
        for item in all_news:
            if item['link'] not in seen_links:
                seen_links.add(item['link'])
                unique_news.append(item)
        
        print(f"총 {len(unique_news)}개 뉴스 수집 완료")
        return unique_news


# 테스트용 코드
if __name__ == "__main__":
    crawler = NewsCrawler()
    
    print("=== 뉴스 크롤링 테스트 ===\n")
    
    news = crawler.fetch_all_news(max_per_source=10)
    
    print(f"\n수집된 뉴스 총 {len(news)}개:\n")
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item['source']}] {item['title']}")
        print(f"   링크: {item['link']}")
        print()
