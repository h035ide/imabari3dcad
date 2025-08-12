#!/usr/bin/env python3
"""
Simple Langflow execution script
より簡単で直接的なlangflow実行方法
"""

import subprocess
import sys
import os

def check_requirements():
    """必要な依存関係をチェック"""
    print("依存関係をチェック中...")
    
    try:
        import langflow
        print("✓ langflowは既にインストールされています")
        return True
    except ImportError:
        print("✗ langflowがインストールされていません")
        return False

def install_langflow():
    """langflowをインストール"""
    print("langflowをインストール中...")
    
    try:
        # まずpipで試行
        subprocess.run([sys.executable, "-m", "pip", "install", "langflow"], check=True)
        print("✓ langflowのインストールが完了しました")
        return True
    except subprocess.CalledProcessError:
        print("✗ pipでのインストールに失敗しました")
        
        try:
            # uvで試行
            subprocess.run(["uv", "add", "langflow"], check=True)
            print("✓ uvでのlangflowインストールが完了しました")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ uvでのインストールにも失敗しました")
            return False

def run_langflow():
    """langflowを実行"""
    print("langflowを起動中...")
    print("ブラウザで http://localhost:7860 にアクセスしてください")
    
    try:
        subprocess.run([sys.executable, "-m", "langflow", "run"], check=True)
    except KeyboardInterrupt:
        print("\nlangflowを停止しました")
    except subprocess.CalledProcessError as e:
        print(f"langflowの起動に失敗しました: {e}")

def main():
    """メイン関数"""
    print("=== Simple Langflow Runner ===")
    
    # 環境変数の確認
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: OPENAI_API_KEYが設定されていません")
        print("以下のコマンドで設定してください:")
        if os.name == 'nt':  # Windows
            print("set OPENAI_API_KEY=your-api-key")
        else:  # Unix/Linux
            print("export OPENAI_API_KEY=your-api-key")
        print()
    
    # 依存関係をチェック
    if not check_requirements():
        # langflowをインストール
        if not install_langflow():
            print("langflowのインストールに失敗しました")
            print("手動でインストールしてください:")
            print("pip install langflow")
            return
    
    # langflowを実行
    run_langflow()

if __name__ == "__main__":
    main()
