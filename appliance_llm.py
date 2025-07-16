import os
import json
import logging
from dotenv import load_dotenv
from pdfminer.high_level import extract_text
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_tavily import TavilySearch
from langchain_core.documents import Document
from rag_indexer_class import IndexConfig, RAGIndexer
from utils.index import image_to_base64


# pdfminer 경고 무시
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def search_vector_db_image(img_path):
    """백터 디비에서 이미지의 모델을 가져온다"""

    # 설정 생성
    config = IndexConfig(
        persistent_directory="./chroma",
        collection_name="samsung_imgs",
        embedding_model="text-embedding-3-small",
    )

    # 인덱서 생성 및 실행
    indexer = RAGIndexer(config)

    # 이미지 로드해서 모델명 검색
    img_base64 = image_to_base64(img_path)

    # 유사도 검색
    model_nm = indexer.search_and_show(img_base64)
    return model_nm


def extract_text_from_pdf(pdf_path):
    """PDF 텍스트 추출"""
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"PDF 읽기 실패 {pdf_path}: {e}")
        return ""


def analyze_query_and_retrieve(query: str, retriever, llm):
    # 질문 분석 프롬프트
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
        당신은 사용자의 질문을 분석하는 전문가입니다.
        다음 정보를 JSON으로 출력하세요:
        {{
            "keywords": ["키워드1", "키워드2"],
            "main_topic": "주제",
            "conditions": ["조건1"],
            "details": ["세부사항1"]
        }}""",
            ),
            ("human", "질문: {query}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    analysis_result = chain.invoke({"query": query})

    # JSON 파싱
    try:
        data = json.loads(analysis_result)
        keywords = data.get("keywords", [])
    except Exception:
        keywords = [query]

    all_contexts = []

    # TavilySearch로 웹 검색 도구 설정
    tavily_tool = TavilySearch(max_results=5)

    try:
        # Tavily에서 검색
        search_result = tavily_tool.invoke({"query": query})

        # 'results' 리스트 추출
        web_results = search_result.get("results", [])

        # 각 결과를 Document로 변환
        for item in web_results:
            content = item.get("content", "")
            url = item.get("url", "")

            if content:  # 내용이 있으면 추가
                doc = Document(
                    page_content=content,
                    metadata={"source": url, "title": item.get("title", "")},
                )
                all_contexts.append(doc)
    except Exception as e:
        print(f"웹 검색 오류: {e}")

    # 기존 벡터 retriever도 검색
    for keyword in keywords:
        try:
            docs = retriever.invoke(keyword)
            all_contexts.extend(docs)
        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            continue

    return all_contexts, analysis_result


def enhanced_chain(query: str, retriever, llm, cot_prompt):
    context, analysis = analyze_query_and_retrieve(query, retriever, llm)
    prompt_filled = cot_prompt.invoke(
        {"query": query, "analysis": analysis, "context": context}
    )
    return llm.invoke(prompt_filled)


def run_chatbot():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectordb = Chroma(
        collection_name="samsung_manuals",
        embedding_function=embeddings,
        persist_directory="./chroma",
    )

    retriever = vectordb.as_retriever(
        search_type="mmr", search_kwargs={"k": 8, "fetch_k": 20}
    )

    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)

    cot_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
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
        """,
            ),
            (
                "human",
                """
        질문: {query}
        분석: {analysis}
        컨텍스트: {context}
        """,
            ),
        ]
    )

    print("=" * 60)
    print("🤖 삼성 세탁기/건조기 도우미")
    print("=" * 60)

    while True:
        try:
            query = input("\n💬 질문을 입력하세요 (종료하려면 '종료'): ").strip()
            if query.lower() == "종료":
                print("👋 종료합니다.")
                break
            if not query:
                print("❌ 질문을 입력해주세요.")
                continue

            print("🔍 답변 생성 중...")
            result = enhanced_chain(query, retriever, llm, cot_prompt)

            print("=" * 60)
            print(result.content)
            print("=" * 60)
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")


if __name__ == "__main__":
    run_chatbot()
