import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from src.data_manager import DataManager
from src.ai_analyst import AIAnalyst
from src.scheduler import get_scheduler
from src.ai_debate_engine import AIDebateEngine

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

import json
import os
import re

# Helper: Load Latest Debate (without API key requirement for viewing)
def load_latest_debate():
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        debates_file = os.path.join(data_dir, 'debates.json')
        if os.path.exists(debates_file):
            with open(debates_file, 'r', encoding='utf-8') as f:
                debates = json.load(f)
                if debates:
                    return debates[0]
    except Exception as e:
        print(f"Error loading debate: {e}")
    return None

# Helper: Extract Chart Data (Standalone)
def extract_chart_data_text(text):
    try:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
    except:
        pass
    return []

# Main Dashboard Function
def main_dashboard():
    # Increment Visitor Stats
    if 'visited' not in st.session_state:
        dm.increment_visitor_count()
        st.session_state['visited'] = True
    
    stats = dm.load_stats()
    
    st.title("📈 AI 주식 투자 가이드")
    st.caption(f"총 방문자 수: {stats.get('visitors', 0):,}명")
    
    # 0. Manual Debate Execution (Admin) - Moved to Top
    with st.expander("🎬 AI 토론 실행 (관리자)", expanded=True):
        st.info("""
        **AI 토론 시스템**: 3개의 AI(🐂 Bull, 🐻 Bear, 📊 Analyst)가 오늘의 뉴스를 바탕으로 토론하고,
        🎯 Moderator AI가 최종 종합 리포트를 생성합니다. (약 3분 소요)
        """)
        
        # 금일 뉴스 필터링
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        news_items_all = dm.load_news()
        today_news = []
        
        if news_items_all:
            for item in news_items_all:
                try:
                    fetched_at = item.get('fetched_at', '')
                    if fetched_at:
                        news_time = datetime.fromisoformat(fetched_at.replace('Z', '+00:00').split('+')[0])
                        if news_time >= today_start:
                            today_news.append(item)
                except:
                    continue
        
        st.write(f"📅 **금일 수집된 뉴스**: {len(today_news)}개")

        # API Key check
        api_key_check = None
        try:
            api_key_check = st.secrets.get("GOOGLE_API_KEY")
        except:
            pass
            
        if not api_key_check:
            st.warning("⚠️ API 키가 설정되지 않았습니다.")
        elif len(today_news) < 5:
            st.warning("⚠️ 토론을 실행하려면 최소 5개 이상의 금일 뉴스가 필요합니다.")
        else:
            with st.form("debate_auth_form"):
                col_pass, col_btn = st.columns([3, 1])
                with col_pass:
                    password = st.text_input("관리자 암호", type="password", label_visibility="collapsed", placeholder="관리자 암호 입력")
                with col_btn:
                    submit = st.form_submit_button("🚀 토론 시작", use_container_width=True)
                
                if submit:
                    correct_password = ""
                    try:
                        correct_password = st.secrets["ADMIN_PASSWORD"]
                    except:
                        correct_password = "admin"
                    
                    if password == correct_password:
                        st.success("인증 성공! 토론을 시작합니다...")
                        run_ai_debate(api_key_check, today_news)
                    else:
                        st.error("암호가 틀렸습니다.")

    st.divider()
    
    # Load Data
    latest_debate = load_latest_debate()
    chart_data = []
    
    if latest_debate:
        chart_data = extract_chart_data_text(latest_debate.get('final_report', ''))

    # 1. Sector Chart (Based on Debate)
    st.header("📊 섹터별 기상도 (AI 토론 기반)")
    
    if chart_data:
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
            height=450
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
            xaxis={'visible': False}, 
            yaxis={'title': '영향력', 'visible': False}, 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"분석 기준: {latest_debate.get('timestamp', '')[:16].replace('T', ' ')}")
        
        # 2. AI Debate Result (Placed directly below Chart)
        st.divider()
        st.subheader("🤖 AI 토론 상세 결과")
        display_debate_result(latest_debate)
        
        # 3. Related News (Filtered by Keywords)
        st.divider()
        st.subheader("📰 관련 뉴스 (섹터 이슈)")
        
        # Extract keywords from chart data
        keywords = set()
        for item in chart_data:
            keywords.add(item['sector'])
            if 'tickers' in item:
                keywords.update(item['tickers'])
        
        # Filter news
        news_items = dm.load_news()
        related_news = []
        if news_items:
            for n in news_items:
                # Basic keyword matching
                text = (n['title'] + " " + n.get('summary', '')).lower()
                for k in keywords:
                    if k.lower() in text:
                        related_news.append(n)
                        break
        
        if related_news:
            # CSS for News Links
            st.markdown("""
            <style>
            .news-link {
                font-size: 15px !important;
                text-decoration: none;
                color: #31333F;
                display: block;
                padding: 4px 0;
            }
            .news-link:hover {
                text-decoration: underline;
                color: #ff4b4b;
            }
            .news-source {
                font-size: 12px;
                color: #888;
                margin-left: 8px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display titles only with link
            for item in related_news[:20]:
                st.markdown(f'''
                <a href="{item['link']}" target="_blank" class="news-link">
                    📄 {item['title']} <span class="news-source">[{item['source']}]</span>
                </a>
                ''', unsafe_allow_html=True)
        else:
            st.info("현재 섹터와 관련된 뉴스가 없습니다.")
            
    else:
        st.info("아직 생성된 AI 토론 결과가 없습니다. 상단에서 토론을 실행해주세요.")

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

    st.info("뉴스 수집 및 AI 리포트 생성은 백그라운드에서 10분 주기로 자동 실행됩니다.")
    
    if st.button("새로고침 (상태 확인)"):
        st.rerun()

    st.divider()
    
    st.subheader("2. 뉴스 소스 현황")
    
    # 현재 크롤링 소스 표시
    st.info("""
    📰 **현재 뉴스 수집 소스** (자동 크롤링)
    
    - **네이버 금융** - 시장/종목/공시 뉴스
    - **한국경제** - 증권 뉴스
    
    RSS 피드 대신 직접 크롤링 방식을 사용하여 더 안정적으로 뉴스를 수집합니다.
    """)
    
    # 수집된 뉴스 통계
    news_items = dm.load_news()
    if news_items:
        col1, col2, col3 = st.columns(3)
        
        # 소스별 통계
        source_counts = {}
        for item in news_items:
            source = item.get('source', '기타')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        with col1:
            st.metric("총 뉴스", f"{len(news_items)}개")
        
        with col2:
            # 가장 최근 뉴스 시간
            latest = news_items[0].get('fetched_at', '알 수 없음')
            if latest and len(latest) > 16:
                latest = latest[:16].replace('T', ' ')
            st.metric("최근 수집", latest)
        
        with col3:
            st.metric("소스 수", f"{len(source_counts)}개")
        
        # 소스별 상세
        st.write("**소스별 뉴스 수:**")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- {source}: {count}개")


def run_ai_debate(api_key, news_items):
    """수동으로 AI 토론 실행"""
    debate_engine = AIDebateEngine(api_key=api_key)
    
    # 진행 상황 표시용 placeholder
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_callback(message, progress):
        status_text.write(message)
        progress_bar.progress(progress)
    
    with st.spinner("🤖 AI들이 토론 중입니다... (약 2~3분 소요)"):
        debate_result = debate_engine.run_debate(news_items, progress_callback)
    
    # 결과 저장
    if "error" not in debate_result:
        debate_engine.save_debate_log(debate_result)
        st.success("✅ 토론 완료! 결과가 저장되었습니다.")
        
        # 결과 표시
        display_debate_result(debate_result)
    else:
        st.error(f"❌ 토론 실패: {debate_result['error']}")


def show_latest_debate(api_key):
    """최근 토론 기록 표시"""
    debate_engine = AIDebateEngine(api_key=api_key)
    latest = debate_engine.get_latest_debate()
    
    if latest:
        st.info(f"📌 최근 토론: {latest.get('timestamp', '?')[:16].replace('T', ' ')}")
        display_debate_result(latest)
    else:
        st.warning("아직 토론 기록이 없습니다.")


def display_debate_result(debate_result):
    """토론 결과 표시"""
    
    # Round 1: 개별 분석
    if debate_result.get('rounds'):
        round1 = debate_result['rounds'][0] if len(debate_result['rounds']) > 0 else None
        round2 = debate_result['rounds'][1] if len(debate_result['rounds']) > 1 else None
        
        with st.expander("🎬 Round 1: 개별 분석", expanded=False):
            if round1:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 🐂 Bull AI")
                    st.markdown(round1['opinions'].get('bull', '내용 없음'))
                
                with col2:
                    st.markdown("### 🐻 Bear AI")
                    st.markdown(round1['opinions'].get('bear', '내용 없음'))
                
                with col3:
                    st.markdown("### 📊 Analyst AI")
                    st.markdown(round1['opinions'].get('analyst', '내용 없음'))
        
        with st.expander("⚔️ Round 2: 상호 반박", expanded=False):
            if round2:
                st.markdown("#### 🐂 Bull의 반박")
                st.markdown(round2['opinions'].get('bull_rebuttal', '내용 없음'))
                
                st.divider()
                
                st.markdown("#### 🐻 Bear의 반박")
                st.markdown(round2['opinions'].get('bear_rebuttal', '내용 없음'))
                
                st.divider()
                
                st.markdown("#### 📊 Analyst의 검증")
                st.markdown(round2['opinions'].get('analyst_verdict', '내용 없음'))
    
    # 최종 리포트
    if debate_result.get('final_report'):
        st.markdown("---")
        st.markdown("## 🎯 최종 토론 결과 리포트")
        st.markdown(debate_result['final_report'])

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
