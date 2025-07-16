import os
import json
import logging
import re
from dotenv import load_dotenv
from utils.index import image_to_base64
from pdfminer.high_level import extract_text
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_tavily import TavilySearch
from langchain_core.documents import Document
from rag_indexer_class import IndexConfig, RAGIndexer
from langchain.prompts import PromptTemplate



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
        collection_name="imgs",
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
        고객에게 적절한 호응과 함께 친절한 답변을 해주세요.
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


def enhanced_chain(query: str, retriever, llm, cot_prompt, history=[]):
    context, analysis = analyze_query_and_retrieve(query, retriever, llm)
    prompt_value = cot_prompt.invoke(
        {"query": query, "analysis": analysis, "context": context}
    )

    prompt_str = prompt_value.to_string()

    # history + 현재 질문 prompt를 합쳐 messages 구성
    messages = history + [{"role": "user", "content": prompt_str}]

    # LLM에 messages 전달
    response = llm.invoke(messages)

    return response


def run_chatbot(query, image_path=None, history=[]):
    EMBEDDINGS_MODEL = "text-embedding-3-small"
    COLLECTION_NAME = "manuals"
    VECTOR_DB_DIR = "./chroma"

    # 설정 생성
    config = IndexConfig(
        persistent_directory=VECTOR_DB_DIR,
        collection_name=COLLECTION_NAME,
        embedding_model=EMBEDDINGS_MODEL,
    )

    # 인덱서 생성 및 실행
    indexer = RAGIndexer(config)

    retriever = indexer.vectordb.as_retriever(
        search_type="mmr", search_kwargs={"k": 8, "fetch_k": 20}
    )

    model_code = search_vector_db_image(image_path)

    if image_path:
        query = f"{query} (모델코드: {model_code})"

    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)


    cot_prompt = PromptTemplate.from_template("""
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

    질문: {query}
    분석: {analysis}
    컨텍스트: {context}
    """)

    result = enhanced_chain(query, retriever, llm, cot_prompt, history=history)
    return result.content


def main():
    print("=" * 60)
    print("세탁기/건조기 도우미")
    print("=" * 60)

    history = []

    while True:
        try:
            query = input(
                "\n✅ 질문을 입력하세요 (이미지를 쓸 땐 img:/path/to/img, 종료하려면 '종료'): "
            ).strip()
            if query.lower() == "종료":
                print("✅  종료합니다.")
                break
            if not query:
                print("❌ 질문을 입력해주세요.")
                continue

            # 이미지 경로 입력 처리
            if query.startswith("img:"):
                raw_path = query[4:].strip()

                # 확장자 기준으로 경로를 깔끔하게 추출
                # 예: img:/home/user/test image.jpg something
                match = re.search(
                    r"(.+?\.(?:png|jpg|jpeg|webp))", raw_path, re.IGNORECASE
                )
                if not match:
                    print("올바른 이미지 파일 경로가 아닙니다.")
                    continue

                img_path = match.group(1).strip()

                if not os.path.exists(img_path):
                    print("이미지 파일을 찾을 수 없습니다.")
                    continue

                print("✅  이미지에서 모델명 추출 중...")
                model_nm = search_vector_db_image(img_path)
                print(f"✅ 감지된 모델명: {model_nm}")
                user_question = input("💬 질문 내용을 입력하세요: ").strip()
                if not user_question:
                    print("❌ 질문을 입력해주세요.")
                    continue
                # 모델명을 질문에 추가
                query = f"{user_question} (모델명: {model_nm})"

            # history에 사용자 입력 추가
            history.append({"role": "user", "content": query})

            print("🔍 답변 생성 중...")
            # run_chatbot이 history를 이용해 문맥 기반 응답을 생성하도록 설계
            result = run_chatbot(query, history=history)

            # history에 모델 응답 추가
            history.append({"role": "assistant", "content": result.content})

            print("=" * 60)
            print(result.content)
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n✅ 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()
