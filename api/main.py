from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .youth_policy.routes import router as youth_policy_router
from .chatbot.routes import router as chatbot_router

app = FastAPI(
    title="통합 API 서버",
    description="경제용어 챗봇 + 청년정책 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발서버
        "http://localhost:8080",  # Vue/일반 웹서버
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        "file://",  # Flutter 앱
        "http://10.0.2.2:8000",  # Android 에뮬레이터
        "http://localhost",  # 로컬 개발
        "*"  # 모든 도메인 허용 (개발용)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept", 
        "Accept-Language",
        "Content-Language",
        "X-Requested-With",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
        "User-Agent"
    ],
)

app.include_router(youth_policy_router, prefix="/youth-policy", tags=["청년정책"])
app.include_router(chatbot_router, prefix="/chatbot", tags=["경제용어 챗봇"])

@app.get("/")
def root():
    return {
        "message": "통합 API 서버",
        "services": {
            "청년정책": "/youth-policy",
            "경제용어챗봇": "/chatbot"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)