from rag_indexer_class import IndexConfig, RAGIndexer
from utils.index import image_to_base64


def main():
    """메인 실행 함수"""

    VECTOR_DB_DIR = "./chroma"
    COLLECTION_NAME = "imgs"
    EMBEDDINGS_MODEL = "text-embedding-3-small"

    # 설정 생성
    config = IndexConfig(
        persistent_directory=VECTOR_DB_DIR,
        collection_name=COLLECTION_NAME,
        embedding_model=EMBEDDINGS_MODEL,
    )

    # 인덱서 생성 및 실행
    indexer = RAGIndexer(config)

    # 이미지 로드해서 모델명 검색
    img = "./data/imgs/samsung/아가사랑_3kg_WA30DG2120EE/그레이지/아가사랑_3kg_WA30DG2120EE_그레이지_0001.png"
    img_base64 = image_to_base64(img)

    # 유사도 검색
    result = indexer.search_and_show(img_base64)
    print(result)


if __name__ == "__main__":
    main()
