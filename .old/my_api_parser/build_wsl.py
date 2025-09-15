#!/usr/bin/env python3
# build_wsl.py
"""
WSL環境でtree-sitterの共有ライブラリをビルドするスクリプト
"""

import os
import subprocess
import sys
import shutil
import platform

def run_command(command, cwd=None):
    """コマンドを実行し、結果を返す"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"エラー: {e.stderr}")
        return None

def check_environment():
    """実行環境をチェック"""
    system = platform.system()
    print(f"実行環境: {system}")
    
    if system == "Linux":
        print("✅ Linux環境で実行中（WSLまたはLinux）")
        return "linux"
    elif system == "Windows":
        print("✅ Windows環境で実行中")
        return "windows"
    else:
        print(f"❌ 未対応の環境: {system}")
        return None

def build_in_linux():
    """Linux環境でtree-sitterの共有ライブラリをビルド"""
    print("🚀 Linux環境でtree-sitterの共有ライブラリをビルドします...")
    
    # Linuxで実行するコマンド
    commands = [
        # 必要なパッケージをインストール
        "sudo apt update -y",
        "sudo apt install -y build-essential gcc g++ nodejs npm python3-pip",
        
        # tree-sitter CLIをローカルインストール
        "npm install tree-sitter-cli",
        
        # tree-sitterでパーサーを生成
        "npx tree-sitter generate",
        
        # Python tree-sitterをインストール
        "pip3 install tree-sitter",
        
        # 共有ライブラリをビルド
        "mkdir -p build",
        "python3 -c \"from tree_sitter import Language; Language.build_library('build/my-languages.so', ['.'])\"",
        
        # ビルド結果を確認
        "ls -la build/",
        "echo 'ビルド完了！'"
    ]
    
    # 各コマンドを実行
    for cmd in commands:
        result = run_command(cmd)
        if result is None:
            print(f"❌ コマンドが失敗しました: {cmd}")
            return False
    
    print("✅ Linuxでのビルドが完了しました！")
    return True

def build_in_windows():
    """Windows環境でWSLを使ってビルド"""
    print("🚀 Windows環境でWSLを使ってビルドします...")
    
    # 現在のディレクトリのパスを取得
    current_dir = os.path.abspath('.')
    wsl_path = current_dir.replace('C:', '/mnt/c').replace('\\', '/')
    
    # WSLで実行するコマンド
    wsl_commands = [
        # 必要なパッケージをインストール
        "sudo apt update -y",
        "sudo apt install -y build-essential gcc g++ nodejs npm python3-pip",
        
        # プロジェクトディレクトリに移動
        f"cd {wsl_path}",
        
        # tree-sitter CLIをローカルインストール
        "npm install tree-sitter-cli",
        
        # tree-sitterでパーサーを生成
        "npx tree-sitter generate",
        
        # Python tree-sitterをインストール
        "pip3 install tree-sitter",
        
        # 共有ライブラリをビルド
        "mkdir -p build",
        "python3 -c \"from tree_sitter import Language; Language.build_library('build/my-languages.so', ['.'])\"",
        
        # ビルド結果を確認
        "ls -la build/",
        "echo 'ビルド完了！'"
    ]
    
    # 各コマンドを実行
    for cmd in wsl_commands:
        wsl_cmd = f"wsl {cmd}"
        result = run_command(wsl_cmd)
        if result is None:
            print(f"❌ コマンドが失敗しました: {cmd}")
            return False
    
    print("✅ WSLでのビルドが完了しました！")
    return True

def copy_to_windows():
    """WSLでビルドしたファイルをWindowsにコピー"""
    print("📁 ビルドしたファイルをWindowsにコピーします...")
    
    # WSLのビルドディレクトリからWindowsにコピー
    copy_commands = [
        "wsl cp build/my-languages.so /mnt/c/Users/user/workfolders/imabari3dcad/my_api_parser/build/",
        "wsl ls -la /mnt/c/Users/user/workfolders/imabari3dcad/my_api_parser/build/"
    ]
    
    for cmd in copy_commands:
        result = run_command(cmd)
        if result is None:
            print(f"❌ コピーが失敗しました: {cmd}")
            return False
    
    print("✅ ファイルのコピーが完了しました！")
    return True

def test_language():
    """ビルドしたLanguageオブジェクトをテスト"""
    print("🧪 ビルドしたLanguageオブジェクトをテストします...")
    
    test_script = '''
import os
from tree_sitter import Language, Parser

# ビルドした共有ライブラリを読み込み
try:
    language = Language('build/my-languages.so', 'api_doc')
    print("✅ Languageオブジェクトの作成に成功しました！")
    
    # パーサーを作成してテスト
    parser = Parser()
    parser.set_language(language)
    
    # テスト用のコード
    test_code = """
/**
 * @function calculateSum
 * @param {number} a - 最初の数値
 * @param {number} b - 2番目の数値
 * @returns {number} 合計値
 */
function calculateSum(a, b) {
    return a + b;
}
"""
    
    # パースを実行
    tree = parser.parse(test_code.encode('utf-8'))
    
    if tree:
        print("✅ パースが成功しました！")
        print(f"ルートノード: {tree.root_node.type}")
    else:
        print("❌ パースに失敗しました")
        
except Exception as e:
    print(f"❌ エラー: {e}")
'''
    
    # テストスクリプトを実行
    result = run_command(f'python -c "{test_script}"')
    return result is not None

def main():
    """メイン関数"""
    print("🔧 tree-sitter ビルドスクリプト")
    print("=" * 50)
    
    # 実行環境をチェック
    env = check_environment()
    if env is None:
        return False
    
    # 環境に応じてビルド
    if env == "linux":
        if not build_in_linux():
            print("❌ Linuxでのビルドに失敗しました")
            return False
    elif env == "windows":
        if not build_in_windows():
            print("❌ WSLでのビルドに失敗しました")
            return False
        
        # Windowsの場合はファイルをコピー
        if not copy_to_windows():
            print("❌ ファイルのコピーに失敗しました")
            return False
    
    # テスト
    if not test_language():
        print("❌ Languageオブジェクトのテストに失敗しました")
        return False
    
    print("🎉 すべての処理が完了しました！")
    print("build/my-languages.so が利用可能です")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 