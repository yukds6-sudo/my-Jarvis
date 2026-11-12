import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io

st.set_page_config(page_title="자비스", page_icon="🎙️")
st.title("🎙️ AI 비서 자비스")
st.caption("말로 하거나 글자로 입력해 보세요! 최신 정보 검색도 가능합니다.")

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 1순위부터 3순위까지 사용할 AI 두뇌 목록 (붐빌 때 자동으로 다음 두뇌 사용)
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.8-flash-lite",
    "gemini-3.5-flash"
]

audio_value = st.audio_input("🎤 마이크를 누르고 말하세요")
text_prompt = st.chat_input("또는 글자로 입력하세요...")

user_input = audio_value if audio_value else text_prompt

if user_input:
    with st.spinner("자비스가 정보를 찾고 생각 중입니다..."):
        if audio_value:
            contents = [
                types.Part.from_bytes(data=audio_value.read(), mime_type="audio/wav"),
                "사용자의 말을 듣고 친절하게 대답해줘."
            ]
        else:
            contents = text_prompt

        reply_text = None
        last_error = None

        # 1순위 모델이 붐비면(503 등) 자동으로 다음 예비 모델로 시도하기
        for model_name in MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction="너는 초등학생 주인님을 돕는 AI 비서 자비스야. 특수문자(*, # 등) 없이 자연스러운 말투로 대답해줘.",
                        tools=[{"google_search": {}}] # 실시간 구글 검색 기능!
                    )
                )
                reply_text = response.text
                break # 성공하면 반복 멈추기!
            except Exception as e:
                last_error = e
                continue # 실패하면 다음 예비 모델로 바로 넘어가기

        # 대답 생성에 성공했을 때
        if reply_text:
            st.write(reply_text)
            tts = gTTS(text=reply_text, lang='ko')
            sound_fp = io.BytesIO()
            tts.write_to_fp(sound_fp)
            st.audio(sound_fp, format="audio/mp3", autoplay=True)
        else:
            st.error(f"모든 서버가 잠시 붐비고 있어요! 1분 뒤에 다시 시도해 주세요. (상세 이유: {last_error})")
