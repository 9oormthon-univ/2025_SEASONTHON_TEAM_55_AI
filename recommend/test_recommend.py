import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001"

def test_server_health():
    # 서버 상태 확인
    try:
        url = f"{BASE_URL}/"
        res = requests.get(url, timeout=5)
        print(f"서버 상태: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"서버 메시지: {data.get('message', 'N/A')}")
            print(f"사용 가능한 엔드포인트: {data.get('endpoints', [])}")
        return res.status_code == 200
    except requests.exceptions.ConnectionError:
        print("서버에 연결할 수 없습니다. 서버가 실행중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"서버 확인 중 오류: {e}")
        return False

def test_percent():
    """포트폴리오 비율 추천 테스트"""
    print(f"\n{'='*50}")
    print("📊 /recommend/percent API 테스트")
    print('='*50)
    
    url = f"{BASE_URL}/recommend/percent"
    payload = {
        "riskLevel": "STABILITY_SEEKING",
        "targetAmount": 10000000,
        "investmentPeriod": 24
    }
    
    print(f"요청 URL: {url}")
    print(f"요청 데이터: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"\n응답 상태 코드: {res.status_code}")
        print(f"응답 헤더: Content-Type = {res.headers.get('content-type', 'N/A')}")
        
        if res.status_code == 200:
            try:
                json_data = res.json()
                print(f"\nJSON 파싱 성공!")
                print(f"응답 데이터:")
                print(json.dumps(json_data, ensure_ascii=False, indent=2))
                
                # 응답 데이터 검증
                if json_data.get('success'):
                    data = json_data.get('data', {})
                    print(f"\n추천 결과 요약:")
                    print(f"  - 위험수준: {data.get('riskLevel')}")
                    print(f"  - 목표금액: {data.get('targetAmount'):,}원")
                    print(f"  - 투자기간: {data.get('investmentPeriod')}개월")
                    print(f"  - 예상수익: {data.get('expectedTotal'):,}원")
                    print(f"  - 자산배분:")
                    for asset, percent in data.get('allocation', {}).items():
                        print(f"    * {asset}: {percent}%")
                else:
                    print(f"API 에러: {json_data.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")
                print(f"원본 응답 텍스트: {res.text}")
        else:
            print(f"HTTP 오류: {res.status_code}")
            print(f"응답 내용: {res.text}")
            
    except requests.exceptions.ConnectionError:
        print("서버 연결 실패")
    except requests.exceptions.Timeout:
        print("요청 시간 초과")
    except Exception as e:
        print(f"요청 중 오류: {e}")

def test_products():
    """상품 추천 테스트"""
    print(f"\n{'='*50}")
    print("/recommend/products API 테스트")
    print('='*50)
    
    url = f"{BASE_URL}/recommend/products"
    payload = {
        "riskLevel": "RISK_NEUTRAL",
        "targetAmount": 5000000,
        "investmentPeriod": 12
    }
    
    print(f"요청 URL: {url}")
    print(f"요청 데이터: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"\n응답 상태 코드: {res.status_code}")
        
        if res.status_code == 200:
            try:
                json_data = res.json()
                print(f"\nJSON 파싱 성공!")
                
                if json_data.get('success'):
                    data = json_data.get('data', {})
                    print(f"\n추천 상품 결과:")
                    print(f"  - 위험수준: {data.get('riskLevel')}")
                    print(f"  - 목표금액: {data.get('targetAmount'):,}원")
                    print(f"  - 투자기간: {data.get('investmentPeriod')}개월")
                    print(f"  - 예상수익: {data.get('expectedTotal'):,}원")
                    
                    products = data.get('recommendedProducts', {})
                    for product_type, product_list in products.items():
                        if product_list:
                            print(f"\n  📋 {product_type.upper()} 상품:")
                            for i, product in enumerate(product_list, 1):
                                print(f"    {i}. {product.get('name', 'N/A')}")
                                print(f"       발행사: {product.get('bank', 'N/A')}")
                                print(f"       수익률: {product.get('rate', 0)}%")
                                print(f"       투자금액: {product.get('investAmount', 0):,}원")
                                print(f"       예상수익: {product.get('expectedValue', 0):,}원")
                else:
                    print(f"API 에러: {json_data.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")
                print(f"원본 응답 텍스트: {res.text}")
        else:
            print(f"HTTP 오류: {res.status_code}")
            print(f"응답 내용: {res.text}")
            
    except requests.exceptions.ConnectionError:
        print("서버 연결 실패")
    except requests.exceptions.Timeout:
        print("요청 시간 초과")
    except Exception as e:
        print(f"요청 중 오류: {e}")

def test_invalid_requests():
    """잘못된 요청 테스트"""
    print(f"\n{'='*50}")
    print("잘못된 요청 처리 테스트")
    print('='*50)
    
    # 1. 빈 데이터 테스트
    print("\n 1. 빈 데이터 테스트")
    url = f"{BASE_URL}/recommend/percent"
    try:
        res = requests.post(url, json={}, timeout=30)
        print(f"상태 코드: {res.status_code}")
        if res.status_code != 200:
            print(f"응답: {res.text}")
        else:
            print("예상치 못한 성공")
    except Exception as e:
        print(f"오류: {e}")
    
    # 2. 잘못된 riskLevel 테스트
    print("\n 2. 잘못된 riskLevel 테스트")
    try:
        res = requests.post(url, json={
            "riskLevel": "INVALID_LEVEL",
            "targetAmount": 1000000,
            "investmentPeriod": 12
        }, timeout=5)
        print(f"상태 코드: {res.status_code}")
        if res.status_code != 200:
            print(f"응답: {res.text}")
        else:
            print("예상치 못한 성공")
    except Exception as e:
        print(f"오류: {e}")
    
    # 3. 음수 금액 테스트
    print("\n 3. 음수 금액 테스트")
    try:
        res = requests.post(url, json={
            "riskLevel": "STABLE",
            "targetAmount": -1000000,
            "investmentPeriod": 12
        }, timeout=5)
        print(f"상태 코드: {res.status_code}")
        if res.status_code != 200:
            print(f"응답: {res.text}")
        else:
            print("예상치 못한 성공")
    except Exception as e:
        print(f"오류: {e}")
    
    # 4. 0 금액 테스트
    print("\n 4. 0 금액 테스트")
    try:
        res = requests.post(url, json={
            "riskLevel": "STABLE",
            "targetAmount": 0,
            "investmentPeriod": 12
        }, timeout=5)
        print(f"상태 코드: {res.status_code}")
        if res.status_code != 200:
            print(f"응답: {res.text}")
        else:
            print("예상치 못한 성공")
    except Exception as e:
        print(f"오류: {e}")

def test_all_risk_levels():
    """모든 위험수준 테스트"""
    print(f"\n{'='*50}")
    print("모든 위험수준 테스트")
    print('='*50)
    
    risk_levels = ["STABLE", "STABILITY_SEEKING", "RISK_NEUTRAL", "ACTIVE_INVESTMENT", "AGGRESSIVE_INVESTMENT"]
    url = f"{BASE_URL}/recommend/percent"
    
    for risk_level in risk_levels:
        print(f"\n {risk_level} 테스트")
        try:
            res = requests.post(url, json={
                "riskLevel": risk_level,
                "targetAmount": 1000000,
                "investmentPeriod": 12
            }, timeout=5)
            
            if res.status_code == 200:
                data = res.json()
                if data.get('success'):
                    allocation = data.get('data', {}).get('allocation', {})
                    expected_total = data.get('data', {}).get('expectedTotal', 0)
                    print(f"    성공")
                    print(f"     자산배분: {allocation}")
                    print(f"     예상수익: {expected_total:,}원")
                else:
                    print(f"  실패 - {data.get('error')}")
            else:
                print(f"  HTTP 오류: {res.status_code}")
                
        except Exception as e:
            print(f"  요청 오류: {e}")

def test_edge_cases():
    """극단적인 케이스 테스트"""
    print(f"\n{'='*50}")
    print("극단적인 케이스 테스트")
    print('='*50)
    
    test_cases = [
        {
            "name": "매우 큰 금액 (100억원)",
            "data": {"riskLevel": "STABLE", "targetAmount": 10000000000, "investmentPeriod": 12}
        },
        {
            "name": "매우 작은 금액 (1만원)",
            "data": {"riskLevel": "STABLE", "targetAmount": 10000, "investmentPeriod": 12}
        },
        {
            "name": "매우 긴 투자기간 (10년)",
            "data": {"riskLevel": "RISK_NEUTRAL", "targetAmount": 5000000, "investmentPeriod": 120}
        },
        {
            "name": "매우 짧은 투자기간 (1개월)",
            "data": {"riskLevel": "RISK_NEUTRAL", "targetAmount": 5000000, "investmentPeriod": 1}
        }
    ]
    
    url = f"{BASE_URL}/recommend/percent"
    
    for case in test_cases:
        print(f"\n🧪 {case['name']}")
        try:
            res = requests.post(url, json=case['data'], timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data.get('success'):
                    result = data.get('data', {})
                    print(f" 성공 - 예상수익: {result.get('expectedTotal', 0):,}원")
                else:
                    print(f" 실패 - {data.get('error')}")
            else:
                print(f" HTTP 오류: {res.status_code}")
                
        except Exception as e:
            print(f" 요청 오류: {e}")

def test_performance():
    """성능 테스트"""
    print(f"\n{'='*50}")
    print("성능 테스트 (10회 요청)")
    print('='*50)
    
    url = f"{BASE_URL}/recommend/percent"
    payload = {
        "riskLevel": "RISK_NEUTRAL",
        "targetAmount": 1000000,
        "investmentPeriod": 12
    }
    
    times = []
    success_count = 0
    
    for i in range(10):
        try:
            start_time = time.time()
            res = requests.post(url, json=payload, timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            if res.status_code == 200:
                success_count += 1
                print(f"  요청 {i+1}: {response_time:.3f}초")
            else:
                print(f"  요청 {i+1}: HTTP {res.status_code}")
                
        except Exception as e:
            print(f"  요청 {i+1}: 오류 - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n 성능 결과:")
        print(f"  - 성공률: {success_count}/10 ({success_count*10}%)")
        print(f"  - 평균 응답시간: {avg_time:.3f}초")
        print(f"  - 최소 응답시간: {min_time:.3f}초")
        print(f"  - 최대 응답시간: {max_time:.3f}초")

def run_comprehensive_tests():
    """전체 테스트 실행"""
    print("포트폴리오 추천 API 종합 테스트 시작")
    print("="*60)
    
    # 1. 서버 상태 확인
    if not test_server_health():
        print("\n 서버가 실행되지 않았습니다.")
        print("해결 방법:")
        print("1. Flask 서버가 실행중인지 확인")
        print("2. 포트 5001이 사용 가능한지 확인")
        print("3. 필요한 의존성이 설치되어 있는지 확인")
        return
    
    # 2. 기본 기능 테스트
    test_percent()
    test_products()
    
    # 3. 에러 처리 테스트
    test_invalid_requests()
    
    # 4. 모든 위험수준 테스트
    test_all_risk_levels()
    
    # 5. 극단적인 케이스 테스트
    test_edge_cases()
    
    # 6. 성능 테스트
    test_performance()
    
    print(f"\n{'='*60}")
    print(" 모든 테스트 완료!")
    print("="*60)
    print("\n 추가 확인사항:")
    print("- Spring BE와의 연동 테스트")
    print("- 실제 금융 데이터셋 적용")
    print("- 프론트엔드와의 API 연동")

if __name__ == "__main__":
    run_comprehensive_tests()