import os
import yaml
from datetime import datetime
import google.generativeai as genai

# APIキーを環境変数から取得
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# モデル指定
model = genai.GenerativeModel('models/gemini-3.1-flash-lite')

def get_progress():
    with open('docs/PROGRESS.md', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['current_chapter']

def update_progress(chapter):
    with open('docs/PROGRESS.md', 'w', encoding='utf-8') as f:
        yaml.dump({'current_chapter': chapter + 1}, f)

def get_plot():
    with open('docs/PLOT.md', 'r', encoding='utf-8') as f:
        return f.read()

def generate_chapter():
    chapter = get_progress()
    plot = get_plot()
    
    # プロンプトの構築
    prompt = f"""
    あなたは小説家です。以下の全体プロットに基づき、第{chapter}章を執筆してください。
    
    ## 全体プロット
    {plot}
    
    ## 今日の執筆指示 (第{chapter}章)
    - 雰囲気: ライト、ポップ、明るいコメディ。
    - ジャンル: 現代または未来を舞台にした、隣人との庭いじりバトル。
    - 注意点: AIという言葉や概念には一切言及しないでください。
    - 文字数: 800文字程度。
    - キャラクター: 主人公・佐藤と隣人の鈴木。
    
    ## 出力フォーマット
    ---
    ## 第{chapter}章: (タイトル)
    (執筆内容)
    
    ## 編集者の指摘
    (テンポやコメディ要素に関する鋭い指摘)
    
    ## 読者の感想
    (読みやすさや笑いのツボに関する感想)
    """
    
    response = model.generate_content(prompt)
    
    # コンテンツの保存
    os.makedirs('daily-report', exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f'daily-report/{today}_chapter_{chapter}.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Generated: {filename}")
    update_progress(chapter)

if __name__ == "__main__":
    generate_chapter()
