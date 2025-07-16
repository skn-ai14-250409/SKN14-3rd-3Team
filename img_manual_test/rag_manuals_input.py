import glob
import logging
import os
import tiktoken
from tqdm import tqdm
from pdfminer.high_level import extract_text
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# pdfminer 경고 무시
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def get_pdf_files(base_dir):
    """하위 디렉토리 모든 PDF 파일 목록 가져오기"""
    pdf_pattern = os.path.join(base_dir, "**", "*.pdf")
    return glob.glob(pdf_pattern, recursive=True)


def extract_text_from_pdf(pdf_path):
    """PDF 텍스트 추출하기"""
    try:
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        print(f"PDF 읽기 실패 {pdf_path}: {e}")
        return ""


def process_pdf_text(pdf_path):
    """PDF 텍스트 처리 및 청크 분할"""
    # PDF에서 텍스트 추출
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        return []

    # 파일명에서 모델명 추출
    filename = os.path.basename(pdf_path)
    model_name = filename.replace(".pdf", "")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    )

    # 텍스트 청크로 분할
    chunks = text_splitter.split_text(text)

    # 각 청크에 메타데이터 추가
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        processed_chunks.append(
            {
                "text": chunk,
                "metadata": {
                    "model_name": model_name,
                    "chunk_id": i + 1,
                    "total_chunks": len(chunks),
                },
            }
        )

    return processed_chunks


MAX_TOKENS_PER_REQUEST = 300000
# text-embedding-3-small에 맞는 encoding
encoding = tiktoken.get_encoding("cl100k_base")


def batch_by_tokens(texts, metadatas, max_tokens=MAX_TOKENS_PER_REQUEST):
    batches = []
    current_texts = []
    current_metadatas = []
    current_tokens = 0

    for text, metadata in zip(texts, metadatas):
        tokens = len(encoding.encode(text))
        if tokens > max_tokens:
            # 너무 긴 단일 텍스트 → 따로 처리
            print(f"텍스트 하나가 {tokens} 토큰으로 너무 깁니다. 잘라서 넣으세요!")
            continue

        if current_tokens + tokens > max_tokens:
            # 현재 배치 마감
            batches.append((current_texts, current_metadatas))
            current_texts = []
            current_metadatas = []
            current_tokens = 0

        current_texts.append(text)
        current_metadatas.append(metadata)
        current_tokens += tokens

    # 마지막 배치 추가
    if current_texts:
        batches.append((current_texts, current_metadatas))

    return batches


def main():
    """메인 실행 함수"""
    BASE_DIR = "./data/manuals/"
    EMBEDDINGS_MODEL = "text-embedding-3-small"
    COLLECTION_NAME = "manuals"
    VECTOR_DB_DIR = "./chroma"

    embeddings = OpenAIEmbeddings(model=EMBEDDINGS_MODEL)
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=VECTOR_DB_DIR,
    )

    """PDF 텍스트 인덱싱"""
    # PDF 파일 목록 가져오기
    pdf_files = get_pdf_files(BASE_DIR)

    if not pdf_files:
        print("PDF 파일을 찾을 수 없습니다.")

    print(f"총 {len(pdf_files)}개의 PDF 파일을 처리합니다.")

    # 전체 텍스트 청크 저장
    all_chunks = []

    for pdf_path in tqdm(pdf_files, desc="PDF 처리 중"):
        chunks = process_pdf_text(pdf_path)
        all_chunks.extend(chunks)
        print(f"처리완료: {os.path.basename(pdf_path)} - {len(chunks)}개 청크")

    # 벡터 데이터베이스에 저장
    if all_chunks:
        print(f"\n총 {len(all_chunks)}개 청크를 벡터DB에 저장 중...")

        texts = [chunk["text"] for chunk in all_chunks]
        metadatas = [chunk["metadata"] for chunk in all_chunks]

        batches = batch_by_tokens(texts, metadatas)

        for batch_texts, batch_metadatas in tqdm(batches, desc="임베딩 배치 저장 중"):
            vectordb.add_texts(texts=batch_texts, metadatas=batch_metadatas)

        print("벡터DB 저장 완료!")
    else:
        print("처리할 텍스트가 없습니다.")


if __name__ == "__main__":
    main()
