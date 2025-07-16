from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from rag_indexer_class import IndexConfig, RAGIndexer
from utils.index import image_to_base64


import os
from dotenv import load_dotenv

load_dotenv() # load all the environment variable.

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
# MODEL_NAME=os.getenv("MODEL_NAME")


def analyze_query_and_retrieve(query: str, retriever, llm) -> str:
    """쿼리를 분석하고 관련 정보를 검색하는 함수"""
    
    # 1. 쿼리 분석 프롬프트
    query_analysis_prompt = ChatPromptTemplate.from_messages([
        ('system', """당신은 사용자의 질문을 분석하는 전문가입니다. 
        주어진 질문에서 다음을 추출하세요:
        
        1. 주요 키워드 (3-5개)
        2. 질문의 핵심 주제
        3. 구체적인 조건이나 요구사항
        4. 답변에서 다뤄야 할 세부 사항들
        
        JSON 형식으로 출력하세요:
        {{
            "keywords": ["키워드1", "키워드2", "키워드3"],
            "main_topic": "주제",
            "conditions": ["조건1", "조건2"],
            "details": ["세부사항1", "세부사항2"]
        }}"""),
        ('human', "질문: {query}")
    ])
    
    # 2. 쿼리 분석 실행
    query_analysis = query_analysis_prompt | llm | StrOutputParser()
    analysis_result = query_analysis.invoke({"query": query})
    
    # 3. 분석된 키워드들을 사용하여 검색
    keywords = []
    try:
        import json
        analysis_dict = json.loads(analysis_result)
        keywords = analysis_dict.get("keywords", [])
    except:
        # JSON 파싱 실패시 원본 쿼리 사용
        keywords = [query]
    
    # 4. 각 키워드별로 검색 수행
    all_contexts = []
    for keyword in keywords:
        try:
            contexts = retriever.get_relevant_documents(keyword)
            all_contexts.extend(contexts)
        except:
            continue
    
    # 5. 중복 제거 및 정렬
    unique_contexts = []
    seen_content = set()
    for doc in all_contexts:
        if doc.page_content not in seen_content:
            unique_contexts.append(doc)
            seen_content.add(doc.page_content)
    
    # 6. 컨텍스트 결합
    combined_context = "\n\n".join([doc.page_content for doc in unique_contexts[:10]])
    
    return combined_context, analysis_result


def main_image():
    """메인 실행 함수"""

    # 설정 생성
    config = IndexConfig(
        persistent_directory="./chroma",
        collection_name="samsung_imgs",
        embedding_model="text-embedding-3-small",
    )

    # 인덱서 생성 및 실행
    indexer = RAGIndexer(config)

    # 이미지 로드해서 모델명 검색
    img = "./data/samsung_imgs/아가사랑_3kg_WA30DG2120EE.png"
    img_base64 = image_to_base64(img)

    # 유사도 검색
    model_nm = indexer.search_and_show(img_base64)
    return model_nm


def search_manuals(query: str, model_nm: str, k: int = 5):
    query = model_nm + query # model nm 자체를 프롬프트로 넘겨서 저장해놓기
    print("최종 프롬프트 :", query)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectordb = Chroma(
        collection_name="samsung_manuals",
        embedding_function=embeddings,
        persist_directory="./chroma",
    )

    """매뉴얼 검색"""
    docs = vectordb.similarity_search(query, k=k)

    return docs

    # for i, doc in enumerate(docs):
    #     print(f"\n[TOP-{i + 1}]")
    #     print(f'모델명: {doc.metadata.get("model_name", "Unknown")}')
    #     print(f'청크 ID: {doc.metadata.get("chunk_id", "Unknown")}')
    #     print(f'청크 (total): {doc.metadata.get("total_chunks", "Unknown")}')
    #     print(f"내용: {doc.page_content[:200]}...")
    #     print("-" * 50)


# Chain-of-Thought 프롬프트 개선
cot_prompt = ChatPromptTemplate.from_messages([
    ('system', """당신은 스마트한 가전 제품 도우미입니다. 
    사용자의 질문에 대해 생각의 나무를 사용하여 주제를 자세히 설명하고 필요할 때는 뒤로 물러나 명확하고 일관된 사고 사슬을 구성하세요.
    
    다음 단계를 따라 답변하세요:
    
    **1단계: 질문 분석**
    - 사용자가 무엇을 묻고 있는지 파악
    - 관련된 제품, 기능, 문제점 식별
    - 구체적인 조건이나 상황 파악
    
    **2단계: 정보 수집**
    - 제공된 컨텍스트에서 관련 정보 찾기
    - 각 키워드별로 관련 내용 검색
    - 정보의 신뢰성과 관련성 평가
    
    **3단계: 정보 구조화**
    - 찾은 정보를 논리적으로 분류
    - 우선순위에 따라 정렬
    - 조건별로 구분하여 정리
    
    **4단계: 답변 구성**
    - 명확하고 구조화된 답변 작성
    - 단계별 혹은 종류별 설명 제공
    - 구체적인 예시나 방법 제시
    - 정보가 부족한 경우 안내
    
    답변 형식:
    ## 질문 분석
    [사용자의 질문을 분석한 내용]
    
    ## 관련 정보
    [찾은 주요 정보들]
    
    ## 답변
    [구조화된 답변]
    
    ### 1. [주제/조건 A]
    [상세 설명]
    
    ### 2. [주제/조건 B] 
    [상세 설명]
    
    ### 3. [주제/조건 C]
    [상세 설명]
    
    ## 추가 안내
    [필요한 경우 추가 정보나 주의사항]"""),
    
    ('human', """
    사용자 질문: {query}
    
    질문 분석 결과: {analysis}
    
    관련 컨텍스트:
    {context}
    
    위의 단계를 따라 체계적으로 답변하세요.
    """)
])

llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.3)

# 개선된 체인 구성
def enhanced_chain(query: str):
    # 1. 쿼리 분석 및 컨텍스트 검색
    model_nm = main_image()
    print("모델명 :", model_nm)
    retriever = search_manuals(query, model_nm)
    context, analysis = analyze_query_and_retrieve(query, retriever, llm)
    # 2. CoT 프롬프트로 답변 생성
    response = cot_prompt.invoke({
        "query": query,
        "analysis": analysis,
        "context": context
    })
    
    return llm.invoke(response)


