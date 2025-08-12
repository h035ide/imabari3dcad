#!/usr/bin/env python3
"""
Langflow setup and execution script
依存関係の競合を避けるため、langflowを別の環境で実行するためのスクリプト
"""

import subprocess
import sys
import os
from pathlib import Path

def create_langflow_env():
    """langflow用の仮想環境を作成"""
    print("Langflow用の仮想環境を作成中...")
    
    # 仮想環境のパス
    langflow_env_path = Path("langflow_env")
    
    if not langflow_env_path.exists():
        # 仮想環境を作成
        subprocess.run([sys.executable, "-m", "venv", str(langflow_env_path)], check=True)
        print(f"仮想環境を作成しました: {langflow_env_path}")
    
    return langflow_env_path

def install_langflow(env_path):
    """langflowをインストール"""
    print("Langflowをインストール中...")
    
    # 仮想環境のPythonパス
    if os.name == 'nt':  # Windows
        python_path = env_path / "Scripts" / "python.exe"
        pip_path = env_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux
        python_path = env_path / "bin" / "python"
        pip_path = env_path / "bin" / "pip"
    
    # pipをアップグレード（エラーハンドリング付き）
    try:
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError:
        print("pipのアップグレードに失敗しましたが、続行します...")
    
    # langflowをインストール
    try:
        subprocess.run([str(pip_path), "install", "langflow"], check=True)
        print("Langflowのインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"Langflowのインストールに失敗しました: {e}")
        print("代替方法を試します...")
        # 代替方法：python -m pipを使用
        subprocess.run([str(python_path), "-m", "pip", "install", "langflow"], check=True)
        print("Langflowのインストールが完了しました（代替方法）")
    
    return python_path

def run_langflow(python_path, host="0.0.0.0", port="7860"):
    """langflowを実行"""
    print(f"Langflowを起動中... (http://{host}:{port})")
    
    try:
        subprocess.run([
            str(python_path), "-m", "langflow", "run",
            "--host", host,
            "--port", port
        ], check=True)
    except KeyboardInterrupt:
        print("\nLangflowを停止しました")
    except subprocess.CalledProcessError as e:
        print(f"Langflowの起動に失敗しました: {e}")

def main():
    """メイン関数"""
    print("=== Langflow Setup and Execution ===")
    
    # 環境変数の確認
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: OPENAI_API_KEYが設定されていません")
        print("環境変数を設定してください:")
        print("export OPENAI_API_KEY='your-api-key'")
        print("または、Windowsの場合:")
        print("set OPENAI_API_KEY=your-api-key")
    
    # 仮想環境を作成
    env_path = create_langflow_env()
    
    # langflowをインストール
    python_path = install_langflow(env_path)
    
    # langflowを実行
    run_langflow(python_path)

if __name__ == "__main__":
    main()
