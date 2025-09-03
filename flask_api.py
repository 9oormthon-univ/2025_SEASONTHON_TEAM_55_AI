from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)

# 전역 챗봇 변수
chatbot = None

class EconomicChatbot:
    def __init__(self, api_key, vectorstore_path="economic_terms_faiss"):
        self.api_key = api_key
        self.vectorstore_path = vectorstore_path
        
        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=self.api_key
        )
        
        # 벡터스토어 로드
        self.vectorstore = FAISS.load_local(
            self.vectorstore_path, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 검색기 설정
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # QA 체인 구성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                model="gpt-3.5-turbo", 
                temperature=0, 
                openai_api_key=self.api_key
            ),
            retriever=self.retriever,
            return_source_documents=True
        )
    
    def get_answer(self, question):
        """질문에 대한 답변 생성"""
        try:
            response = self.qa_chain.invoke({"query": question})
            
            # 관련 용어들 추출
            related_terms = []
            if response.get('source_documents'):
                for doc in response['source_documents']:
                    term = doc.metadata.get('term', '')
                    if term and term not in related_terms:
                        related_terms.append(term)
            
            return {
                "success": True,
                "answer": response['result'],
                "related_terms": related_terms[:5],
                "source_count": len(response.get('source_documents', []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "related_terms": [],
                "source_count": 0
            }
    
    def find_similar_terms(self, search_term, count=5):
        # 유사한 용어들 검색
        try:
            docs = self.vectorstore.similarity_search(search_term, k=count)
            results = []
            
            for doc in docs:
                term_name = doc.metadata.get('term', '')
                if term_name:
                    content = doc.page_content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    results.append({
                        "term": term_name,
                        "content": content
                    })
            
            return {"success": True, "terms": results}
            
        except Exception as e:
            return {"success": False, "error": str(e), "terms": []}

@app.route('/', methods=['GET'])
def health_check():
    # 서버 상태 확인
    return jsonify({
        "status": "running",
        "message": "경제용어 챗봇 API가 정상 동작중입니다",
        "endpoints": ["/ask", "/search", "/chat"]
    })

@app.route('/ask', methods=['POST'])
def ask_question():
    # 질문-답변 API
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "question 필드가 필요합니다"
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                "success": False,
                "error": "빈 질문은 처리할 수 없습니다"
            }), 400
        
        # 챗봇에게 질문
        result = chatbot.get_answer(question)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

@app.route('/search', methods=['POST'])
def search_terms():
    # 용어 검색 API
    try:
        data = request.get_json()
        
        if not data or 'term' not in data:
            return jsonify({
                "success": False,
                "error": "term 필드가 필요합니다"
            }), 400
        
        search_term = data['term'].strip()
        count = data.get('k', 5)  # 'k' 필드 지원
        
        if not search_term:
            return jsonify({
                "success": False,
                "error": "빈 검색어는 처리할 수 없습니다"
            }), 400
        
        # 유사 용어 검색
        result = chatbot.find_similar_terms(search_term, count)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    # 채팅 API
    try:
        data = request.get_json()
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                "success": False,
                "reply": "메시지를 입력해주세요"
            }), 400
        
        # 챗봇 응답 생성
        result = chatbot.get_answer(message)
        
        return jsonify({
            "success": result['success'],
            "reply": result['answer'],
            "related_terms": result['related_terms'],
            "metadata": {
                "source_count": result['source_count'],
                "user_message": message
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "reply": f"서버에 문제가 발생했습니다: {str(e)}"
        }), 500

def setup_chatbot():
    # 챗봇 초기화
    global chatbot
    
    try:
        # API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
        
        # 벡터스토어 경로 확인
        vectorstore_path = "economic_terms_faiss"
        if not os.path.exists(vectorstore_path):
            raise FileNotFoundError(f"벡터스토어 폴더를 찾을 수 없습니다: {vectorstore_path}")
        
        # 챗봇 초기화
        print("챗봇 초기화 중...")
        chatbot = EconomicChatbot(api_key, vectorstore_path)
        print("경제용어 챗봇 초기화 완료")
        
    except Exception as e:
        print(f"챗봇 초기화 실패: {e}")
        raise

if __name__ == '__main__':
    # 챗봇 설정
    setup_chatbot()
    
    # 서버 실행
    print("Flask 서버 시작...")
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )