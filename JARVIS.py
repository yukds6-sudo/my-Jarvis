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

# 1. 첫 인사 멘트 (앱 처음 켰을 때 딱 한 번만 출력)
welcome_msg = "안녕하세요 저는 AI 자비스입니다."
st.info(welcome_msg)

if "welcomed" not in st.session_state:
    speak(welcome_msg, auto=True)
    st.session_state.welcomed = True

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# 2. 초고속 Groq 무료 API 연결
API_KEY = st.secrets["GROQ_API_KEY"]
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)

# 3. 마이크 음성 입력 & 글자 입력
audio_value = st.audio_input("🎤 마이크를 누르고 말하세요")
text_prompt = st.chat_input("또는 글자로 입력하세요...")

user_text = None

# 새로운 글자 입력이 들어왔을 때 최우선 처리
if text_prompt:
    user_text = text_prompt
# 새로운 마이크 녹음이 들어왔을 때만 음성 인식 실행 (예전 녹음 중복 방지)
elif audio_value is not None and audio_value.file_id != st.session_state.last_audio_id:
    st.session_state.last_audio_id = audio_value.file_id
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_value) as source:
            audio_data = recognizer.record(source)
            user_text = recognizer.recognize_google(audio_data, language="ko-KR")
            st.success(f"🗣️ 내가 한 말: {user_text}")
    except Exception:
        st.warning("목소리를 잘 듣지 못했어요. 마이크 가까이에서 다시 한 번 말씀해 주세요!")

# 4. 질문에 맞춰 정확히 대답하기
if user_text:
    with st.spinner("자비스가 생각 중입니다..."):
        try:
            # Groq에서 가장 한국어를 잘하는 고성능 대화 모델 우선 선택
            all_models = [m.id for m in client.models.list().data]
            preferred = [
                "meta-llama/llama-4-maverick-17b-128e-instruct",
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "llama-3.3-70b-versatile",
                "qwen/qwen3-32b",
                "llama-3.1-8b-instant"
            ]
            active_model = next((m for m in preferred if m in all_models), all_models[0])

            completion = client.chat.completions.create(
                model=active_model,
                messages=[
                    {
                        "role": "system",
                        "content": "너는 주인님의 질문에 정확하고 친절하게 대답하는 유능한 한국어 AI 비서 자비스야. 자기소개는 반복하지 말고 주인님이 물어본 질문의 핵심 답만 특수문자(*, # 등) 없이 3문장 이내로 자연스럽게 말해줘."
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
                temperature=0.7,
                max_tokens=512
            )

            reply_text = completion.choices[0].message.content
            st.write(reply_text)
            speak(reply_text, auto=True)

        except Exception as e:
            st.error(f"오류가 발생했어요! (상세 이유: {e})")
