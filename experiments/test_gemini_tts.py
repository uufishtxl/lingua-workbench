import os
from dotenv import load_dotenv

# 加载环境变量（假设你的项目根目录有 .env 文件）
# 如果没有，请取消下方注释并填入你的 API KEY
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', '.env')
load_dotenv(env_path)
# os.environ["GEMINI_API_KEY"] = "你的_API_KEY"

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ 请先安装官方 SDK: pip install google-genai")
    exit(1)

def test_gemini_audio():
    # 自动读取环境变量中的 GEMINI_API_KEY
    client = genai.Client()

    print("🚀 开始调用 Gemini 2.5 Flash 生成文本和语音...")
    
    # 我们模拟一次对话，要求它返回文字和声音
    prompt = "You are a senior dev in Silicon Valley. Greet me warmly and ask if I have set up my dev environment. Keep it short."
    
    try:
        # 1. 先用标准的 Gemini 2.5 Flash 生成文本
        print("🤖 [步骤 1] 思考中...")
        text_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        reply_text = text_response.text
        print("\n--- 📝 文本回复 ---")
        print(reply_text)
        
        # 2. 调用专门的 TTS 模型生成语音
        print("\n🗣️ [步骤 2] 正在将文字转为语音...")
        tts_response = client.models.generate_content(
            model='gemini-2.5-flash-preview-tts',
            contents=reply_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Puck"
                        )
                    )
                )
            )
        )
        
        # 3. 保存音频
        has_audio = False
        import wave
        for i, part in enumerate(tts_response.candidates[0].content.parts):
            if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                audio_data = part.inline_data.data
                output_file = os.path.join(os.path.dirname(__file__), "gemini_voice.wav")
                
                # Gemini TTS 默认返回 24kHz, 16bit, 单声道 PCM 数据
                # 我们需要加上 WAV (RIFF) 文件头才能在普通播放器中播放
                with wave.open(output_file, "wb") as wav_file:
                    wav_file.setnchannels(1)       # 单声道: 1 channel
                    wav_file.setsampwidth(2)       # 16-bit: 2 bytes
                    wav_file.setframerate(24000)   # 24kHz 采样率
                    wav_file.writeframes(audio_data)
                    
                print(f"✅ 成功生成并提取音频！")
                print(f"💾 保存路径: {output_file}")
                has_audio = True
                
        if not has_audio:
            print("⚠️ 未能在 TTS 响应中找到音频数据。")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    test_gemini_audio()
