# 📈 AI Stock Analysis Dashboard

이 프로젝트는 RSS 피드를 통해 주식 관련 뉴스를 수집하고, Google Gemini API를 활용해 거시 경제 및 섹터별 이슈를 분석하여 "오늘의 주가 가이드"를 제공하는 대시보드입니다.

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
* **📊 섹터별 기상도**: AI 분석 데이터를 기반으로 섹터별 호재(붉은색)/악재(푸른색)를 버블 차트로 시각화합니다.
* **오늘의 시장 브리핑**: 거시 경제, 섹터 분석, 리스크 관리, 투자 제언이 담긴 AI 리포트입니다.
* **실시간 주요 뉴스**: 수집된 뉴스를 빠르게 검색하고 원문을 확인할 수 있습니다.

### 관리자 모드
* **비밀번호 인증**: `secrets.toml`에 설정한 암호로 접속합니다.
* **시스템 상태 모니터링**: 백그라운드에서 실행되는 뉴스 수집 및 AI 분석 스케줄러의 상태를 확인합니다.
* **RSS 피드 관리**: '네이버 금융', '구글 금융' 등 뉴스 소스를 추가하거나 삭제할 수 있습니다.
