# 📈 AI Stock Analysis Dashboard

이 프로젝트는 **네이버 금융**을 직접 크롤링하여 주식 관련 뉴스를 수집하고, Google Gemini API를 활용해 거시 경제 및 섹터별 이슈를 분석하여 "오늘의 주가 가이드"를 제공하는 대시보드입니다.

## 🛠 설치 및 실행 방법 (로컬)

### 1. 환경 설정
1. 파이썬 가상환경 생성 및 활성화
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. 필요 라이브러리 설치
   ```bash
   pip install -r requirements.txt
   ```

### 2. API 키 설정
`.streamlit/secrets.toml` 파일을 열고 본인의 Google Gemini API 키와 관리자 비밀번호를 입력하세요.

```toml
# .streamlit/secrets.toml
GOOGLE_API_KEY = "여기에_API_키_입력"
ADMIN_PASSWORD = "admin"  # 원하는 관리자 암호로 변경
```

### 3. 프로그램 실행
```bash
streamlit run app.py
```

## ☁️ 배포 방법 (외부 접속용 - Streamlit Cloud)
이 앱을 모바일이나 타 PC에서 접속하려면 무료 호스팅 서비스인 **Streamlit Community Cloud**에 배포해야 합니다.

### 1단계: GitHub에 코드 올리기
1. [GitHub](https://github.com/)에 로그인하고 새 리포지토리(Repository)를 생성합니다 (예: `stock-dashboard`).
2. 아래 명령어로 코드를 푸시합니다.
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/[본인아이디]/stock-dashboard.git
   git push -u origin main
   ```

### 2단계: Streamlit Cloud 연동
1. [Streamlit Share](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. 'New app' 버튼을 클릭합니다.
3. 방금 생성한 리포지토리(`stock-dashboard`)와 파일 경로(`app.py`)를 선택하고 'Deploy!'를 클릭합니다.

### 3단계: 비밀키(Secrets) 설정 (중요!)
Streamlit Cloud는 로컬의 `secrets.toml` 파일을 읽지 못하므로, 클라우드 설정에 키를 등록해야 합니다.
1. 배포된 앱 화면 우측 하단의 **'Manage app'** 버튼 클릭.
2. 세로 점 3개(`⋮`) 클릭 -> **Settings** -> **Secrets**.
3. 아래 내용을 복사하여 붙여넣고 저장합니다.
   ```toml
   GOOGLE_API_KEY = "본인의_API_키"
   ADMIN_PASSWORD = "admin"
   ```

이제 생성된 URL(예: `https://stock-dashboard.streamlit.app`)로 어디서든 접속할 수 있습니다!

## 🖥 기능 설명

### 메인 화면
* **📊 섹터별 기상도**: AI 토론 결과를 기반으로 섹터별 호재(붉은색)/악재(푸른색)를 시각화합니다.
* **🤖 AI 토론 상세**: 3명의 AI 전문가(낙관/비관/중립)의 치열한 토론 과정과 최종 결론을 보여줍니다.
* **📰 관련 뉴스**: 섹터별 기상도에 언급된 이슈와 관련된 뉴스만 선별하여 제공합니다.
* **🎬 AI 토론 실행**: 관리자 인증을 통해 수동으로 AI 토론을 실행할 수 있습니다.

### 관리자 모드
* **비밀번호 인증**: `secrets.toml`에 설정한 암호로 접속합니다.
* **시스템 상태 모니터링**: 백그라운드에서 실행되는 뉴스 수집 및 AI 분석 스케줄러의 상태를 확인합니다 (10분 주기).
* **뉴스 소스 현황**: 크롤링 중인 뉴스 소스 및 수집 통계를 확인할 수 있습니다.

## 🤖 AI 토론 시스템

**멀티 턴 토론 방식**으로 더 깊이 있고 균형 잡힌 투자 분석을 제공합니다.

### 토론 참가 AI
| AI | 역할 | 관점 |
|-----|------|------|
| 🐂 **Bull AI** | 낙관론자 | 기회 요인 발굴, 상승 섹터 추천 |
| 🐻 **Bear AI** | 비관론자 | 리스크 분석, 주의 섹터 경고 |
| 📊 **Analyst AI** | 중립 분석가 | 데이터 기반 객관적 분석 |
| 🎯 **Moderator AI** | 수석 전략가 | 토론 종합, 최종 투자 가이드 |

### 토론 진행
1. **Round 1 - 개별 분석**: 각 AI가 금일 뉴스를 바탕으로 독립적인 분석 수행
2. **Round 2 - 상호 반박**: Bull과 Bear가 서로의 의견에 반론, Analyst가 양측 검증
3. **Final - 종합**: Moderator가 토론 내용을 종합하여 최종 리포트 작성

> ⚠️ **비용 주의**: AI 토론은 API 호출이 많습니다. 메인 화면 하단에서 관리자 암호를 입력하여 수동으로 실행할 수 있습니다. 이미 완료된 토론은 "최근 토론 결과 보기" 버튼으로 무료로 확인할 수 있습니다.

## 📰 뉴스 수집 소스
* **네이버 금융** - 시장/종목/공시 뉴스 (직접 크롤링)
* **한국경제** - 증권 뉴스 (직접 크롤링)
