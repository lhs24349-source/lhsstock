import os
import json
from datetime import datetime
from google import genai
from google.genai import types
import streamlit as st
import time

class AIAnalyst:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash" 

    def _generate_persona_analysis(self, persona_role, persona_prompt, news_text, verbose=True):
        """Helper to generate analysis from a specific persona perspective with retry logic"""
        
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        
        full_prompt = f"""
        현재 날짜는 **{current_date_str}**입니다.
        당신은 {persona_role}입니다.
        아래 뉴스 데이터를 바탕으로 본인의 전문 분야에 집중하여 분석 리포트를 작성해주세요.
        
        **뉴스 데이터:**
        {news_text}
        
        **분석 지침:**
        {persona_prompt}
        
        **출력:**
        핵심 내용을 불렛 포인트로 간결하게 정리해주세요.
        """
        
        max_retries = 3
        base_delay = 2 # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt) # 2s, 4s, 8s
                        if verbose:
                            st.write(f"⏳ 사용량이 많아 대기 중입니다... ({sleep_time}초)")
                        else:
                            print(f"⏳ 사용량이 많아 대기 중입니다... ({sleep_time}초)")
                        time.sleep(sleep_time)
                        continue
                return f"Error ({persona_role}): {error_msg}"
        return f"Error ({persona_role}): Rate limit exceeded after retries."

    def analyze_news(self, news_items, verbose=True):
        if not news_items:
            return "분석할 뉴스가 없습니다."

        # 1. Prepare Data
        # Sort by latest first and take top 50
        sorted_news = sorted(news_items, key=lambda x: x.get('fetched_at', ''), reverse=True)[:50]
        news_text = ""
        for i, item in enumerate(sorted_news):
            news_text += f"{i+1}. [{item['source']}] {item['title']}\n"

        # 2. Multi-Persona Analysis Phase
        # Helper to handle status updates depending on verbose mode
        class DummyStatus:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def write(self, text): 
                if verbose: st.write(text)
                else: print(text)
            def update(self, label, state, expanded): pass

        # Context manager for status
        status_ctx = st.status("🕵️ AI 전문가들이 분석 중입니다...", expanded=True) if verbose else DummyStatus()

        with status_ctx as status:
            
            # Persona A: Macro Economist
            status.write("🌍 거시경제 전문가가 시장 흐름을 읽고 있습니다...")
            macro_prompt = """
            - 환율, 금리, 유가, 전쟁, 외교 분쟁 등 거시 경제 이슈에 집중하세요.
            - 이러한 이슈가 한국 금융 시장 전반에 미칠 영향을 예측하세요.
            - 단기적인 시장 분위기(Bull/Bear)를 진단하세요.
            """
            macro_analysis = self._generate_persona_analysis("거시경제 분석가", macro_prompt, news_text, verbose)
            
            # Persona B: Sector Specialist
            status.write("🏭 산업 분석가가 수혜/피해 업종을 선별 중입니다...")
            sector_prompt = """
            - 뉴스에서 언급된 특정 산업(반도체, 2차전지, 자동차, 방산 등)을 식별하세요.
            - 각 이슈에 따른 수혜 업종과 악재 업종을 명확히 구분하세요.
            - 구체적인 종목명(Ticker)이 있다면 포함하세요.
            """
            sector_analysis = self._generate_persona_analysis("산업/섹터 전문 애널리스트", sector_prompt, news_text, verbose)

            # Persona C: Risk Manager
            status.write("⚠️ 리스크 관리자가 위험 요소를 점검 중입니다...")
            risk_prompt = """
            - 투자자가 간과하기 쉬운 위험 요소나 악재를 비판적으로 분석하세요.
            - '묻지마 투자'를 경계할 수 있도록 구체적인 리스크 시나리오를 제시하세요.
            - 현재 시장에서 '관망'이 필요한 섹터가 있다면 경고하세요.
            """
            risk_analysis = self._generate_persona_analysis("리스크 관리자", risk_prompt, news_text, verbose)

            # 3. Synthesis Phase
            status.write("📝 수석 전략가가 최종 리포트를 작성 중입니다...")
            final_prompt = f"""
            당신은 투자 자문 회사의 **수석 투자 전략가(Chief Investment Officer)**입니다.
            당신의 산하에 있는 세 명의 전문가(거시경제, 섹터, 리스크)가 제출한 보고서를 종합하여 최종 **'오늘의 주가 가이드 리포트'**를 작성하세요.

            ---
            **[전문가 보고서 1: 거시경제]**
            {macro_analysis}

            **[전문가 보고서 2: 섹터 분석]**
            {sector_analysis}

            **[전문가 보고서 3: 리스크 관리]**
            {risk_analysis}
            ---

            **작성 요구사항:**
            1. 세 보고서의 내용을 논리적으로 통합하세요. (단순 나열 금지, 유기적 연결)
            2. 서로 상충되는 의견이 있다면, 더 보수적이고 안전한 관점을 채택하거나 양측의 근거를 비교하세요.
            3. 최종 출력은 아래 Markdown 형식을 엄격히 따르세요.

            **최종 리포트 형식 (Markdown):**
            # 📈 AI 주식 투자 가이드 ({datetime.now().strftime('%Y-%m-%d')})

            ## 🌍 시장 날씨 & 핵심 이슈
            > 한 줄 요약: (예: "미국 금리 인하 기대감에 훈풍, 반도체 주목")
            * (거시 경제 분석 요약)

            ## 🏭 섹터별 기상도
            ### ☀️ 맑음 (수혜 예상)
            * **[섹터/테마]**: 이유 요약
              * *관련주: 삼성전자, SK하이닉스...*
            
            ### ☔ 흐림 (주의 필요)
            * **[섹터/테마]**: 이유 요약
              * *관련주: ...*

            ## ⚠️ 리스크 체크
            * (리스크 관리자의 핵심 경고 사항)

            ## 💡 수석 전략가의 투자 제언
            * (매수/매도/관망 등 구체적 포지션 제안)

            ---
            **[중요: 시각화를 위한 JSON 데이터]**
            **리포트의 맨 마지막**에 아래 형식의 JSON 데이터를 포함해주세요. 이 데이터는 차트 생성에 사용됩니다.
            반드시 Markdown 코드 블록(\`\`\`json ... \`\`\`) 안에 작성하세요.
            
            ```json
            [
              {{
                "sector": "반도체",
                "sentiment": "맑음",  // "맑음" 또는 "흐림"
                "score": 8,           // 맑음이면 6~10, 흐림이면 1~5 (영향력 크기)
                "reason": "AI 수요 증가",
                "tickers": ["삼성전자", "SK하이닉스"] // 뉴스에 언급된 실제 종목명
              }},
              {{
                "sector": "2차전지",
                "sentiment": "흐림",
                "score": 3,
                "reason": "전기차 수요 둔화",
                "tickers": ["LG에너지솔루션", "에코프로"]
              }}
            ]
            ```
            """

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=final_prompt
                )
                final_report = response.text
                if verbose:
                    status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                return final_report
            except Exception as e:
                return f"Final Synthesis Error: {str(e)}"

    def extract_chart_data(self, report_text):
        """Extracts JSON block from the report text for visualization"""
        import re
        try:
            match = re.search(r'```json\s*([\s\S]*?)\s*```', report_text)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
        except Exception:
            pass
        return []

    def save_report(self, report_content):
        # Save to reports.json with timestamp
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        reports_file = os.path.join(data_dir, 'reports.json')
        
        new_report = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "timestamp": datetime.now().isoformat(),
            "content": report_content
        }

        try:
            if os.path.exists(reports_file):
                with open(reports_file, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
            else:
                reports = []
            
            # Prepend new report
            reports.insert(0, new_report)
            # Keep last 30 reports
            reports = reports[:30]

            with open(reports_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False

    def get_latest_report(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        reports_file = os.path.join(data_dir, 'reports.json')
        if os.path.exists(reports_file):
            with open(reports_file, 'r', encoding='utf-8') as f:
                reports = json.load(f)
                if reports:
                    return reports[0]
        return None
