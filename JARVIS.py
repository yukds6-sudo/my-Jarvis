import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io

st.set_page_config(page_title="자비스", page_icon="🎙️")
st.title("🎙️ AI 비서 자비스")
st.caption("마이크 버튼을 누르고 말하거나, 아래에 글자로 질문해 보세요!")

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

audio_value = st.audio_input("🎤 마이크를 누르고 말하세요")
text_prompt = st.chat_input("또는 글자로 입력하세요...")

user_input = audio_value if audio_value else text_prompt

if user_input:
    with st.spinner("자비스가 생각 중입니다..."):
        try:
            if audio_value:
                contents = [
                    types.Part.from_bytes(data=audio_value.read(), mime_type="audio/wav"),
                    "사용자의 말을 듣고 친절하게 대답해줘."
                ]
            else:
                contents = text_prompt

            # 구글이 공식 안내한 최신 모델 사용
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="너는 주인님을 돕는 똑똑한 AI 자비스야. 특수문자(*, # 등) 없이 자연스러운 말투로 대답해줘."
                )
            )

            st.write(response.text)
            tts = gTTS(text=response.text, lang='ko')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format="audio/mp3", autoplay=True)

        except Exception as e:
            st.error(f"잠시 문제가 생겼어요! (상세 이유: {e})")
