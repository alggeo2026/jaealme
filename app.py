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

# [보완] 2. 유연한 키워드 매칭 답변 로직
def generate_response(user_input):
    # 학습된 내용 우선 확인 (부분 일치로 개선)
    correction = next((note['correct'] for note in st.session_state.learning_note if note['wrong'] in user_input), None)
    
    if any(word in user_input for word in ["틀렸어", "아니야", "그거 아냐", "잘못알았어"]):
        return "몰라서 그랬어 미안! 알려주면 고치께. 뭐가 맞는 거야?"
    
    if correction:
        return f"[{st.session_state.persona}] 아 맞다, {correction}라고 했지! 이제 확실히 기억나."

    # 키워드 기반 유연한 응대 (정확히 일치하지 않아도 반응함)
    if any(word in user_input for word in ["안녕", "안녕히", "반가워", "하이"]):
        return f"[{st.session_state.persona}] 왔어? 뭐 필요한 거 있어?"
    elif "세제" in user_input:
        return f"[{st.session_state.persona}] 세제 거의 다 써가던데, 더 살까?"
    elif any(word in user_input for word in ["물", "생수", "음료"]):
        return f"[{st.session_state.persona}] 생수는 아직 넉넉해 보여!"
    elif any(word in user_input for word in ["배워", "가르쳐", "기억해"]):
        return f"[{st.session_state.persona}] 응! 언제든 가르쳐주면 바로 배울게."
    else:
        # 엉뚱한 대답 방지: 모를 때는 솔직하게 물어보기
        return f"[{st.session_state.persona}] 음, '{user_input}'은(는) 처음 들어봐. 조금 더 쉽게 말해줄래?"

# --- UI 레이아웃 ---
st.set_page_config(page_title="재알메", layout="centered")
st.title(f"🏠 재알메 v4.0 ({st.session_state.persona})")

# [보완] 3. 스피커 잠금 해제형 음성 인식 브릿지
st.components.v1.html(
    """
    <script>
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ko-KR';
    
    function updateBtn(text, color) {
        const btn = document.getElementById('micBtn');
        if (btn) {
            btn.innerText = text;
            btn.style.background = color;
        }
    }

    function speak(text) {
        if (!text) return;
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'ko-KR';
        window.speechSynthesis.speak(msg);
    }

    // 마이크 시작 시 '무음'을 먼저 재생하여 브라우저 스피커 권한을 미리 획득합니다.
    function startWithSound() {
        const dummy = new SpeechSynthesisUtterance(""); 
        window.speechSynthesis.speak(dummy);
        recognition.start();
    }

    recognition.onstart = () => updateBtn('🎤 주인의 말씀을 듣는 중...', '#28a745');
    recognition.onspeechend = () => updateBtn('🧠 생각 중...', '#ffc107');
    
    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        updateBtn('✅ 인식 완료: ' + text, '#007bff');
        
        const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (textArea) {
            const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            setter.call(textArea, text);
            textArea.dispatchEvent(new Event('input', { bubbles: true }));
            
            setTimeout(() => {
                const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                if (sendBtn) sendBtn.click();
            }, 500);
        }
    };

    recognition.onerror = () => updateBtn('❌ 다시 눌러주세요', '#dc3545');

    window.addEventListener('message', (e) => {
        if (e.data.type === 'tts') speak(e.data.text);
    });
    </script>
    <button id="micBtn" onclick="startWithSound()" style="width:100%; height:80px; border-radius:20px; background: #FF4B4B; color:white; border:none; font-size:20px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        🎤 눌러서 재알메에게 말하기
    </button>
    """,
    height=110,
)

# [유지] 4. 대화창 처리
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("재알메에게 직접 가르치기"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if len(st.session_state.messages) > 1 and "몰라서 그랬어" in st.session_state.messages[-2]["content"]:
        st.session_state.learning_note.append({"wrong": "이전내용", "correct": prompt})
        response = f"[{st.session_state.persona}] 응! 확실히 배웠어. '{prompt}'라고 기억할게!"
    else:
        response = generate_response(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    clean_response = response.replace('[', '').replace(']', '')
    st.components.v1.html(f"<script>window.parent.postMessage({{type: 'tts', text: '{clean_response}'}}, '*');</script>", height=0)
    st.rerun()
