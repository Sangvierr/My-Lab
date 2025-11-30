from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from datetime import datetime

# 1. Airflow 변수 가져오기 (없으면 기본값 사용)
WIN_IP = Variable.get("WIN_SERVER_IP")
MAC_IP = Variable.get("MAC_SERVER_IP",)
MODEL_NAME_VAR = Variable.get("OLLAMA_MODEL", default_var="qwen3:4b")

# 2. API 주소 조합
OLLAMA_API_URL = f"http://{WIN_IP}:11434/api/generate"
JAVA_API_URL = f"http://{MAC_IP}:8090/api/news"

with DAG(
    dag_id="02_naver_news_scraper",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mylab", "ai_pipeline"],
) as dag:

    # ---------------------------------------------------------
    # 1. 뉴스 크롤링 (네이버 IT 랭킹뉴스)
    # ---------------------------------------------------------
    @task.virtualenv(
        task_id="scrape_naver_it_news",
        requirements=["requests", "beautifulsoup4"],
        system_site_packages=False
    )
    def scrape_news():
        import requests
        from bs4 import BeautifulSoup
        import time

        print("📡 [시작] 네이버 IT 뉴스 크롤링을 시작합니다.")
        
        url = "https://news.naver.com/main/ranking/popularDay.naver?mid=etc&sid1=105"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            news_boxes = soup.select('.rankingnews_box')
        except Exception as e:
            print(f"❌ [에러] 랭킹 페이지 접속 실패: {e}")
            return []
        
        results = []
        
        if news_boxes:
            target_box = news_boxes[0]
            articles = target_box.select('li a')
            
            # 상위 3개만 수집
            for i, article in enumerate(articles[:1]): 
                title = article.text.strip()
                link = article['href']
                content = ""
                
                print(f"📡 [요청] 기사 접속 중: {title[:15]}...")
                
                try:
                    res = requests.get(link, headers=headers)
                    bs = BeautifulSoup(res.text, 'html.parser')
                    # 네이버 뉴스 본문 영역
                    content_area = bs.select_one('#dic_area')
                    
                    if content_area:
                        content = content_area.get_text(strip=True)
                        print(f"✅ [수집] 본문 크롤링 성공 ({len(content)}자)")
                    else:
                        print(f"❌ [실패] 본문 요소를 찾을 수 없음")
                except Exception as e:
                    print(f"❌ [에러] 기사 접속 실패: {e}")

                if content:
                    results.append({'rank': i+1, 'title': title, 'link': link, 'content': content})
                    time.sleep(0.5)
        else:
            print("❌ [실패] 랭킹 뉴스 박스를 찾지 못했습니다.")

        print(f"✅ [완료] 총 {len(results)}건의 기사를 수집했습니다.")
        return results

    # ---------------------------------------------------------
    # 2. AI 요약 (Ollama)
    # ---------------------------------------------------------
    @task.virtualenv(
        task_id="summarize_with_ollama",
        requirements=["requests"],
        system_site_packages=False
    )
    def summarize_news(news_list: list, api_url: str, model_name: str):
        import requests
        import json

        print(f"📡 [시작] Ollama({model_name})에게 {len(news_list)}건의 요약을 요청합니다.")

        summarized_results = []
        for news in news_list:
            original_text = news['content']
            # 2000자 제한
            if len(original_text) > 2000:
                original_text = original_text[:2000] + "..."

            prompt = f"""
            아래 뉴스 기사를 '3줄 요약' 형식으로 한국어로 요약해줘.
            결과는 반드시 요약된 텍스트만 출력해.

            [기사 본문]
            {original_text}
            """

            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }

            try:
                print(f"📡 [요청] 요약 진행 중: {news['title'][:15]}...")
                response = requests.post(api_url, json=payload, timeout=120)
                
                if response.status_code == 200:
                    summary = response.json().get('response', '요약 실패')
                    # 로그 깔끔하게 앞부분만 출력
                    clean_summary = summary.replace('\n', ' ')[:30]
                    print(f"✅ [성공] {clean_summary}...")
                    
                    news['summary'] = summary
                    del news['content']  # 원본 본문 제거 (DB 용량 절약)
                    summarized_results.append(news)
                else:
                    print(f"❌ [실패] 응답 코드: {response.status_code}")
                    print(f"   ㄴ 내용: {response.text}")

            except Exception as e:
                print(f"❌ [에러] Ollama 연결 실패: {e}")

        print(f"✅ [완료] 총 {len(summarized_results)}건 요약 완료")
        return summarized_results

    # ---------------------------------------------------------
    # 3. Java 백엔드로 전송
    # ---------------------------------------------------------
    @task.virtualenv(
        task_id="send_to_java_backend",
        requirements=["requests"],
        system_site_packages=False
    )
    def send_to_java(news_list: list, java_url: str):
        import requests
        import json

        print(f"📡 [시작] Java 서버({java_url})로 데이터 전송 시작")

        success_count = 0
        for news in news_list:
            try:
                payload = {
                    "title": news['title'],
                    "link": news['link'],
                    "summary": news['summary']
                }
                
                headers = {'Content-Type': 'application/json'}
                print(f"📡 [전송] {news['title'][:15]}...")
                response = requests.post(java_url, json=payload, headers=headers, timeout=10)

                if response.status_code == 200:
                    print(f"✅ [성공] 서버 저장 완료")
                    success_count += 1
                else:
                    print(f"❌ [실패] 서버 응답 코드: {response.status_code}")
            
            except Exception as e:
                print(f"❌ [에러] Java 서버 연결 실패: {e}")

        print(f"✅ [완료] 총 {success_count}/{len(news_list)} 건 전송 성공")

    # ---------------------------------------------------------
    # 4. 파이프라인 연결
    # ---------------------------------------------------------
    raw_news = scrape_news()
    summarized_news = summarize_news(raw_news, api_url=OLLAMA_API_URL, model_name=MODEL_NAME_VAR)
    send_to_java(summarized_news, java_url=JAVA_API_URL)