import threading
import time
import datetime
import streamlit as st
from src.data_manager import DataManager
from src.ai_analyst import AIAnalyst

class BackgroundScheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BackgroundScheduler, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.interval = 600  # 10 minutes (600 seconds)
        self.is_running = False
        self.thread = None
        self.last_run = None
        self.next_run = None
        self.status = "Stopped"
        
        # Initialize managers
        self.dm = DataManager()
        # API Key might be loaded later or passed, but for bg task we need it from secrets
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
        except:
            api_key = None
            
        self.ai = AIAnalyst(api_key=api_key) if api_key else None

    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.status = "Running"
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[{datetime.datetime.now()}] Background Scheduler Started")

    def stop(self):
        self.is_running = False
        self.status = "Stopped"
        if self.thread:
            self.thread.join(timeout=1)

    def _run_loop(self):
        while self.is_running:
            self.status = "Processing..."
            try:
                self._execute_job()
                self.last_run = datetime.datetime.now()
                self.next_run = self.last_run + datetime.timedelta(seconds=self.interval)
                self.status = f"Waiting (Next run: {self.next_run.strftime('%H:%M:%S')})"
            except Exception as e:
                print(f"Scheduler Error: {e}")
                self.status = f"Error: {str(e)}"
            
            # Sleep in small chunks to allow stopping
            for _ in range(self.interval):
                if not self.is_running:
                    break
                time.sleep(1)
            
            # Initial run might have just finished, loop again

    def _execute_job(self):
        print(f"[{datetime.datetime.now()}] Executing Background Job...")
        
        # 1. Fetch News
        new_count = self.dm.fetch_and_update_news()
        print(f"  - Fetched {new_count} new items")
        
        # 2. Analyze if there are news and AI is available
        if self.ai:
            news = self.dm.load_news()
            if news:
                print("  - analyzing news...")
                # Simple check to avoid re-analyzing if nothing changed? 
                # For now, just analyze periodically as requested.
                # Maybe optimization: check if latest news is newer than last report?
                # User asked for "periodic", so we just do it.
                
                analysis_text = self.ai.analyze_news(news, verbose=False)
                if "오류" not in analysis_text and "Error" not in analysis_text:
                    self.ai.save_report(analysis_text)
                    print("  - Report saved successfully")
                else:
                    print(f"  - Analysis failed: {analysis_text}")
            else:
                print("  - No news to analyze")
        else:
            print("  - AI not initialized (No Key)")

def get_scheduler():
    return BackgroundScheduler()
