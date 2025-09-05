import os
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from ..common.config import Config

class EconomicChatbot:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.vectorstore_path = Config.VECTORSTORE_PATH
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=self.api_key
        )
        
        self.vectorstore = FAISS.load_local(
            self.vectorstore_path, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
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
        try:
            response = self.qa_chain.invoke({"query": question})
            
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