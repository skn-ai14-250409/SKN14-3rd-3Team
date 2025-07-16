import os
import json
import logging
from dotenv import load_dotenv
from pdfminer.high_level import extract_text
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Mac에서 pdfminer 경고 무시
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def extract_text_from_pdf(pdf_path):
    """PDF 텍스트 추출"""
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"PDF 읽기 실패 {pdf_path}: {e}")
        return ""

def analyze_query_and_retrieve(query: str, retriever, llm):
    """쿼리 분석 + 관련 정보 검색"""
    prompt = ChatPromptTemplate.from_messages([
        ('system', """
        당신은 사용자의 질문을 분석하는 전문가입니다.
        다음 정보를 JSON으로 출력하세요:
        {{
            "keywords": ["키워드1", "키워드2"],
            "main_topic": "주제",
            "conditions": ["조건1"],
            "details": ["세부사항1"]
        }}"""),
        ('human', "질문: {query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    analysis_result = chain.invoke({"query": query})
    
    # JSON 파싱
    try:
        data = json.loads(analysis_result)
        keywords = data.get("keywords", [])
    except Exception:
        keywords = [query]
    
    # 키워드별 검색
    all_contexts = []
    for keyword in keywords:
        try:
            docs = retriever.invoke(keyword)
            all_contexts.extend(docs)
        except:
            continue
    
    # 중복 제거
    unique = []
    seen = set()
    for doc in all_contexts:
        if doc.page_content not in seen:
            unique.append(doc)
            seen.add(doc.page_content)
    
    combined_context = "\n\n".join([doc.page_content for doc in unique[:10]])
    return combined_context, analysis_result

def enhanced_chain(query: str, retriever, llm, cot_prompt):
    context, analysis = analyze_query_and_retrieve(query, retriever, llm)
    prompt_filled = cot_prompt.invoke({
        "query": query,
        "analysis": analysis,
        "context": context
    })
    return llm.invoke(prompt_filled)

def run_chatbot():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectordb = Chroma(
        collection_name="samsung_manuals",
        embedding_function=embeddings,
        persist_directory="./chroma",
    )

    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 8, "fetch_k": 20})
    
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)

    cot_prompt = ChatPromptTemplate.from_messages([
        ('system', """
        Elaborate on the topic using a Tree of Thoughts and backtrack when necessary to construct a clear, cohesive Chain of Thought reasoning.
        당신은 스마트한 가전 도우미입니다. 체계적으로 답변하세요:
        ## 질문 분석
        [분석 내용]
        ## 관련 정보
        [정보]
        ## 답변
        ### 1. [조건 A]
        ### 2. [조건 B]
        ## 추가 안내
        """),
        ('human', """
        질문: {query}
        분석: {analysis}
        컨텍스트: {context}
        """)
    ])

    print("="*60)
    print("🤖 삼성 세탁기/건조기 도우미")
    print("="*60)

    while True:
        try:
            query = input("\n💬 질문을 입력하세요 (종료하려면 '종료'): ").strip()
            if query.lower() == '종료':
                print("👋 종료합니다.")
                break
            if not query:
                print("❌ 질문을 입력해주세요.")
                continue

            print("🔍 답변 생성 중...")
            result = enhanced_chain(query, retriever, llm, cot_prompt)

            print("="*60)
            print(result.content)
            print("="*60)
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    run_chatbot()
