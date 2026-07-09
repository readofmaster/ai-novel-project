import os
import google.generativeai as genai

# APIキーを環境変数から取得
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 利用可能なモデルをリストアップして表示する
print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model name: {m.name}")
