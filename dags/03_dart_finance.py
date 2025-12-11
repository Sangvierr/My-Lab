from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from datetime import datetime

# 1. Airflow 변수 가져오기
MAC_IP = Variable.get("MAC_SERVER_IP")
WIN_IP = Variable.get("WIN_SERVER_IP")
DART_KEY = Variable.get("DART_API_KEY")
MODEL_NAME_VAR = Variable.get("OLLAMA_MODEL")

# 2. API 주소 조합
JAVA_API_URL = f"http://{MAC_IP}:8090/api/finance/bulk"
OLLAMA_API_URL = f"http://{WIN_IP}:11434/api/generate"

with DAG(
    dag_id="03_dart_finance_etl",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mylab", "finance"],
) as dag:

    # ----------------------------------------------------------------
    # 1. OpenDartReader를 활용한 통합 수집 및 분석 (참고: https://github.com/FinanceData/OpenDartReader)
    # ----------------------------------------------------------------
    @task.virtualenv(
        task_id="analyze_dart_reports",
        requirements=["requests", "opendartreader", "pandas", "beautifulsoup4", "lxml"],
        system_site_packages=False
    )
    def analyze_dart(api_key, ollama_url, model_name):
        import OpenDartReader
        import requests
        import pandas as pd
        from bs4 import BeautifulSoup
        import time

        # 1. 객체 생성 (API KEY)
        dart = OpenDartReader(api_key)
        
        # 2. 분석 대상 기업
        target_corps = ["삼성전자", "SK하이닉스", "현대자동차", "한화에어로스페이스", "레인보우로보틱스"]
        target_year = 2023
        
        result_list = []
        
        print(f"📡 [시작] DART 데이터 수집 및 분석 (OpenDartReader 활용)")

        # -------------------------------------------------------
        # 도우미 함수: 금액 정제 (괄호 -> 음수, 콤마 제거)
        # -------------------------------------------------------
        def clean_money(value):
            if pd.isna(value) or value == '': return 0
            str_val = str(value).replace(',', '').strip()
            # (1,000) 형태 처리 -> -1000
            if str_val.startswith('(') and str_val.endswith(')'):
                return -int(str_val[1:-1])
            return int(str_val)

        for name in target_corps:
            print(f"\n🏢 [처리 중] {name}...")
            
            # 초기 데이터 구조
            finance_data = {
                "corpName": name,
                "year": str(target_year),
                "quarter": "4Q", # 사업보고서 기준
                "corpCode": "",  # 아래에서 찾아서 넣음
                "revenue": 0,
                "operatingProfit": 0,
                "netIncome": 0,
                "aiSummary": "분석 대기",
                "aiRisk": "데이터 없음"
            }

            try:
                # --- [A] 정형 데이터: 재무제표 ---
                # finstate(기업명, 연도, 보고서코드=11011(사업보고서))
                print(f"   📡 [요청] 재무제표 조회")
                fs = dart.finstate(name, target_year, reprt_code='11011')
                
                if fs is not None and not fs.empty:
                    # 1. 기업 고유코드 확보 (첫 행에서 가져옴)
                    finance_data['corpCode'] = fs.iloc[0]['corp_code']
                    
                    # 2. 연결재무제표(CFS) 필터링
                    fs = fs[fs['fs_div'] == 'CFS']
                    
                    # 3. 데이터 추출
                    for _, row in fs.iterrows():
                        acct_nm = row['account_nm']
                        amt = clean_money(row['thstrm_amount']) # 정제 함수 사용
                        
                        if acct_nm in ['매출액', '수익(매출액)']:
                            finance_data['revenue'] = amt
                        elif acct_nm in ['영업이익', '영업이익(손실)']:
                            finance_data['operatingProfit'] = amt
                        elif acct_nm in ['당기순이익', '당기순이익(손실)']:
                            finance_data['netIncome'] = amt
                    print(f"   ✅ [완료] 재무제표 확보 (매출: {finance_data['revenue']:,}원)")
                else:
                    print(f"   ❌ [실패] 재무제표 데이터 없음")
                    continue # 재무제표 없으면 다음 기업으로

                # --- [B] 비정형 데이터: 사업보고서 원문 ---
                print(f"   📡 [요청] 사업보고서 원문 검색")
                # list(기업명, 시작일, 종류=A(정기공시))
                reports = dart.list(name, start=f'{target_year}0101', kind='A', final=True)
                
                report_text = ""
                if not reports.empty:
                    # 가장 상단(최신)의 접수번호 가져오기
                    target_report = reports[reports['report_nm'].str.contains('사업보고서')].iloc[0]
                    rcept_no = target_report['rcept_no']
                    print(f"   ✅ [발견] 보고서 접수번호: {rcept_no}")

                    # document(접수번호) -> XML 원문 전체 반환
                    xml_text = dart.document(rcept_no)
                    
                    # 'II. 사업의 내용' 또는 '사업의 내용' 섹션 찾기 (정규식 활용)
                    # XML 태그 제거 후 텍스트만 추출
                    soup = BeautifulSoup(xml_text, 'lxml')
                    full_text = soup.get_text()
                    
                    # 텍스트에서 '사업의 내용' 이후 부분만 잘라내기 (단순화)
                    start_idx = full_text.find('사업의 내용')
                    if start_idx != -1:
                        # 찾은 위치부터 2000자만 추출
                        report_text = full_text[start_idx : start_idx + 2000]
                        print(f"   ✅ [추출] 사업 내용 텍스트 확보 ({len(report_text)}자)")
                    else:
                        print(f"   ⚠️ [경고] '사업의 내용' 키워드 못 찾음 (전체 텍스트 앞부분 사용)")
                        report_text = full_text[:2000]
                else:
                    print(f"   ❌ [실패] 사업보고서 공시 목록 없음")

                # --- [C] AI 분석 (Ollama) ---
                if report_text:
                    print(f"   📡 [요청] AI 분석 시작 (Model: {model_name})...")
                    prompt = f"""
                    [역할] 너는 주식 투자 전문가야.
                    [지시] 아래 기업의 사업 내용을 읽고 JSON 포맷으로 분석해줘.
                    1. summary: 회사가 영위하는 주요 사업을 1문장으로 요약.
                    2. risk: 현재 겪을 수 있는 가장 큰 리스크 1가지.

                    [사업 내용]
                    {report_text}
                    
                    [출력 형식]
                    {{ "summary": "...", "risk": "..." }}
                    """
                    
                    payload = {
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                    
                    try:
                        res = requests.post(ollama_url, json=payload, timeout=120)
                        if res.status_code == 200:
                            import json
                            ai_res = res.json().get('response', '{}')
                            try:
                                parsed = json.loads(ai_res)
                                finance_data['aiSummary'] = parsed.get('summary', '분석 실패')
                                finance_data['aiRisk'] = parsed.get('risk', '분석 실패')
                                print(f"   ✅ [성공] AI 분석 완료")
                            except:
                                finance_data['aiSummary'] = ai_res[:500]
                                finance_data['aiRisk'] = "JSON 파싱 실패"
                        else:
                            print(f"   ❌ [실패] AI 응답 코드: {res.status_code}")
                    except Exception as e:
                        print(f"   ❌ [에러] AI 연결 실패: {e}")

                result_list.append(finance_data)
                time.sleep(1) # API 호출 제한 방지

            except Exception as e:
                print(f"   ❌ [에러] 처리 중 중단: {e}")

        return result_list

    # 2. Java로 전송 (Load)
    @task.virtualenv(
        task_id="send_to_java_bulk",
        requirements=["requests"],
        system_site_packages=False
    )
    def send_to_java(data_list, java_url):
        import requests
        import json

        if not data_list:
            print("⚠️ [경고] 전송할 데이터가 없습니다.")
            return

        print(f"📡 [시작] Java 서버({java_url})로 {len(data_list)}건 전송")
        
        try:
            headers = {'Content-Type': 'application/json'}
            res = requests.post(java_url, json=data_list, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"✅ [성공] 서버 저장 완료: {res.text}")
            else:
                print(f"❌ [실패] 전송 실패 (Code: {res.status_code})")
        except Exception as e:
            print(f"❌ [에러] 연결 실패: {e}")

    # 파이프라인 연결 (수정된 변수명 적용)
    analyzed_data = analyze_dart(DART_KEY, OLLAMA_API_URL, MODEL_NAME_VAR)
    send_to_java(analyzed_data, JAVA_API_URL)