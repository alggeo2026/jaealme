import streamlit as st
import time
from datetime import datetime, timedelta

# [유지] 1. 초기 세션 및 학습 메모리 설정
if "messages" not in st.session_state:
    st.session_state.messages = []
if "learning_note" not in st.session_state:
    st.session_state.learning_note = [] 
if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "생수": {"last_asked": datetime.now() - timedelta(days=7), "status": "보통"},
        "세제": {"last_asked": datetime.now() - timedelta(days=20), "status": "부족"},
        "치약": {"last_asked": datetime.now() - timedelta(days=40), "status": "보통"},
        "참기름": {"last_asked": datetime.now() - timedelta(days=40), "status": "보통"}
    }
if "persona" not in st.session_state:
    st.session_state.persona = "민아"

# [유지] 2. 페르소나 및 학습 기반 답변 로직
def generate_response(user_input):
    correction = next((note['correct'] for note in st.session_state.learning_note if note['wrong'] in user_input), None)
    
    if any(word in user_input for word in ["틀렸어", "아니야", "그거 아냐", "잘못알았어"]):
        return "몰라서 그랬어 미안! 알려주면 고치께. 뭐가 맞는 거야?"
    
    if correction:
        return f"[{st.session_state.persona}] 아 맞다, {correction}라고 했지! 이번엔 진짜 안 잊어버릴게."

    if "안녕" in user_input:
        return f"[{st.session_state.persona}] 왔어? 밖은 어때? 뭐 필요한 거 있어?"
    elif "세제" in user_input:
        return f"[{st.session_state.persona}] 세제 거의 다 써가던데, 더 살까?"
    elif "물소리" in user_input or "물" in user_input:
        return f"[{st.session_state.persona}] 생수랑 세제 체크해볼까?"
    else:
        return f"[{st.session_state.persona}] 음, 무슨 소린지 잘 모르겠어. 더 가르쳐줘!"

# --- UI 레이아웃 (모바일 최적화) ---
st.set_page_config(page_title="재알메", layout="centered")
st.title(f"🏠 재알메 v3.9 ({st.session_state.persona})")

# [완결판] 3. 강력한 음성 인식 & 자동 전송 브릿지
# 폰 브라우저의 보안 정책을 우회하여 채팅창에 즉시 텍스트를 배달합니다.
st.components.v1.html(
    """
    <script>
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ko-KR';
    recognition.continuous = false;
    recognition.interimResults = false;

    function updateBtn(text, color) {
        const btn = document.getElementById('micBtn');
        if (btn) {
            btn.innerText = text;
            btn.style.background = color;
        }
    }

    function speak(text) {
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'ko-KR';
        window.speechSynthesis.speak(msg);
    }

    recognition.onstart = () => updateBtn('🎤 듣고 있어요...', '#28a745');
    recognition.onspeechend = () => updateBtn('🧠 생각 중...', '#ffc107');
    
    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        updateBtn('✅ 인식: ' + text, '#007bff');
        
        // 부모 창(Streamlit)의 모든 요소를 뒤져서 채팅창을 찾아냅/니다.
        const findAndFill = () => {
            const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (textArea) {
                const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                setter.call(textArea, text);
                textArea.dispatchEvent(new Event('input', { bubbles: true }));
                
                setTimeout(() => {
                    const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (sendBtn) sendBtn.click();
                    updateBtn('🎤 눌러서 재알메 깨우기', '#FF4B4B');
                }, 600);
            }
        };
        findAndFill();
    };

    recognition.onerror = (e) => {
        console.error(e);
        updateBtn('❌ 다시 시도 (클릭)', '#dc3545');
    };

    window.addEventListener('message', (e) => {
        if (e.data.type === 'tts') speak(e.data.text);
    });
    </script>
    <button id="micBtn" onclick="recognition.start()" style="width:100%; height:80px; border-radius:20px; background: #FF4B4B; color:white; border:none; font-size:22px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        🎤 눌러서 재알메 깨우기
    </button>
    """,
    height=110,
)

# [유지] 4. 대화창 처리
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# [보완] 실시간 입력 및 학습 로직
if prompt := st.chat_input("재알메에게 직접 가르치기"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 학습 모드: "미안" 답변 직후의 입력을 정답으로 저장
    if len(st.session_state.messages) > 1 and "몰라서 그랬어" in st.session_state.messages[-2]["content"]:
        st.session_state.learning_note.append({"wrong": "이전내용", "correct": prompt})
        response = f"[{st.session_state.persona}] 아하, 그렇구나! 이제 확실히 배웠어. 고마워!"
    else:
        response = generate_response(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # TTS 음성 출력 트리거 (대괄호 제거 후 순수 텍스트만 읽기)
    clean_response = response.replace('[', '').replace(']', '')
    st.components.v1.html(f"<script>window.parent.postMessage({{type: 'tts', text: '{clean_response}'}}, '*');</script>", height=0)
    st.rerun()
