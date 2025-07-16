import glob
import os
import io
from tqdm import tqdm
from PIL import Image

import tiktoken
import pytesseract
from pdfminer.high_level import extract_text
import fitz

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_pdf_files(base_dir):
    """PDF 파일 목록 가져오기"""
    pdf_pattern = os.path.join(base_dir, "*.pdf")
    return glob.glob(pdf_pattern)


def extract_text_from_pdf(pdf_path: str) -> list[Document]:
    """PDF 텍스트 추출하기"""
    try:
        doc = fitz.open(pdf_path)
        documents = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 1. 먼저 텍스트 추출 시도
            text = page.get_text() # extract_text ffrom pdfminer.high_level import extract_text
            
            # 2. 텍스트가 충분하지 않으면 이미지에서 OCR 수행
            if len(text.strip()) < 50:  # 텍스트가 적으면 이미지 처리
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                ocr_text = pytesseract.image_to_string(img, lang="kor")
                
                # OCR 결과가 더 나으면 사용
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
            
            metadata = {"page": page_num + 1, "source": pdf_path}
            
            if text.strip():  # 빈 페이지 방지
                documents.append(Document(page_content=text, metadata=metadata))
        
        return documents
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
    BASE_DIR = "./data/samsung_manuals/"
    # PDF_NAME = "아가사랑_3kg_WA30DG2120EE.pdf"

    # docs = process_pdf_text(BASE_DIR + PDF_NAME)
    # print(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma(
        collection_name="samsung_manuals",
        embedding_function=embeddings,
        persist_directory="./chroma",
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