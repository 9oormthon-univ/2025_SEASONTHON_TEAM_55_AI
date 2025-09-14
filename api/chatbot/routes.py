from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
import asyncio
from .models import EconomicChatbot

router = APIRouter()
chatbot = None

class QuestionRequest(BaseModel):
    question: str

class SearchRequest(BaseModel):
    term: str
    k: int = 5

class ChatRequest(BaseModel):
    message: str

def get_chatbot():
    global chatbot
    if chatbot is None:
        chatbot = EconomicChatbot()
    return chatbot

@router.get("/health")
def health_check():
    return {
        "status": "running",
        "message": "경제용어 챗봇 API가 정상 동작중입니다",
        "endpoints": ["/ask", "/search", "/chat"]
    }

@router.post("/ask")
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="빈 질문은 처리할 수 없습니다")
    
    try:
        bot = get_chatbot()
        result = bot.get_answer(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/search")
def search_terms(request: SearchRequest):
    if not request.term.strip():
        raise HTTPException(status_code=400, detail="빈 검색어는 처리할 수 없습니다")
    
    try:
        bot = get_chatbot()
        result = bot.find_similar_terms(request.term, request.k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요")
    
    try:
        bot = get_chatbot()
        result = bot.get_answer(request.message)
        
        return {
            "success": result['success'],
            "reply": result['answer'],
            "related_terms": result['related_terms'],
            "metadata": {
                "source_count": result['source_count'],
                "user_message": request.message
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버에 문제가 발생했습니다: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get('message', '').strip()
            if not user_message:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': '메시지를 입력해주세요'
                }))
                continue

            # 응답 시작 알림
            await websocket.send_text(json.dumps({
                'type': 'start',
                'message': '답변을 생성하고 있습니다...'
            }))

            try:
                bot = get_chatbot()
                result = bot.get_answer(user_message)

                # 답변을 스트리밍 형태로 전송
                answer = result['answer']
                chunks = [answer[i:i+50] for i in range(0, len(answer), 50)]

                for chunk in chunks:
                    await websocket.send_text(json.dumps({
                        'type': 'chunk',
                        'content': chunk
                    }))
                    await asyncio.sleep(0.1)  # 스트리밍 효과

                # 완료 메시지
                await websocket.send_text(json.dumps({
                    'type': 'complete',
                    'success': result['success'],
                    'related_terms': result['related_terms'],
                    'metadata': {
                        'source_count': result['source_count'],
                        'user_message': user_message
                    }
                }))

            except Exception as e:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': f'서버에 문제가 발생했습니다: {str(e)}'
                }))

    except WebSocketDisconnect:
        print("Client disconnected")