import streamlit as st
import time
from datetime import datetime, timedelta

# 1. 초기 세션 및 학습 메모리 설정
if "messages" not in st.session_state:
    st.session_state.messages = []
if "learning_note" not in st.session_state:
    st.session_state.learning_note = []  # 주인의 가르침 저장소
if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "생수": {"last_asked": datetime.now() - timedelta(days=7), "status": "보통"},
        "세제": {"last_asked": datetime.now() - timedelta(days=20), "status": "부족"}
    }
if "persona" not in st.session_state:
    st.session_state.persona = "민아"

# 2. 페르소나 및 학습 기반 답변 로직
def generate_response(user_input):
    # 학습된 내용이 있는지 먼저 확인
    correction = next((note['correct'] for note in st.session_state.learning_note if note['wrong'] in user_input), None)
    
    if "틀렸어" in user_input or "아니야" in user_input:
        return "몰라서 그랬어 미안! 알려주면 고치께. 뭐가 맞는 거야?"
    
    if correction:
        return f"[{st.session_state.persona}] 아 맞다, {correction}라고 했지! 기억하고 있어."

    # 기본 페르소나 답변 (Gemini Nano 역할 대행)
    if "안녕" in user_input:
        return f"[{st.session_state.persona}] 왔어? 뭐 필요한 거 있어?"
    elif "세제" in user_input:
        return f"[{st.session_state.persona}] 세제 거의 다 써가던데, 더 살까?"
    else:
        return f"[{st.session_state.persona}] 음, 무슨 소린지 잘 모르겠어. 더 가르쳐줘!"

# --- UI 레이아웃 (모바일 최적화) ---
st.set_page_config(page_title="재알메", layout="centered")
st.title(f"🏠 재알메 v3.6 ({st.session_state.persona})")

# 3. 음성 인식(STT) 및 출력(TTS) 자바스크립트 브릿지
st.components.v1.html(
    """
    <script>
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ko-KR';
    
    function speak(text) {
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'ko-KR';
        window.speechSynthesis.speak(msg);
    }

    function startListening() {
        recognition.start();
        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            window.parent.postMessage({type: 'stt', text: text}, '*');
        };
    }
    // Streamlit에서 메시지를 받아 TTS 실행
    window.addEventListener('message', (e) => {
        if (e.data.type === 'tts') speak(e.data.text);
    });
    </script>
    <button onclick="startListening()" style="width:100%; height:50px; border-radius:10px; background-color:#FF4B4B; color:white; border:none; font-weight:bold;">
        🎤 내 목소리 들려주기 (클릭해서 대화)
    </button>
    """,
    height=70,
)

# 4. 대화창 및 학습 데이터 처리
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 사용자 입력 처리 (텍스트 입력 및 음성 데이터 시뮬레이션)
if prompt := st.chat_input("재알메에게 가르쳐줄 내용 입력"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 학습 모드: 이전 대답이 틀렸다고 했을 때 다음 입력을 정답으로 저장
    if len(st.session_state.messages) > 1 and "몰라서 그랬어" in st.session_state.messages[-2]["content"]:
        st.session_state.learning_note.append({"wrong": "이전내용", "correct": prompt})
        response = "응! 이제 확실히 배웠어. 고마워!"
    else:
        response = generate_response(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # TTS 실행을 위한 스크립트 트리거 (음성 출력)
    st.components.v1.html(f"<script>window.parent.postMessage({{type: 'tts', text: '{response}'}}, '*');</script>", height=0)
    st.rerun()

# 사이드바: 학습 장부 확인
with st.sidebar:
    st.header("📝 재알메 학습 장부")
    if not st.session_state.learning_note:
        st.write("아직 배운 게 없어요.")
    for note in st.session_state.learning_note:
        st.caption(f"수정됨: {note['correct']}")
