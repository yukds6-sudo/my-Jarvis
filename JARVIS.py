import streamlit as st
from openai import OpenAI
from gtts import gTTS
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

# 3. 질문 입력 및 자비스 대답 + 목소리 출력
text_prompt = st.chat_input("자비스에게 글자로 질문해 보세요...")

if text_prompt:
    with st.spinner("자비스가 생각 중입니다..."):
        try:
            completion = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                messages=[
                    {
                        "role": "system",
                        "content": "너는 주인님을 돕는 AI 비서 자비스야. 항상 첫 인사나 자기소개가 필요할 때는 '안녕하세요 저는 AI 자비스입니다.'라고 말하고, 특수문자(*, # 등) 없이 자연스럽고 친절한 한국어 말투로 대답해줘."
                    },
                    {
                        "role": "user",
                        "content": text_prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1024
            )

            reply_text = completion.choices[0].message.content
            st.write(reply_text)
            
            # 자비스의 대답을 목소리로 읽어주기
            speak(reply_text, auto=True)

        except Exception as e:
            st.error(f"오류가 발생했어요! (상세 이유: {e})")
