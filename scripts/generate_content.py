import os
from datetime import datetime
import google.generativeai as genai

# APIキーを環境変数から取得
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 修正: 指定可能なモデル名に変更
model = genai.GenerativeModel('models/gemini-3.1-flash-lite')

def generate_content():
    today = datetime.now().strftime('%Y-%m-%d')
    
    # プロンプトの構築
    prompt = f"""
    あなたは小説家、編集者、そして熱心な読者の3役を演じます。
    今日の執筆テーマ：「AIとの共生」。
    
    以下のフォーマットで出力してください。
    ---
    ## {today} の執筆内容
    (小説の続きを執筆)
    
    ## 編集者の指摘
    (執筆内容に対する鋭い指摘)
    
    ## 読者の感想
    (執筆内容に対する熱い感想)
    """
    
    response = model.generate_content(prompt)
    
    # コンテンツの保存
    os.makedirs('daily-report', exist_ok=True)
    filename = f'daily-report/{today}.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Generated: {filename}")

if __name__ == "__main__":
    generate_content()
