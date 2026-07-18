import os
import re
import logging
from datetime import datetime
from google import genai
from google.genai import types

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("novel.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# APIキーを環境変数から取得
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# モデル指定
MODEL_ID = 'gemini-3.1-flash-lite' # 指定されたモデルを使用

def get_progress():
    with open('docs/PROGRESS.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # "- **執筆中**: 第2章「庭いじりの夜明け」" のような行から数字を取得
    # Asterisks need to be escaped as they are special regex characters
    match = re.search(r'執筆中\*\*: 第(\d+)章', content)
    if match:
        return int(match.group(1))
    return 1 # デフォルト

def update_progress(chapter):
    with open('docs/PROGRESS.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 執筆中の章番号を更新
    new_content = re.sub(r'(執筆中\*\*: 第)\d+(章)', rf'\g<1>{chapter + 1}\g<2>', content)
    
    # 2. 全体進捗のパーセンテージを更新 (現在の章 * 10)
    new_percentage = chapter * 10
    new_content = re.sub(r'(\*\*)\d+(%)\*\* 完了', rf'\g<1>{new_percentage}\g<2>** 完了', new_content)
    
    # 3. 完了したマイルストーンにチェックを入れる
    if f'- [x] 第{chapter}章' not in new_content:
        new_content = re.sub(r'## 完了したマイルストーン', rf'## 完了したマイルストーン\n- [x] 第{chapter}章 執筆・校閲・統合完了', new_content)
    
    # 4. GitHub統計を更新
    # 実際にはGitHub Actions側で取得した値を環境変数などで渡すのが望ましいが、
    # ここではコマンドを実行して取得する
    import subprocess
    
    # 既存の統計情報を正規表現でパースしておく（フォールバック用）
    open_pr_match = re.search(r'- PR数　オープン (\d+)', content)
    closed_pr_match = re.search(r'- PR数　オープン \d+ / クローズ (\d+)', content)
    open_issue_match = re.search(r'- Issue数　オープン (\d+)', content)
    closed_issue_match = re.search(r'- Issue数　オープン \d+ / クローズ (\d+)', content)
    
    fallback_open_pr = open_pr_match.group(1) if open_pr_match else "0"
    fallback_closed_pr = closed_pr_match.group(1) if closed_pr_match else "0"
    fallback_open_issue = open_issue_match.group(1) if open_issue_match else "0"
    fallback_closed_issue = closed_issue_match.group(1) if closed_issue_match else "0"
    
    def get_stat(cmd, fallback_val):
        try:
            return subprocess.check_output(cmd, shell=True).decode().strip()
        except Exception as e:
            logger.warning(f"Failed to execute command '{cmd}'. Using fallback: {fallback_val}. Error: {e}")
            return fallback_val
        
    open_pr = get_stat("gh pr list --state open --json number --jq 'length'", fallback_open_pr)
    closed_pr = get_stat("gh pr list --state closed --json number --jq 'length'", fallback_closed_pr)
    open_issue = get_stat("gh issue list --state open --json number --jq 'length'", fallback_open_issue)
    closed_issue = get_stat("gh issue list --state closed --json number --jq 'length'", fallback_closed_issue)
    
    stats_text = f"## GitHub 統計\n- PR数　オープン {open_pr} / クローズ {closed_pr}\n- Issue数　オープン {open_issue} / クローズ {closed_issue}"
    new_content = re.sub(r'## GitHub 統計.*', stats_text, new_content, flags=re.DOTALL)
    
    with open('docs/PROGRESS.md', 'w', encoding='utf-8') as f:
        f.write(new_content)

def get_plot():
    with open('docs/PLOT.md', 'r', encoding='utf-8') as f:
        return f.read()

def generate_chapter():
    chapter = get_progress()
    plot = get_plot()
    
    # フィードバックの読み込み
    feedback = ""
    if os.path.exists('feedback.txt'):
        with open('feedback.txt', 'r', encoding='utf-8') as f:
            feedback = f.read()
    
    # プロンプトの構築
    prompt = f"""
    あなたは小説家です。以下の全体プロットに基づき、第{chapter}章を執筆してください。
    
    ## 全体プロット
    {plot}
    
    ## 前回のPRでのフィードバック
    {feedback if feedback else "特になし"}
    
    ## 今日の執筆指示 (第{chapter}章)
    - 上記のフィードバックがある場合は、それを反映させて執筆してください。
    - 雰囲気: ライト、ポップ、明るいコメディ。
    - ジャンル: 現代または未来を舞台にした、隣人との庭いじりバトル。
    - 注意点: AIという言葉や概念には一切言及しないでください。
    - 文字数: 800文字程度。
    - キャラクター: 主人公・佐藤と隣人の鈴木。
    
    ## 出力フォーマット
    ---
    # 第{chapter}章：(タイトル)
    (執筆内容)
    
    ## 編集者の指摘
    (テンポやコメディ要素に関する鋭い指摘)
    
    ## 読者の感想
    (読みやすさや笑いのツボに関する感想)
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
    )
    
    # コンテンツの保存（デイリーレポート：すべて含む）
    os.makedirs('daily-report', exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    daily_filename = f'daily-report/{today}_chapter_{chapter}.md'
    with open(daily_filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    logger.info(f"Generated: {daily_filename}")
    
    # コンテンツの保存（章ファイルへ自動統合：本文のみ）
    os.makedirs('docs/novel', exist_ok=True)
    chapter_filename = f'docs/novel/chapter{chapter}.md'
    
    # 改善された抽出ロジック
    # 1. まず --- で区切られているか確認
    parts = response.text.split('---')
    if len(parts) >= 2:
        # 最初の --- の次が本文である可能性が高い
        body_content = parts[1].strip()
    else:
        # 2. 従来通り ## 編集者の指摘 で分割
        body_match = re.split(r'\n\n## 編集者の指摘', response.text, flags=re.DOTALL)
        body_content = body_match[0].strip()
        
    with open(chapter_filename, 'w', encoding='utf-8') as f:
        f.write(body_content)
    
    logger.info(f"Updated: {chapter_filename}")
    
    # 小説一覧に自動追加
    readme_path = 'docs/novel/README.md'
    # タイトルを抽出
    title_match = re.search(r'# 第\d+章：(.+)', response.text)
    title = title_match.group(1) if title_match else f"第{chapter}章"
    
    with open(readme_path, 'a', encoding='utf-8') as f:
        f.write(f"\n- [第{chapter}章：{title}](chapter{chapter}.md)")
    
    logger.info(f"Added to {readme_path}")
    
    update_progress(chapter)
    
    # 処理完了後にフィードバックファイルを削除
    if os.path.exists('feedback.txt'):
        os.remove('feedback.txt')
        logger.info("Deleted feedback.txt for security.")

if __name__ == "__main__":
    generate_chapter()
