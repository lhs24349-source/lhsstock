"""
AI 토론 엔진 모듈

여러 AI 페르소나(Bull, Bear, Analyst)가 토론하고
Moderator가 최종 종합하는 멀티 턴 토론 시스템
"""

import json
import os
from datetime import datetime, timedelta
from google import genai
import time


class AIDebateEngine:
    """
    AI 토론 엔진
    
    Bull(낙관론자), Bear(비관론자), Analyst(중립분석가)가 토론하고
    Moderator(진행자)가 최종 종합 리포트를 생성합니다.
    """
    
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        
        # 토론 라운드 수 (2~3턴 권장)
        self.debate_rounds = 2
        
        # 각 페르소나 정의
        self.personas = {
            "bull": {
                "name": "🐂 Bull AI (낙관론자)",
                "emoji": "🐂",
                "system_prompt": """당신은 항상 기회를 찾는 낙관적 투자 전문가입니다.
- 뉴스에서 긍정적 신호와 투자 기회를 발굴하세요
- 상승 가능성이 있는 섹터와 종목을 추천하세요
- 단, 근거 없는 낙관은 금지. 뉴스 데이터에 기반하세요.
- 간결하게 핵심만 불렛 포인트로 정리하세요."""
            },
            "bear": {
                "name": "🐻 Bear AI (비관론자)",
                "emoji": "🐻",
                "system_prompt": """당신은 리스크를 꿰뚫어보는 보수적 투자 전문가입니다.
- 시장의 위험 신호와 숨겨진 악재를 찾아내세요
- 과열된 섹터나 피해야 할 종목을 경고하세요
- 근거 있는 비관만 제시하세요.
- 간결하게 핵심만 불렛 포인트로 정리하세요."""
            },
            "analyst": {
                "name": "📊 Analyst AI (중립 분석가)",
                "emoji": "📊",
                "system_prompt": """당신은 데이터 기반의 중립적 시장 분석가입니다.
- 감정을 배제하고 오직 데이터와 팩트에 집중하세요
- 뉴스의 영향력을 정량적으로 평가하세요
- Bull과 Bear 양측의 주장을 검증하세요.
- 간결하게 핵심만 불렛 포인트로 정리하세요."""
            },
            "moderator": {
                "name": "🎯 Moderator AI (수석 전략가)",
                "emoji": "🎯",
                "system_prompt": """당신은 투자 자문사의 수석 전략가입니다.
- Bull, Bear, Analyst의 의견을 종합하세요
- 상충되는 의견이 있다면 더 설득력 있는 근거를 채택하세요
- 최종 투자 가이드를 작성하세요"""
            }
        }
    
    def _call_ai(self, prompt, max_retries=3):
        """AI 호출 (재시도 로직 포함)"""
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt)
                        print(f"⏳ API 한도 초과, {sleep_time}초 대기 중...")
                        time.sleep(sleep_time)
                        continue
                return f"Error: {error_msg}"
        return "Error: API 호출 실패"
    
    def run_debate(self, news_items, progress_callback=None):
        """
        토론 실행
        
        Args:
            news_items: 뉴스 항목 리스트
            progress_callback: 진행 상황 콜백 함수 (message, progress)
            
        Returns:
            토론 결과 딕셔너리
        """
        if not news_items:
            return {"error": "토론할 뉴스 데이터가 없습니다."}
        
        # 뉴스 텍스트 준비
        news_text = self._prepare_news_text(news_items)
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        debate_log = {
            "timestamp": datetime.now().isoformat(),
            "news_count": len(news_items),
            "rounds": []
        }
        
        # ========== Round 1: 개별 분석 ==========
        if progress_callback:
            progress_callback("🎬 Round 1: 각 AI가 개별 분석 중...", 0.1)
        
        round1 = {"round": 1, "title": "개별 분석", "opinions": {}}
        
        # Bull AI 분석
        if progress_callback:
            progress_callback("🐂 Bull AI가 기회 요인을 분석 중...", 0.15)
        
        bull_prompt = f"""현재 시간: {current_date}
{self.personas['bull']['system_prompt']}

**오늘의 뉴스 데이터:**
{news_text}

위 뉴스를 바탕으로 투자 기회를 분석해주세요."""
        
        round1["opinions"]["bull"] = self._call_ai(bull_prompt)
        time.sleep(1)  # API 호출 간격
        
        # Bear AI 분석
        if progress_callback:
            progress_callback("🐻 Bear AI가 리스크를 분석 중...", 0.25)
        
        bear_prompt = f"""현재 시간: {current_date}
{self.personas['bear']['system_prompt']}

**오늘의 뉴스 데이터:**
{news_text}

위 뉴스를 바탕으로 리스크와 주의사항을 분석해주세요."""
        
        round1["opinions"]["bear"] = self._call_ai(bear_prompt)
        time.sleep(1)
        
        # Analyst AI 분석
        if progress_callback:
            progress_callback("📊 Analyst AI가 중립 분석 중...", 0.35)
        
        analyst_prompt = f"""현재 시간: {current_date}
{self.personas['analyst']['system_prompt']}

**오늘의 뉴스 데이터:**
{news_text}

위 뉴스를 바탕으로 객관적인 시장 분석을 해주세요."""
        
        round1["opinions"]["analyst"] = self._call_ai(analyst_prompt)
        
        debate_log["rounds"].append(round1)
        
        # ========== Round 2: 상호 반박 ==========
        if progress_callback:
            progress_callback("⚔️ Round 2: AI들이 서로의 의견에 반박 중...", 0.45)
        
        round2 = {"round": 2, "title": "상호 반박", "opinions": {}}
        time.sleep(1)
        
        # Bull이 Bear 의견에 반박
        if progress_callback:
            progress_callback("🐂 Bull AI가 Bear의 의견에 반론 중...", 0.5)
        
        bull_rebuttal_prompt = f"""당신은 낙관적 투자 전문가입니다.
Bear AI가 다음과 같은 리스크를 제시했습니다:

**Bear AI 의견:**
{round1['opinions']['bear']}

이 의견의 과장되거나 잘못된 부분을 지적하고, 왜 시장이 여전히 기회가 있는지 반박해주세요.
단, 근거 없는 반박은 금지. 논리적으로 설명하세요."""
        
        round2["opinions"]["bull_rebuttal"] = self._call_ai(bull_rebuttal_prompt)
        time.sleep(1)
        
        # Bear가 Bull 의견에 반박
        if progress_callback:
            progress_callback("🐻 Bear AI가 Bull의 의견에 반론 중...", 0.6)
        
        bear_rebuttal_prompt = f"""당신은 보수적 투자 전문가입니다.
Bull AI가 다음과 같은 기회를 제시했습니다:

**Bull AI 의견:**
{round1['opinions']['bull']}

이 의견의 낙관적인 부분의 위험성을 지적하고, 왜 주의가 필요한지 반박해주세요.
단, 근거 없는 비관은 금지. 논리적으로 설명하세요."""
        
        round2["opinions"]["bear_rebuttal"] = self._call_ai(bear_rebuttal_prompt)
        time.sleep(1)
        
        # Analyst가 양측 검증
        if progress_callback:
            progress_callback("📊 Analyst AI가 양측 의견을 검증 중...", 0.7)
        
        analyst_verify_prompt = f"""당신은 중립적 시장 분석가입니다.
Bull과 Bear의 논쟁을 검토해주세요.

**Bull AI 원래 의견:**
{round1['opinions']['bull']}

**Bear AI 원래 의견:**
{round1['opinions']['bear']}

**Bull의 반박:**
{round2['opinions']['bull_rebuttal']}

**Bear의 반박:**
{round2['opinions']['bear_rebuttal']}

객관적으로 누구의 주장이 더 설득력 있는지, 양측이 합의할 수 있는 부분은 무엇인지 분석해주세요."""
        
        round2["opinions"]["analyst_verdict"] = self._call_ai(analyst_verify_prompt)
        
        debate_log["rounds"].append(round2)
        
        # ========== Final: Moderator 종합 ==========
        if progress_callback:
            progress_callback("🎯 Moderator AI가 최종 리포트 작성 중...", 0.85)
        
        time.sleep(1)
        
        final_prompt = f"""당신은 투자 자문사의 **수석 투자 전략가(CIO)**입니다.
오늘 진행된 AI 토론 내용을 종합하여 최종 투자 가이드를 작성하세요.

=== 토론 기록 ===

**[Round 1: 개별 분석]**

🐂 Bull AI:
{round1['opinions']['bull']}

🐻 Bear AI:
{round1['opinions']['bear']}

📊 Analyst AI:
{round1['opinions']['analyst']}

**[Round 2: 상호 반박]**

🐂 Bull의 반박:
{round2['opinions']['bull_rebuttal']}

🐻 Bear의 반박:
{round2['opinions']['bear_rebuttal']}

📊 Analyst의 검증:
{round2['opinions']['analyst_verdict']}

=== 작성 요구사항 ===
1. 토론 내용을 논리적으로 통합하세요
2. 합의된 사항과 논쟁 사항을 구분하세요
3. 최종 투자 제언을 명확히 제시하세요
4. 신뢰도 점수(1~10)를 평가하세요

**최종 리포트 형식 (Markdown):**

# 📈 AI 토론 결과 리포트 ({datetime.now().strftime('%Y-%m-%d %H:%M')})

## 🤝 합의 사항
* (Bull, Bear, Analyst가 동의한 내용)

## ⚔️ 논쟁 사항
* (의견이 갈린 부분과 각자의 입장)

## 🏭 섹터별 기상도
### ☀️ 맑음 (수혜 예상)
* **[섹터명]**: 이유
  * *관련주: ...*

### ☔ 흐림 (주의 필요)
* **[섹터명]**: 이유
  * *관련주: ...*

## 🎯 최종 투자 제언
* (구체적인 매수/매도/관망 제안)
* **신뢰도 점수: X/10** (근거 설명)

---
**[시각화용 JSON 데이터]**
```json
[
  {{"sector": "반도체", "sentiment": "맑음", "score": 8, "reason": "이유", "tickers": ["삼성전자"]}},
  {{"sector": "2차전지", "sentiment": "흐림", "score": 4, "reason": "이유", "tickers": ["LG에너지솔루션"]}}
]
```
"""

        final_report = self._call_ai(final_prompt)
        debate_log["final_report"] = final_report
        
        if progress_callback:
            progress_callback("✅ 토론 완료!", 1.0)
        
        return debate_log
    
    def _prepare_news_text(self, news_items):
        """뉴스 항목을 텍스트로 변환"""
        sorted_news = sorted(news_items, key=lambda x: x.get('fetched_at', ''), reverse=True)[:50]
        
        text = ""
        for i, item in enumerate(sorted_news, 1):
            text += f"{i}. [{item.get('source', '출처없음')}] {item.get('title', '제목없음')}\n"
        
        return text
    
    def save_debate_log(self, debate_log):
        """토론 기록 저장"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        debates_file = os.path.join(data_dir, 'debates.json')
        
        try:
            if os.path.exists(debates_file):
                with open(debates_file, 'r', encoding='utf-8') as f:
                    debates = json.load(f)
            else:
                debates = []
            
            debates.insert(0, debate_log)
            debates = debates[:10]  # 최근 10개만 유지
            
            with open(debates_file, 'w', encoding='utf-8') as f:
                json.dump(debates, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving debate log: {e}")
            return False
    
    def get_latest_debate(self):
        """최근 토론 기록 가져오기"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        debates_file = os.path.join(data_dir, 'debates.json')
        
        if os.path.exists(debates_file):
            with open(debates_file, 'r', encoding='utf-8') as f:
                debates = json.load(f)
                if debates:
                    return debates[0]
        return None


# 테스트용 코드
if __name__ == "__main__":
    print("AI 토론 엔진 모듈 로드 성공")
