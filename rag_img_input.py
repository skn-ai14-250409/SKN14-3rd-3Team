from rag_indexer_class import IndexConfig, RAGIndexer


def main():
    """메인 실행 함수"""

    # 설정 생성
    config = IndexConfig(
        persistent_directory="./chroma",
        collection_name="imgs",
        embedding_model="text-embedding-3-small",
        figures_directory="./data/imgs",
    )

    # 인덱서 생성 및 실행
    indexer = RAGIndexer(config)

    # 기존 컬렉션 정보 출력
    info = indexer.get_collection_info()
    print(f"Current collection info: {info}")

    # 이미지 인덱싱 실행
    indexer.index_images(batch_size=100)

    # 완료 후 컬렉션 정보 출력
    info = indexer.get_collection_info()
    print(f"Final collection info: {info}")


if __name__ == "__main__":
    main()
