import pytest
from unittest.mock import patch, mock_open
from scripts.generate_content import get_progress

def test_get_progress_success():
    """正常に章番号を取得できるかテスト"""
    mock_md_content = """
    # 進捗
    - **執筆中**: 第3章「タイトル」
    """
    with patch("builtins.open", mock_open(read_data=mock_md_content)):
        assert get_progress() == 3

def test_get_progress_default():
    """ファイルの内容が不明な場合にデフォルトの1を返すかテスト"""
    mock_md_content = "# 進捗\n何もない"
    with patch("builtins.open", mock_open(read_data=mock_md_content)):
        assert get_progress() == 1
