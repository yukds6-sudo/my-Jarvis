import streamlit as st
from openai import OpenAI
from gtts import gTTS
import speech_recognition as sr
import io

st.set_page_config(page_title="자비스", page_icon="🎙️")
st.title("🎙️ AI 비서 자비스")

# 글자를 한국어 음성(MP3)으로 바꿔주는 함수
def speak(text, auto=True):
    tts = gTTS(text=text, lang='ko')
    sound_fp = io.BytesIO()
    tts.write_to_fp(sound_fp)
    sound_fp.seek(0)
    st.audio(sound_fp, format="audio/mp3", autoplay=auto)

# 1. 첫 인사 멘트 화면 표시 및 목소리 출력
welcome_msg = "안녕하세요 저는 AI 자비스입니다."
st.info(welcome_msg)

if "welcomed" not in st.session_state:
    speak(welcome_msg, auto=True)
    st.session_state.welcomed = True

# 2. 엔비디아 API 연결
API_KEY = st.secrets["NVIDIA_API_KEY"]
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# 3. 마이크 음성 입력 & 글자 입력
audio_value = st.audio_input("🎤 마이크를 누르고 말하세요")
text_prompt = st.chat_input("또는 글자로 입력하세요...")

user_text = None

if audio_value:
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_value) as source:
            audio_data = recognizer.record(source)
            user_text = recognizer.recognize_google(audio_data, language="ko-KR")
            st.success(f"🗣️ 내가 한 말: {user_text}")
    except Exception:
        st.warning("목소리를 잘 듣지 못했어요. 마이크 가까이에서 다시 한 번 말씀해 주세요!")
elif text_prompt:
    user_text = text_prompt

# 4. 엔비디아 최신 AI 모델 자동 탐색 후 대답하기
if user_text:
    with st.spinner("자비스가 생각 중입니다..."):
        # 엔비디아 서버에서 현재 활성화된 무료 대화형 모델 목록 자동 조회
        candidate_models = [
            "meta/llama-4-scout-17b-16e-instruct",
            "meta/llama-4-maverick-17b-128e-instruct",
            "qwen/qwen3-235b-a22b",
            "google/gemma-3-27b-it",
            "mistralai/mistral-large-3-675b-instruct-2512"
        ]
        try:
            live_models = [
                m.id for m in client.models.list().data
                if any(k in m.id.lower() for k in ["instruct", "llama", "qwen", "gemma", "deepseek"])
                and "embed" not in m.id.lower()
                and "guard" not in m.id.lower()
                and "vision" not in m.id.lower()
            ]
            for m_id in live_models:
                if m_id not in candidate_models:
                    candidate_models.append(m_id)
        except Exception:
            pass

        reply_text = None
        last_error = None

        for model_name in candidate_models[:8]:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "너는 주인님을 돕는 AI 비서 자비스야. 항상 첫 인사나 자기소개가 필요할 때는 '안녕하세요 저는 AI 자비스입니다.'라고 말하고, 특수문자(*, # 등) 없이 자연스럽고 친절한 한국어 말투로 대답해줘."
                        },
                        {
                            "role": "user",
                            "content": user_text
                        }
                    ],
                    temperature=0.5,
                    max_tokens=1024
                )
                reply_text = completion.choices[0].message.content
                if reply_text:
                    break
            except Exception as e:
                last_error = e
                continue

        if reply_text:
            st.write(reply_text)
            speak(reply_text, auto=True)
        else:
            st.error(f"오류가 발생했어요! (상세 이유: {last_error})")
