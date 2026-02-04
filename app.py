import streamlit as st
import pandas as pd
import time
from datetime import datetime
from src.data_manager import DataManager
from src.ai_analyst import AIAnalyst
from src.scheduler import get_scheduler

# Page Config
st.set_page_config(
    page_title="AI 주식 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Scheduler (Singleton)
@st.cache_resource
def init_scheduler():
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler

scheduler = init_scheduler()

# Initialize Managers
# Removed cache to ensure secrets are re-read if added later
def get_managers():
    dm = DataManager()
    # Safely get API key
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY") 
    except Exception:
        api_key = None
    
    ai = AIAnalyst(api_key=api_key) if api_key else None
    return dm, ai

dm, ai = get_managers()

# Styles
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .news-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
    }
    .stButton>button { width: 100%; }
    
    /* Mobile Optimization */
    @media only screen and (max-width: 600px) {
        .big-font { font-size: 20px !important; }
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 18px !important; }
        .stMarkdown p { font-size: 16px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# Main Dashboard Function
def main_dashboard():
    # Increment Visitor Stats
    if 'visited' not in st.session_state:
        dm.increment_visitor_count()
        st.session_state['visited'] = True
    
    stats = dm.load_stats()
    
    st.title("📈 AI 주식 투자 가이드")
    st.caption(f"총 방문자 수: {stats.get('visitors', 0):,}명 | 자동 업데이트 중 (5분 주기)")
    
    # 1. Daily Report Section
    st.header("📢 오늘의 시장 브리핑")
    
    report = None
    if ai:
        report = ai.get_latest_report()
    
    if report:
        # --- Visualization Section ---
        chart_data = ai.extract_chart_data(report['content'])
        if chart_data:
            st.subheader("📊 섹터별 기상도")
            
            import plotly.express as px
            
            # Prepare data for plotting
            df = pd.DataFrame(chart_data)
            
            # Map sentiment to color
            color_map = {"맑음": "#ff4b4b", "흐림": "#4b7bff"} # Red for Bullish, Blue for Bearish
            
            # Handle empty tickers for display
            df['tickers_display'] = df['tickers'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            df['size_display'] = df['score'] * 5 # Scale bubble size
            
            fig = px.scatter(
                df, 
                x="sector", 
                y="score", 
                size="size_display", 
                color="sentiment",
                color_discrete_map=color_map,
                hover_name="sector",
                hover_data={"reason": True, "tickers_display": True, "size_display": False, "score": False, "sector": False},
                text="sector",
                size_max=60,
                height=450 # Slightly taller for legend
            )
            
            fig.update_traces(
                textposition='top center',
                hovertemplate="<b>%{hovertext}</b><br><br>상태: %{marker.color}<br>이유: %{customdata[0]}<br>관련주: %{customdata[1]}"
            )
            
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis={'visible': False}, # Hide X axis labels
                yaxis={'title': '영향력', 'visible': False}, # Hide Y axis too for cleaner look on mobile
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=30, b=10) # Reduce margins
            )
            
            st.plotly_chart(fig, use_container_width=True)
        # -----------------------------

        with st.expander("📄 AI 분석 리포트 상세 보기", expanded=False): # Collapsed by default as Chart is above
            st.markdown(report['content'])
            st.caption(f"생성 시간: {report['timestamp']}")
    else:
        st.info("아직 생성된 리포트가 없습니다. 잠시 후 자동으로 생성됩니다.")

    st.divider()

    # 2. News Feed Section
    st.header("📰 실시간 주요 뉴스")
    news_items = dm.load_news()
    
    if not news_items:
        st.warning("수집된 뉴스가 없습니다.")
    else:
        # Filter/Search
        search_term = st.text_input("뉴스 검색", placeholder="키워드 입력 (예: 반도체, 삼성전자)")
        
        filtered_news = news_items
        if search_term:
            term = search_term.lower()
            filtered_news = [
                n for n in news_items 
                if (n['title'] and term in n['title'].lower()) or 
                   (n.get('summary') and term in n['summary'].lower())
            ]
            
        # Display top 20
        for item in filtered_news[:20]:
            with st.container():
                st.markdown(f"#### [{item['source']}] {item['title']}")
                st.markdown(f"{item.get('published', '')} | {item['category']}")
                if item.get('summary'):
                    summary_clean = item['summary'].replace('<', '(').replace('>', ')') # Basic HTML tag cleaning
                    st.markdown(f"{summary_clean[:200]}..." if len(summary_clean) > 200 else summary_clean)
                st.markdown(f"[기사 원문 보기]({item['link']})")
                st.markdown("---")

# Admin Dashboard Function
def admin_dashboard():
    st.title("🛠 관리자 대시보드")
    
    st.subheader("1. 시스템 상태")
    col_status, col_lastrun, col_nextrun = st.columns(3)
    
    with col_status:
        st.metric("백그라운드 작업", scheduler.status)
        
    with col_lastrun:
        last = scheduler.last_run.strftime('%H:%M:%S') if scheduler.last_run else "없음"
        st.metric("최근 실행", last)
        
    with col_nextrun:
        next_r = scheduler.next_run.strftime('%H:%M:%S') if scheduler.next_run else "대기 중"
        st.metric("다음 실행 예정", next_r)

    st.info("뉴스 수집 및 AI 리포트 생성은 백그라운드에서 5분 주기로 자동 실행됩니다.")
    
    if st.button("새로고침 (상태 확인)"):
        st.rerun()

    st.divider()
    
    st.subheader("2. RSS 피드 관리")
    
    # Pre-defined Presets
    RSS_PRESETS = {
        "직접 입력": "",
        "네이버 금융 (구글뉴스 RSS 대체)": "https://news.google.com/rss/search?q=site:finance.naver.com&hl=ko&gl=KR&ceid=KR:ko", 
        "매일경제 (전체)": "https://www.mk.co.kr/rss/30000001/",
        "한국경제 (증권/금융)": "https://www.hankyung.com/feed/finance",
        "구글 금융 (국내)": "https://news.google.com/rss/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR%3Ako",
        "구글 금융 (미국/글로벌)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWvfSkwyX3qAmDn2BzF4QAxhWjFfM180XzVykAQA?hl=en-US&gl=US&ceid=US:en",
        "TechCrunch (기술/AI)": "https://techcrunch.com/feed/",
    }

    feeds = dm.get_feeds()
    
    # Add New Feed
    with st.form("add_feed_form"):
        st.write("새 RSS 추가")
        
        # Preset Selection
        selected_preset = st.selectbox("추천 피드 선택", list(RSS_PRESETS.keys()))
        
        # Determine initial values based on preset
        default_url = RSS_PRESETS[selected_preset]
        default_name = selected_preset if selected_preset != "직접 입력" else ""
        
        # Input fields (Editable)
        new_name = st.text_input("매체명 (예: 매일경제)", value=default_name)
        new_url = st.text_input("RSS URL", value=default_url)
        new_cat = st.selectbox("카테고리", ["Economy", "Domestic", "Global", "Sector"])
        
        submitted = st.form_submit_button("추가")
        
        if submitted:
            if new_name and new_url:
                dm.add_feed(new_name, new_url, new_cat)
                st.success(f"'{new_name}' 추가 완료!")
                time.sleep(1) # Wait for a bit
                st.rerun()
            else:
                st.error("매체명과 URL을 모두 입력해주세요.")
            
    # List & Delete Feeds
    st.write("등록된 피드 목록")
    for feed in feeds:
        c1, c2, c3, c4 = st.columns([2, 4, 1, 1])
        c1.write(feed['name'])
        c2.write(feed['url'])
        c3.write(feed['category'])
        if c4.button("삭제", key=f"del_{feed['url']}"):
            dm.remove_feed(feed['url'])
            st.rerun()

# Sidebar & Routing
def sidebar():
    st.sidebar.title("메뉴")
    mode = st.sidebar.radio("이동", ["대시보드", "관리자 모드"])
    
    if mode == "대시보드":
        main_dashboard()
    else:
        st.sidebar.divider()
        password = st.sidebar.text_input("관리자 암호", type="password")
        
        # Check password
        correct_password = ""
        try:
            correct_password = st.secrets["ADMIN_PASSWORD"]
        except:
             # Default fallback if secrets not set
            correct_password = "admin"
            
        if password == correct_password:
            admin_dashboard()
        elif password:
            st.sidebar.error("암호가 틀렸습니다.")
        else:
            st.sidebar.info("관리자 암호를 입력하세요.")

if __name__ == "__main__":
    sidebar()
