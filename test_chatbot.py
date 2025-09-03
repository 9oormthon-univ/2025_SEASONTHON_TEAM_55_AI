from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

# .env 파일에서 API 키 가져오기
load_dotenv()

def load_vectorstore():
    # 벡터스토어 로드하는 함수
    print("벡터스토어 로딩 중...")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OPENAI_API_KEY를 .env 파일에 설정해주세요!")
            return None, None
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        # FAISS 벡터스토어 불러오기
        if not os.path.exists("economic_terms_faiss"):
            print("economic_terms_faiss 폴더를 찾을 수 없습니다.")
            print("먼저 벡터스토어를 생성해주세요.")
            return None, None
        
        vectorstore = FAISS.load_local(
            "economic_terms_faiss", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        print(f"벡터스토어 로드 완료! 총 {vectorstore.index.ntotal}개 문서")
        
        return vectorstore, embeddings
        
    except Exception as e:
        print(f"벡터스토어 로드 실패: {e}")
        return None, None

def test_search(vectorstore):
    # 검색 기능 테스트
    print("\n검색 기능 테스트...")
    
    query = "GDP"
    try:
        results = vectorstore.similarity_search(query, k=3)
        print(f"'{query}' 검색 결과: {len(results)}개")
        
        for i, doc in enumerate(results, 1):
            term_name = doc.metadata.get('term', '제목 없음')
            preview = doc.page_content[:80] + "..." if len(doc.page_content) > 80 else doc.page_content
            print(f"{i}. {term_name}")
            print(f"   {preview}")
            
        return True
        
    except Exception as e:
        print(f"검색 실패: {e}")
        return False

def setup_qa_system(vectorstore, embeddings):
    # QA 시스템 구성
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        
        # 검색기 설정
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # QA 체인 구성
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                model="gpt-3.5-turbo", 
                temperature=0, 
                openai_api_key=api_key
            ),
            retriever=retriever,
            return_source_documents=True
        )
        
        return qa_chain
        
    except Exception as e:
        print(f"QA 시스템 구성 실패: {e}")
        return None

def run_qa_tests(qa_chain):
    # QA 시스템 테스트
    print("\nQA 시스템 테스트 중...")
    
    questions = [
        "GDP가 뭐야?",
        "인플레이션 설명해줘",
        "통화정책이란?"
    ]
    
    for question in questions:
        print(f"\n질문: {question}")
        print("-" * 30)
        
        try:
            response = qa_chain.invoke({"query": question})
            
            answer = response['result'][:150] + "..." if len(response['result']) > 150 else response['result']
            print(f"답변: {answer}")
            
            # 참고한 문서들 출력
            if response.get('source_documents'):
                related_terms = []
                for doc in response['source_documents']:
                    term = doc.metadata.get('term', '')
                    if term and term not in related_terms:
                        related_terms.append(term)
                
                if related_terms:
                    print(f"참고 용어: {', '.join(related_terms[:3])}")
                    
        except Exception as e:
            print(f"답변 생성 실패: {e}")

def chat_mode(qa_chain):
    # 채팅 모드
    print("\n=== 채팅 모드 시작 ===")
    print("('종료' 입력시 종료)")
    
    while True:
        user_question = input("\n질문: ").strip()
        
        if user_question in ['종료', 'quit', 'exit', '끝']:
            print("채팅을 종료합니다.")
            break
        
        if not user_question:
            print("질문을 입력해주세요.")
            continue
            
        try:
            response = qa_chain.invoke({"query": user_question})
            print(f"\n답변: {response['result']}")
            
            # 관련 용어 표시
            if response.get('source_documents'):
                terms = []
                for doc in response['source_documents']:
                    term = doc.metadata.get('term', '')
                    if term and term not in terms:
                        terms.append(term)
                
                if terms:
                    print(f"관련 용어: {', '.join(terms[:4])}")
                    
        except Exception as e:
            print(f"오류: {e}")

def main():
    # 메인 실행 함수
    print("=== 경제용어 챗봇 테스트 ===")
    
    # 벡터스토어 로드
    vectorstore, embeddings = load_vectorstore()
    if not vectorstore:
        print("벡터스토어 로드에 실패했습니다.")
        return
    
    # 검색 테스트
    if not test_search(vectorstore):
        print("검색 테스트 실패")
        return
    
    # QA 시스템 설정
    qa_chain = setup_qa_system(vectorstore, embeddings)
    if not qa_chain:
        print("QA 시스템 구성 실패")
        return
    
    # QA 테스트 실행
    run_qa_tests(qa_chain)
    
    # 대화형 테스트 여부 묻기
    print("\n" + "="*40)
    want_chat = input("대화형 테스트를 해보시겠습니까? (y/n): ").lower()
    if want_chat in ['y', 'yes', 'ㅇ', '네']:
        chat_mode(qa_chain)
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main()