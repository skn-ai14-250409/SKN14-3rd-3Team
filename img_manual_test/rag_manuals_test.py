from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


def search_manuals(query: str, k: int = 5):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectordb = Chroma(
        collection_name="samsung_manuals",
        embedding_function=embeddings,
        persist_directory="./chroma",
    )

    """매뉴얼 검색"""
    docs = vectordb.similarity_search(query, k=k)

    for i, doc in enumerate(docs):
        print(f"\n[TOP-{i + 1}]")
        print(f'모델명: {doc.metadata.get("model_name", "Unknown")}')
        print(f'청크 ID: {doc.metadata.get("chunk_id", "Unknown")}')
        print(f'청크 (total): {doc.metadata.get("total_chunks", "Unknown")}')
        print(f"내용: {doc.page_content[:200]}...")
        print("-" * 50)


def main():
    """메인 실행 함수"""
    search_manuals("주의 사항 알려줘")


if __name__ == "__main__":
    main()
