import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import time

st.set_page_config(page_title="자비스", page_icon="🎙️")
st.title("🎙️ AI 비서 자비스")
st.caption("마이크 버튼을 누르고 말하거나, 아래에 글자로 질문해 보세요!")

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

audio_value = st.audio_input("🎤 마이크를 누르고 말하세요")
text_prompt = st.chat_input("또는 글자로 입력하세요...")

user_input = audio_value if audio_value else text_prompt

if user_input:
    with st.spinner("자비스가 대답을 준비 중입니다..."):
        if audio_value:
            contents = [
                types.Part.from_bytes(data=audio_value.read(), mime_type="audio/wav"),
                "사용자의 말을 듣고 친절하고 짧게 대답해줘."
            ]
        else:
            contents = text_prompt

        # 내 API 키로 쓸 수 있는 모든 Flash 모델 목록 자동 조회
        available_models = ["gemini-3.8-flash"]
        try:
            for m in client.models.list():
                name = m.name.replace("models/", "")
                if "flash" in name and name not in available_models:
                    available_models.append(name)
        except Exception:
            pass

        reply_text = None
        last_error = None

        # 503 혼잡 시 최대 3번 재시도하며 한가한 모델로 자동 연결
        for model_name in available_models[:4]:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction="너는 주인님을 돕는 똑똑한 AI 비서 자비스야. 특수문자(*, # 등) 없이 3문장 이내로 빠르고 자연스럽게 대답해줘."
                        )
                    )
                    reply_text = response.text
                    break
                except Exception as e:
                    last_error = e
                    if "503" in str(e):
                        time.sleep(2) # 2초 기다렸다 재시도
                        continue
                    else:
                        break # 404 등 다른 에러면 다음 모델로 바로 이동
            if reply_text:
                break

        if reply_text:
            st.write(reply_text)
            tts = gTTS(text=reply_text, lang='ko')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format="audio/mp3", autoplay=True)
        else:
            st.error(f"구글 서버가 매우 혼잡합니다. 10초 뒤 다시 시도해 주세요! (상세: {last_error})")
