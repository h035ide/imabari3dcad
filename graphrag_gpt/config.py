"""
接続情報と API キーを一元管理するだけのシンプルなモジュール
"""
import os
from dotenv import load_dotenv

load_dotenv()  # .env を読み込む

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER     = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
