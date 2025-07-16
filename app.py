import os
import json
import time
import streamlit as st
import html
from PIL import Image
from datetime import datetime
from app_llm_cli import run_chatbot


# 페이지 설정
st.set_page_config(
    page_title="LG 세탁기/건조기 매뉴얼 Q&A",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS 스타일링
st.markdown(
    """
<style>
    .chat-header { text-align: center; padding: 10px; background-color: #f5f5f5; border-radius: 10px; }
    .chat-container { padding: 20px; background-color: #fff; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .chat-messages { max-height: 400px; overflow-y: auto; padding: 10px; }
    .message { display: flex; align-items: flex-start; margin: 10px 0; }
    .user { justify-content: flex-end; }
    .bot { justify-content: flex-start; }
    .avatar { font-size: 24px; margin: 0 10px; }
    .message-content { background-color: #e0f7fa; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word; }
    .user .message-content { background-color: #b3e5fc; }
    .message-time { font-size: 12px; color: #666; margin-top: 5px; align-self: flex-end; }
    .system-message { text-align: center; color: #888; font-size: 14px; margin: 10px 0; }
    .typing-indicator { display: flex; align-items: center; color: #666; }
    .typing-dots { font-size: 20px; }
    .chat-input { margin-top: 20px; }
</style>
""",
    unsafe_allow_html=True,
)

# "temp" 폴더 생성
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# 세션 상태 초기화: 여러 대화 관리
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False

# 대화 기록이 모두 삭제되었거나 초기 상태일 때 KeyError 방지 및 복구
if not st.session_state.conversations:
    new_id = "1"
    st.session_state.conversations[new_id] = {
        "title": "대화 1",
        "messages": [
            {
                "role": "system",
                "content": "LG 세탁기/건조기 매뉴얼 Q&A 챗봇이 시작되었습니다.",
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        ],
        "image": None,
    }
    st.session_state.current_conversation_id = new_id

if st.session_state.current_conversation_id not in st.session_state.conversations:
    st.session_state.current_conversation_id = list(
        st.session_state.conversations.keys()
    )[0]

# 샘플 FAQ 데이터
SAMPLE_FAQS = [
    "세탁기 에러코드 해결법",
    "건조기 필터 청소 방법",
    "세탁 용량 가이드",
    "세탁기 소음 해결법",
    "건조 시간 단축 방법",
]

# 헤더
st.markdown(
    """
<div class="chat-header">
    <h1>세탁기/건조기 매뉴얼 Q&A</h1>
    <p>궁금한 점을 언제든지 물어보세요!</p>
</div>
""",
    unsafe_allow_html=True,
)

# 메인 레이아웃
col1, col2, col3 = st.columns([2, 4, 2])

# 왼쪽: 대화 목록 (히스토리)
with col1:
    st.markdown("### 대화 목록")
    for conv_id, conv in st.session_state.conversations.copy().items():
        if st.button(conv["title"], key=f"conv_{conv_id}", use_container_width=True):
            st.session_state.current_conversation_id = conv_id
            st.rerun()
    if st.button("새 대화 시작", use_container_width=True, type="primary"):
        new_id = str(int(max(list(st.session_state.conversations.keys()) or ["0"])) + 1)
        st.session_state.conversations[new_id] = {
            "title": f"대화 {new_id}",
            "messages": [
                {
                    "role": "system",
                    "content": "새 대화가 시작되었습니다.",
                    "timestamp": datetime.now().strftime("%H:%M"),
                }
            ],
            "image": None,
        }
        st.session_state.current_conversation_id = new_id
        st.rerun()

# 현재 대화 정보
current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
messages = current_conv["messages"]

# 중앙: 현재 대화
with col2:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    messages_container = st.container()
    with messages_container:
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        for message in messages:
            if message["role"] == "system":
                st.markdown(
                    f'<div class="system-message">{message["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                role_class = "user" if message["role"] == "user" else "bot"
                avatar_icon = "👤" if message["role"] == "user" else "🤖"

                # [수정 1] 메시지 내용을 HTML에 안전하게 삽입하도록 처리
                sanitized_content = html.escape(message["content"])
                message_html = sanitized_content.replace("\n", "<br>").replace("•", "•")

                # 사용자 메시지와 봇 메시지의 레이아웃을 분리하여 타임스탬프 위치 조정
                if message["role"] == "user":
                    st.markdown(
                        f"""
                    <div class="message user">
                        <div class="message-time">{message["timestamp"]}</div>
                        <div class="message-content">{message_html}</div>
                        <div class="avatar">{avatar_icon}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:  # role == 'assistant'
                    st.markdown(
                        f"""
                    <div class="message bot">
                        <div class="avatar">{avatar_icon}</div>
                        <div class="message-content">{message_html}</div>
                        <div class="message-time">{message["timestamp"]}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        if st.session_state.is_typing:
            st.markdown(
                """
            <div class="message bot">
                <div class="avatar">🤖</div>
                <div class="typing-indicator">
                    <span>답변을 작성 중입니다</span><span class="typing-dots">...</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("**💡 빠른 질문**")
    cols = st.columns(len(SAMPLE_FAQS))
    for i, faq in enumerate(SAMPLE_FAQS):
        with cols[i]:
            if st.button(
                faq,
                key=f"faq_{i}_{st.session_state.current_conversation_id}",
                help=f"{faq}에 대해 질문하기",
            ):
                current_conv["messages"].append(
                    {
                        "role": "user",
                        "content": faq,
                        "timestamp": datetime.now().strftime("%H:%M"),
                    }
                )
                st.session_state.is_typing = True
                st.rerun()

    st.markdown("**📷 이미지 업로드 및 질문**")
    with st.form(
        key=f"chat_form_{st.session_state.current_conversation_id}",
        clear_on_submit=True,
    ):
        user_input = st.text_input(
            "메시지를 입력하세요...",
            placeholder="세탁기/건조기에 대해 궁금한 점을 물어보세요!",
            label_visibility="collapsed",
        )
        uploaded_image = st.file_uploader(
            "이미지 첨부 (선택 사항)",
            type=["jpg", "jpeg", "png"],
            key=f"image_uploader_{st.session_state.current_conversation_id}",
        )
        send_button = st.form_submit_button("전송", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 오른쪽: 이미지 및 스펙
with col3:
    st.markdown("### 업로드된 이미지 및 스펙")
    if current_conv["image"]:
        # [수정 2] use_column_width 를 use_container_width 로 변경하여 경고 제거
        st.image(
            current_conv["image"], caption="업로드된 이미지", use_container_width=True
        )
        try:
            image = Image.open(current_conv["image"])
            st.write(f"**파일명**: {os.path.basename(current_conv['image'])}")
            st.write(f"**크기**: {os.path.getsize(current_conv['image'])} bytes")
            st.write(f"**해상도**: {image.width} x {image.height} pixels")
        except FileNotFoundError:
            st.error("이미지 파일을 찾을 수 없습니다. 다시 업로드해주세요.")
            current_conv["image"] = None
    else:
        st.info("현재 대화에 업로드된 이미지가 없습니다.")

# 메시지 처리 로직
if send_button:
    image_processed = False
    if uploaded_image is not None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = os.path.join(TEMP_DIR, f"{timestamp}_{uploaded_image.name}")
        with open(image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
        current_conv["image"] = image_path

        # 텍스트 입력이 있을 때와 없을 때를 구분하여 메시지 추가
        if not user_input:
            current_conv["messages"].append(
                {
                    "role": "user",
                    "content": "이미지를 업로드했습니다.",
                    "timestamp": datetime.now().strftime("%H:%M"),
                }
            )
        image_processed = True

    if user_input:
        # 이미지가 함께 업로드된 경우, 메시지를 하나로 합치기
        content = f"이미지 첨부: {user_input}" if image_processed else user_input
        current_conv["messages"].append(
            {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )

    if user_input or image_processed:
        st.session_state.is_typing = True
        st.rerun()

# 봇 응답 시뮬레이션
if st.session_state.is_typing:
    time.sleep(1)
    last_user_message = ""
    for msg in reversed(current_conv["messages"]):
        if msg["role"] == "user":
            last_user_message = msg["content"]
            break

    sample_responses = {
        "세탁기 에러코드 해결법": "세탁기 에러코드별 해결법을 안내드리겠습니다:\n\n• **IE 에러**: 급수 문제 - 수도꼭지 확인\n• **OE 에러**: 배수 문제 - 배수호스 점검\n• **UE 에러**: 불균형 - 세탁물 재배치\n• **PE 에러**: 급수 압력 - 수압 확인\n\n구체적인 에러코드를 알려주시면 더 자세한 해결법을 안내드릴게요!",
        "건조기 필터 청소 방법": "건조기 필터 청소 방법을 단계별로 안내드립니다:\n\n1. **전원 끄기**: 안전을 위해 전원 차단\n2. **필터 분리**: 도어 하단 필터 손잡이로 빼내기\n3. **이물질 제거**: 손으로 보풀, 먼지 제거\n4. **물 세척**: 미지근한 물로 헹구기\n5. **건조 후 장착**: 완전히 말린 후 원위치\n\n✅ 매 사용 후 청소하시면 건조 효율이 높아집니다!",
        "세탁 용량 가이드": "세탁 용량별 가이드를 안내드립니다:\n\n**👕 의류별 기준**\n• 셔츠: 200-250g\n• 청바지: 500-600g\n• 수건: 300-400g\n• 이불: 1.5-2kg\n\n**🏠 가족 구성별 권장**\n• 1-2인: 8kg\n• 3-4인: 10-12kg\n• 5인 이상: 15kg+\n\n용량의 80%만 채우시면 세탁 효과가 최적화됩니다!",
        "세탁기 소음 해결법": "세탁기 소음 해결법을 안내드립니다:\n\n**🔧 체크포인트**\n1. **수평 조절**: 다리 높이 조정\n2. **바닥 확인**: 단단한 바닥에 설치\n3. **세탁물 양**: 적정량 준수\n4. **이물질 제거**: 동전, 단추 등 확인\n\n**🔇 소음 유형별 해결**\n• 진동음: 수평 재조정\n• 덜걱거림: 세탁물 재배치\n• 삐걱거림: 서비스 센터 문의\n\n문제가 지속되면 전문가 점검을 받으시길 권합니다.",
        "건조 시간 단축 방법": "건조 시간 단축 방법을 안내드립니다:\n\n**⚡ 효율적인 건조 팁**\n1. **적정 용량**: 용량의 70% 이하\n2. **필터 청소**: 매번 사용 전후\n3. **의류 분리**: 두께별 분리 건조\n4. **수분 제거**: 탈수 시간 연장\n\n**🌪️ 건조 모드 활용**\n• 면 소재: 일반 건조\n• 화학섬유: 저온 건조\n• 두꺼운 의류: 센서 건조\n\n올바른 사용법으로 시간과 전력을 절약하세요!",
        "이미지를 업로드했습니다.": "이미지를 확인했습니다. 업로드하신 이미지에 대해 무엇이 궁금하신가요?",
    }

    bot_response = sample_responses.get(
        last_user_message,
        f"'{last_user_message}'에 대한 질문을 접수했습니다. LG 세탁기/건조기 매뉴얼을 기반으로 가장 정확한 답변을 준비하고 있습니다. 잠시만 기다려주세요!",
    )

    image_path = None
    if current_conv["image"] is not None:
        image_path = os.path.abspath(current_conv["image"])

    current_conv["messages"].append(
        {
            "role": "assistant",
                       "content": run_chatbot(last_user_message, image_path=image_path),
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )
    st.session_state.is_typing = False
    st.rerun()

# 사이드바
with st.sidebar:
    st.markdown("### 📋 기능 메뉴")
    if st.button("🗑️ 모든 대화 기록 삭제", type="secondary"):
        st.session_state.conversations = {}
        st.session_state.current_conversation_id = None
        st.rerun()
    if st.button("📁 대화 기록 저장"):
        try:
            chat_history = {
                "timestamp": datetime.now().isoformat(),
                "conversations": st.session_state.conversations,
            }
            st.download_button(
                label="💾 JSON 다운로드",
                data=json.dumps(chat_history, ensure_ascii=False, indent=2),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )
        except Exception as e:
            st.error(f"파일 저장 중 오류 발생: {e}")

    st.markdown("---")
    st.markdown("### 📊 통계")
    total_messages = sum(
        len(conv["messages"]) for conv in st.session_state.conversations.values()
    )
    st.metric("총 메시지", total_messages)
    st.metric("대화 수", len(st.session_state.conversations))

    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.info("이 챗봇은 LG 세탁기/건조기 매뉴얼을 기반으로 한 Q&A 시스템입니다.")

# 하단 정보
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 12px;'>"
    "LG 세탁기/건조기 매뉴얼 Q&A 챗봇 | "
    "LangChain + RAG 기술 기반 | "
    "실시간 매뉴얼 검색 지원"
    "</div>",
    unsafe_allow_html=True,
)
