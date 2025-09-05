import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    YOUTH_API_KEY = os.getenv('YOUTH_API_KEY')
    JUSO_API_KEY = os.getenv('JUSO_API_KEY')
    
    VECTORSTORE_PATH = "economic_terms_faiss"
    
    YOUTH_POLICY_BASE_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
    YOUTH_RANK_BASE_URL = "https://www.youthcenter.go.kr"
    JUSO_BASE_URL = "https://www.juso.go.kr/addrlink/addrLinkApi.do"