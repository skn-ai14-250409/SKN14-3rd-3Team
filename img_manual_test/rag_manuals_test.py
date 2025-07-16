from rag_indexer_class import IndexConfig, RAGIndexer


def search_manuals(query: str, k: int = 5):
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

    """매뉴얼 검색"""
    docs = indexer.vectordb.similarity_search(query, k=k)

    for i, doc in enumerate(docs):
        print(f"\n[TOP-{i + 1}]")
        print(f'모델명: {doc.metadata.get("model_name", "Unknown")}')
        print(f'청크 ID: {doc.metadata.get("chunk_id", "Unknown")}')
        print(f'청크 (total): {doc.metadata.get("total_chunks", "Unknown")}')
        print(f"내용: {doc.page_content[:200]}...")
        print("-" * 50)


def main():
    """메인 실행 함수"""
    search_manuals("아가사랑_3kg_WA30DG2120EE의 주의 사항")


if __name__ == "__main__":
    main()
