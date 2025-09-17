from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain_core.documents import Document
from tqdm import tqdm
import os
import re

def load_pdf_pages():
    #PDF 파일에서 필요한 페이지들 가져오기
    print("PDF 파일 로드 중...")

    # 금융 용어 PDF 로드
    print("금융 용어 PDF 로드 중...")
    word_loader = PyPDFLoader("word.pdf")
    word_pages = word_loader.load()

    # 18~369 페이지 추출 (인덱스 17~368)
    selected_word_pages = word_pages[17:369]
    print(f"금융 용어 PDF: {len(selected_word_pages)}개 페이지 추출 완료")

    # IPO PDF 로드
    print("IPO PDF 로드 중...")
    ipo_loader = PyPDFLoader("ipo.pdf")
    ipo_pages = ipo_loader.load()
    print(f"IPO PDF: {len(ipo_pages)}개 페이지 추출 완료")

    # 두 PDF의 텍스트 합치기
    word_text = "\n".join([page.page_content for page in selected_word_pages])
    ipo_text = "\n".join([page.page_content for page in ipo_pages])

    # 구분자를 추가하여 두 텍스트 결합
    return word_text + "\n\n===IPO_CONTENT_START===\n\n" + ipo_text

def clean_pdf_text(text):
    """PDF 텍스트 전처리"""
    # 페이지 번호 제거
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    
    # 연속된 줄바꿈 정리
    text = re.sub(r"\n{2,}", "\n", text)
    
    # 문서 제목 반복 제거
    text = re.sub(r"경제금융용어\s*700선", "", text)
    
    # 한글 자모 구분자 제거
    text = re.sub(r"^\s*[ㄱ-ㅎ]\s*$", "", text, flags=re.MULTILINE)
    
    # 불필요한 문자 제거
    text = re.sub(r"ABC", "", text, flags=re.MULTILINE)
    text = re.sub(r"\b\w+\s*[∙•·ㆍ]\s*", "", text)
    
    # 빈 줄 정리
    text = re.sub(r"\n{2,}", "\n", text)
    
    return text

def fix_broken_characters(text):
    # 깨진 특수문자들 복원
    char_map = {
        "\ue06d총산출량": "노동비용/총산출량 = 시간당 노동비용*총노동시간/총산출량 = 시간당 노동비용/총산출량/총노동시간 = 시간당 노동비용/노동생산성",
        "\ue06d매출액 영업손익 ×": "영업손익/매출액*",
        "\ue06d매출액 매출총손익": "매출총손익/매출액",
        "\ue043 × ": "",
        "\ue044": "(",
        "\ue042": "%",
        "\ue045": ")",
        "\ue047": "=",
        "\ue04b": "{",
        "\ue054": "/",
        "\ue048": "+",
        "\ue04c×": "}*",
        "\ue04c": "}",
        "\ue034": "1",
        "\ue03d": "0",
        "\ue046": "-",
        "\ue049": "[",
        "\ue04a×": "]*",
        "×\ue034": "*1",
        "\ue038": "5"
    }
    
    for broken, fixed in char_map.items():
        text = text.replace(broken, fixed)
    
    return text.strip()

def process_line_breaks(text):
    #줄바꿈 처리하여 자연스러운 텍스트로 변환
    # 단어 중간에 끊어진 부분 연결
    text = re.sub(r"(?<=\w)-?\n(?=\w)", "", text)
    # 문장 끝 줄바꿈 처리
    text = re.sub(r"([.!?])\n", r"\1 ", text)
    # 나머지 줄바꿈을 공백으로
    text = text.replace("\n", " ")
    # 여러 공백을 하나로
    return re.sub(r"\s{2,}", " ", text).strip()

def parse_economic_terms(text):
    #경제용어들을 파싱하여 구조화된 문서로 변환
    print("용어 파싱 중...")

    documents = []

    # IPO 컨텐츠와 일반 금융 용어 분리
    if "===IPO_CONTENT_START===" in text:
        word_text, ipo_text = text.split("===IPO_CONTENT_START===", 1)

        # 일반 금융 용어 파싱
        print("일반 금융 용어 파싱 중...")
        word_documents = parse_word_terms(word_text)
        documents.extend(word_documents)

        # IPO 컨텐츠 파싱
        print("IPO 컨텐츠 파싱 중...")
        ipo_documents = parse_ipo_content(ipo_text)
        documents.extend(ipo_documents)
    else:
        # IPO 구분자가 없는 경우 기존 방식으로 파싱
        documents = parse_word_terms(text)

    return documents

def parse_word_terms(text):
    #기존 금융 용어 파싱 로직
    lines = text.strip().split("\n")
    documents = []

    i = 0
    while i < len(lines):
        # 용어명 추출
        term = lines[i].strip()
        i += 1

        explanation_parts = []
        related_terms = ""

        # 용어 설명 수집
        while i < len(lines):
            line = lines[i].strip()

            # 다음 용어인지 확인
            if re.match(r"^[\w/]{1,50}(\s*\([A-Z]+\))?$", line):
                break

            # 연관검색어 처리
            if line.startswith("연관검색어"):
                match = re.match(r"연관검색어\s*:\s*(.*)", line)
                if match:
                    related_terms = match.group(1).strip()

                # 다음 줄 확인
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r"^[\w/]{1,50}(\s*\([A-Z]+\))?$", next_line):
                        i += 1
                        break
            else:
                explanation_parts.append(line)

            i += 1

        # 텍스트 정리
        term = process_line_breaks(term)
        explanation = process_line_breaks(" ".join(explanation_parts))
        related_terms = process_line_breaks(related_terms)

        # 특수문자 복원
        term = fix_broken_characters(term)
        explanation = fix_broken_characters(explanation)
        related_terms = fix_broken_characters(related_terms)

        # 문서 생성
        if term.strip():  # 빈 용어 제외
            content = f"용어: {term}\n설명: {explanation}\n관련용어: {related_terms}"
            documents.append(Document(page_content=content, metadata={"term": term, "source": "financial_terms"}))

    return documents

def parse_ipo_content(text):
    #IPO 컨텐츠를 청크 단위로 파싱
    documents = []

    # IPO 텍스트를 문단 단위로 분할
    paragraphs = text.split('\n\n')

    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if len(paragraph) > 100:  # 너무 짧은 문단은 제외
            # IPO 관련 키워드로 제목 추출 시도
            lines = paragraph.split('\n')
            title = lines[0] if lines else f"IPO 섹션 {i+1}"

            # IPO 키워드 포함 확인
            ipo_keywords = ['IPO', 'ipo', '공개', '상장', '공모', '주식', '투자', '기업공개']
            has_ipo_keyword = any(keyword in paragraph for keyword in ipo_keywords)

            if has_ipo_keyword or len(paragraph) > 200:
                content = f"주제: {title}\n내용: {paragraph}\n분야: IPO"
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "term": title,
                        "source": "ipo_guide",
                        "type": "ipo_content"
                    }
                ))

    return documents

def create_vectorstore(documents, api_key):
    #벡터스토어 생성
    print(f"{len(documents)}개 문서로 벡터스토어 생성 중...")
    
    # 임베딩 모델 설정
    embedding = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=api_key
    )
    
    # 배치 처리로 벡터스토어 생성
    batch_size = 50
    vectorstore = None
    
    for i in tqdm(range(0, len(documents), batch_size), desc="벡터 생성"):
        batch = documents[i:i+batch_size]
        
        try:
            if vectorstore is None:
                vectorstore = FAISS.from_documents(batch, embedding)
            else:
                batch_store = FAISS.from_documents(batch, embedding)
                vectorstore.merge_from(batch_store)
                
        except Exception as e:
            print(f"배치 {i//batch_size + 1} 처리 실패: {e}")
            # 작은 단위로 재시도
            for j in range(0, len(batch), 10):
                mini_batch = batch[j:j+10]
                try:
                    if vectorstore is None:
                        vectorstore = FAISS.from_documents(mini_batch, embedding)
                    else:
                        mini_store = FAISS.from_documents(mini_batch, embedding)
                        vectorstore.merge_from(mini_store)
                except Exception:
                    continue
    
    return vectorstore

def main():
    print("경제용어 벡터스토어 생성 시작")
    
    # 환경변수 로드
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY를 .env 파일에 설정해주세요")
    
    # 1. PDF 로드
    full_text = load_pdf_pages()
    
    # 2. 텍스트 전처리
    clean_text = clean_pdf_text(full_text)
    
    # 3. 용어 파싱
    documents = parse_economic_terms(clean_text)
    
    # 4. 불량 데이터 필터링
    filtered_docs = [doc for doc in documents if doc.metadata.get("term", "").strip() != "총산출량"]
    
    print(f"최종 {len(filtered_docs)}개 용어 처리")
    
    # 5. 벡터스토어 생성
    vectorstore = create_vectorstore(filtered_docs, api_key)
    
    if vectorstore is None:
        raise ValueError("벡터스토어 생성 실패")
    
    print(f"총 {vectorstore.index.ntotal}개 벡터 생성 완료")
    
    # 6. 로컬 저장
    save_path = "economic_terms_faiss"
    vectorstore.save_local(save_path)
    print(f"벡터스토어가 '{save_path}' 폴더에 저장됨")
    
    # 저장 확인
    files = os.listdir(save_path)
    print(f"저장된 파일: {files}")

if __name__ == "__main__":
    main()