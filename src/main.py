from flask import Flask, request
import whisper, telegram, subprocess, os
from openai import OpenAI
from dotenv import load_dotenv
import yt_dlp

# 환경변수 불러오기
load_dotenv()

app = Flask(__name__)

model = whisper.load_model("tiny")
bot = telegram.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
chat_id = os.environ["TELEGRAM_CHAT_ID"]

# 최신 OpenAI 클라이언트 생성
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def get_video_info(url):
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "webpage_url": info.get("webpage_url")
        }

@app.route("/")
def home():
    return "✅ Whisper-GPT-Telegram bot is running!"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    url = request.json.get("url")

    # ✅ 영상 정보 추출
    video_info = get_video_info(url)
    title = video_info["title"]
    link = video_info["webpage_url"]

    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "mp3",   "--force-overwrites", "-o", "audio.%(ext)s", url
    ])

    result = model.transcribe("audio.mp3", language="ko")
    text = result["text"]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "다음은 Whisper로 전사된 한국어입니다. 오류를 수정하고 핵심을 요약해 주세요."},
            {"role": "user", "content": text}
        ]
    )

    summary = response.choices[0].message.content    
    
    # ✅ 텔레그램 메시지 포맷
    message = f"📺 <b>{title}</b>\n🔗 {link}\n\n📝 <b>요약:</b>\n{summary}"
    bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

    return {"summary": summary}
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
