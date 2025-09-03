# 📊 경제용어 챗봇

경제금융용어 700선을 기반으로 한 AI 챗봇 서비스입니다. 경제 용어에 대한 정확한 답변과 관련 용어 추천을 제공합니다.

## 🚀 프로젝트 실행 방법

### **Docker로 한 번에 실행 (권장)**

```bash
# 1. 저장소 클론
git clone <your-repo-url>
cd <repo-name>

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY를 설정하세요

# 3. Docker 이미지 빌드
docker build -t economic-chatbot .

# 4. 컨테이너 실행
docker run -d \
  --name chatbot-container \
  -p 5001:5001 \
  --env-file .env \
  economic-chatbot

# 5. 실행 상태 확인
docker ps

# 6. 로그 확인
docker logs chatbot-container
```

### **🔧 로컬 개발 모드 실행**

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 설정

# 4. 벡터스토어 생성 (최초 1회만)
python create_vectorstore.py

# 5. 서버 실행
python flask_api.py
```

## 📡 API 엔드포인트

### **서버 상태 확인**

- **GET** `/` - 서버 상태 및 사용 가능한 엔드포인트 확인

### **질의응답 API**

- **POST** `/ask` - 경제 용어에 대한 질문 답변

```javascript
// 요청 예시
const response = await fetch("http://localhost:5001/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "GDP가 무엇인가요?" }),
});

const result = await response.json();
// {
//   "success": true,
//   "answer": "국내총생산(GDP)은...",
//   "related_terms": ["명목GDP", "실질GDP", ...],
//   "source_count": 5
// }
```

### **용어 검색 API**

- **POST** `/search` - 유사한 경제 용어 검색

```javascript
// 요청 예시
const response = await fetch("http://localhost:5001/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ term: "인플레이션", k: 3 }),
});
```

### **채팅 API**

- **POST** `/chat` - 채팅 형태의 질의응답

```javascript
// 요청 예시
const response = await fetch("http://localhost:5001/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "통화정책에 대해 설명해주세요" }),
});
```

## ⚙️ 환경 설정

### **필수 환경변수**

`.env` 파일에 다음 항목을 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### **OpenAI API 키 발급**

1. [OpenAI 플랫폼](https://platform.openai.com/)에 가입
2. API Keys 섹션에서 새 키 생성
3. `.env` 파일에 키 입력

### **API 테스트**

```bash
# 서버 상태 확인
curl http://localhost:5001/

# 질문 테스트
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "경상수지란 무엇인가요?"}'

# 용어 검색 테스트
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{"term": "환율", "k": 5}'
```

## 📋 개발 환경 요구사항

### **Docker 사용 시**

- Docker (20.0 이상)
- Docker Compose (선택사항)

### **로컬 개발 시**

- Python 3.9 이상
- OpenAI API 키
- 최소 4GB RAM (벡터스토어 로딩용)

## 🏗️ 프로젝트 구조

```
economic-chatbot/
├── flask_api.py              # Flask API 서버
├── create_vectorstore.py     # 벡터스토어 생성 스크립트
├── requirements.txt          # Python 패키지 목록
├── Dockerfile               # Docker 이미지 빌드 파일
├── .env.example            # 환경변수 템플릿
├── .gitignore              # Git 제외 파일 목록
├── README.md               # 프로젝트 문서
├── word.pdf                # 경제금융용어 700선 (원본)
└── economic_terms_faiss/   # 생성된 벡터 데이터베이스
    ├── index.faiss
    └── index.pkl
```
