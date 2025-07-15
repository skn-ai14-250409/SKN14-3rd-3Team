import streamlit as st
import time
import datetime
from typing import List, Dict

# 페이지 설정
st.set_page_config(
    page_title="LG 세탁기/건조기 매뉴얼 Q&A 챗봇",
    page_icon="🧺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일링 - 카톡/인스타그램 DM 스타일
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #f8f9fa;
    }

    /* 메인 컨테이너 */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        background-color: white;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        overflow: hidden;
    }

    /* 헤더 */
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
    }

    .chat-header h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
    }

    .chat-header p {
        margin: 5px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }

    /* 채팅 영역 */
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background-color: #fafafa;
        scroll-behavior: smooth;
    }

    /* 메시지 버블 공통 스타일 */
    .message {
        display: flex;
        margin: 10px 0;
        animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* 사용자 메시지 (오른쪽) */
    .user-message {
        justify-content: flex-end;
    }

    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 20px 20px 5px 20px;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    /* 봇 메시지 (왼쪽) */
    .bot-message {
        justify-content: flex-start;
    }

    .bot-bubble {
        background: white;
        color: #333;
        padding: 12px 16px;
        border-radius: 20px 20px 20px 5px;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #f0f0f0;
    }

    /* 시간 표시 */
    .message-time {
        font-size: 11px;
        color: #999;
        margin: 5px 10px;
        text-align: center;
    }

    /* 입력 영역 */
    .input-container {
        padding: 20px;
        background: white;
        border-top: 1px solid #e0e0e0;
        display: flex;
        gap: 10px;
        align-items: center;
    }

    /* 빠른 질문 버튼 */
    .quick-questions {
        padding: 15px 20px;
        background: #f8f9fa;
        border-top: 1px solid #e0e0e0;
    }

    .quick-question-btn {
        background: white;
        border: 1px solid #ddd;
        padding: 8px 16px;
        margin: 5px;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s;
        display: inline-block;
    }

    .quick-question-btn:hover {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }

    /* 상태 표시 */
    .status-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 10px;
        color: #666;
        font-size: 14px;
    }

    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .typing-dots {
        display: flex;
        gap: 3px;
    }

    .typing-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #667eea;
        animation: typing 1.4s infinite;
    }

    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes typing {
        0%, 60%, 100% { transform: scale(0.8); opacity: 0.5; }
        30% { transform: scale(1.2); opacity: 1; }
    }

    /* 스크롤바 스타일 */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }

    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }

    .chat-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }

    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }

    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main-container {
            margin: 0;
            border-radius: 0;
            height: 100vh;
        }

        .user-bubble, .bot-bubble {
            max-width: 85%;
        }
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "bot",
        "content": "안녕하세요! 🧺 LG 세탁기/건조기 매뉴얼 Q&A 챗봇입니다.\n\n궁금한 점이 있으시면 언제든 물어보세요!\n예: 세탁 시간, 오류 코드, 관리 방법 등",
        "timestamp": datetime.datetime.now().strftime("%H:%M")
    })

if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

# 빠른 질문 목록
QUICK_QUESTIONS = [
    "세탁 시간이 얼마나 걸리나요?",
    "드럼 청소는 어떻게 하나요?",
    "오류 코드 해결 방법",
    "세탁기가 안 돌아가요",
    "건조기 필터 청소법",
    "세탁량 추천",
    "세제 사용법",
    "냄새 제거 방법"
]


def add_message(role: str, content: str):
    """메시지 추가 함수"""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })


def simulate_bot_response(user_input: str) -> str:
    """봇 응답 시뮬레이션 (실제 구현에서는 LLM API 호출)"""
    responses = {
        "세탁 시간": "일반적으로 표준 세탁 코스는 약 45분-1시간 정도 소요됩니다. 세탁량과 오염도에 따라 달라질 수 있어요. 🕐",
        "드럼 청소": "드럼 청소는 월 1회 권장합니다.\n\n1. 드럼 클린 코스 선택\n2. 드럼 전용 세제 투입\n3. 세탁기 가동\n4. 완료 후 문 열어 건조\n\n정기적인 청소로 냄새와 세균을 예방할 수 있어요! ✨",
        "오류 코드": "오류 코드를 알려주시면 정확한 해결 방법을 안내해드릴게요!\n\n자주 발생하는 오류:\n• IE: 급수 오류\n• OE: 배수 오류\n• UE: 불균형 오류\n• dE: 문 열림 오류",
        "안 돌아가": "세탁기가 작동하지 않는 경우:\n\n1. 전원 확인\n2. 문이 제대로 닫혔는지 확인\n3. 급수 밸브 확인\n4. 필터 청소 상태 확인\n\n그래도 해결되지 않으면 고객센터(1588-7777)로 연락주세요! 📞",
        "필터 청소": "건조기 필터는 매 사용 후 청소해주세요:\n\n1. 필터 분리\n2. 미지근한 물에 세척\n3. 완전히 건조 후 장착\n\n필터가 막히면 건조 효율이 떨어져요! 🔧",
        "세탁량": "세탁기 용량의 70-80% 정도가 적당합니다:\n\n• 10kg 세탁기: 7-8kg\n• 17kg 세탁기: 12-14kg\n\n너무 많이 넣으면 세탁 효과가 떨어져요! ⚖️",
        "세제": "세제는 세탁량과 오염도에 맞게 사용하세요:\n\n• 표준 세탁: 계량컵 1컵\n• 강력 세탁: 계량컵 1.5컵\n• 울/섬세: 계량컵 0.5컵\n\n액체세제 사용을 권장해요! 🧴",
        "냄새": "세탁기 냄새 제거 방법:\n\n1. 드럼 클린 코스 실행\n2. 사용 후 문 열어두기\n3. 세제함 정기 청소\n4. 고무 패킹 청소\n\n정기적인 관리가 중요해요! 🌟"
    }

    # 키워드 매칭으로 응답 찾기
    for keyword, response in responses.items():
        if keyword in user_input:
            return response

    return "죄송하지만 정확한 답변을 찾지 못했어요. 😅\n\n다른 방식으로 질문해주시거나, 구체적인 모델명과 함께 문의해주시면 더 정확한 답변을 드릴 수 있어요!\n\n고객센터: 1588-7777"


def display_chat():
    """채팅 메시지 표시"""
    chat_html = '<div class="chat-container">'

    for i, message in enumerate(st.session_state.messages):
        role = message['role']
        content = message['content']
        timestamp = message['timestamp']

        if role == 'user':
            chat_html += f'''
            <div class="message user-message">
                <div class="user-bubble">{content}</div>
            </div>
            <div class="message-time">{timestamp}</div>
            '''
        else:
            chat_html += f'''
            <div class="message bot-message">
                <div class="bot-bubble">{content}</div>
            </div>
            <div class="message-time">{timestamp}</div>
            '''

    # 타이핑 인디케이터
    if st.session_state.is_typing:
        chat_html += '''
        <div class="message bot-message">
            <div class="bot-bubble">
                <div class="typing-indicator">
                    <span>답변 작성 중</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        </div>
        '''

    chat_html += '</div>'

    return chat_html


def main():
    # 메인 컨테이너
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # 헤더
    st.markdown('''
    <div class="chat-header">
        <h1>🧺 LG 세탁기/건조기 매뉴얼 Q&A</h1>
        <p>AI 어시스턴트가 24시간 도움을 드려요</p>
    </div>
    ''', unsafe_allow_html=True)

    # 채팅 영역
    chat_container = st.container()
    with chat_container:
        st.markdown(display_chat(), unsafe_allow_html=True)

    # 빠른 질문 버튼
    st.markdown('<div class="quick-questions"><strong>💬 빠른 질문:</strong></div>', unsafe_allow_html=True)

    # 빠른 질문 버튼들을 3개씩 배열
    cols = st.columns(3)
    for i, question in enumerate(QUICK_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"quick_{i}", help=f"'{question}' 질문하기"):
                add_message("user", question)
                st.session_state.is_typing = True
                st.rerun()

    # 메시지 입력 영역
    with st.container():
        col1, col2 = st.columns([8, 1])

        with col1:
            user_input = st.text_input(
                "메시지를 입력하세요...",
                key="user_input",
                label_visibility="collapsed",
                placeholder="세탁기/건조기 관련 질문을 입력해주세요"
            )

        with col2:
            send_button = st.button("전송", key="send", type="primary")

    # 메시지 전송 처리
    if (send_button or user_input) and user_input.strip():
        # 사용자 메시지 추가
        add_message("user", user_input)
        st.session_state.is_typing = True

        # 입력 필드 초기화
        st.session_state.user_input = ""
        st.rerun()

    # 봇 응답 생성 (타이핑 상태일 때)
    if st.session_state.is_typing:
        time.sleep(1)  # 타이핑 시뮬레이션

        # 마지막 사용자 메시지 가져오기
        last_user_message = ""
        for message in reversed(st.session_state.messages):
            if message['role'] == 'user':
                last_user_message = message['content']
                break

        # 봇 응답 생성
        bot_response = simulate_bot_response(last_user_message)
        add_message("bot", bot_response)
        st.session_state.is_typing = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 하단 정보
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
        <p>📞 고객센터: 1588-7777 | 🌐 www.lge.co.kr</p>
        <p>※ 이 챗봇은 AI 기반으로 운영되며, 정확한 정보는 공식 매뉴얼을 참고해주세요.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()