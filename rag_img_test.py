from rag_indexer_class import IndexConfig, RAGIndexer
from utils.index import image_to_base64


def main():
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
    indexer.search_and_show(img_base64)


if __name__ == "__main__":
    main()
