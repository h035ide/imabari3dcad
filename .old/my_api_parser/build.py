# build.py
import os
import shutil
from tree_sitter import Language

# buildディレクトリが存在しない場合は作成
os.makedirs('build', exist_ok=True)

# tree-sitterの新しいバージョンでは、Language.build_libraryは削除されている可能性があります
# 代わりに、tree-sitter CLIを使用してビルドする必要があります
try:
    Language.build_library(
        # 作成する共有ライブラリのパス
        'build/my-languages.so',

        # パーサーを検索するディレクトリのリスト
        [
            '.' # カレントディレクトリ (grammar.jsがある場所)
        ]
    )
    print("ライブラリのビルドが完了しました: build/my-languages.so")
except AttributeError:
    print("tree-sitterの新しいバージョンでは、Language.build_libraryが削除されています。")
    print("tree-sitter CLIを使用してビルドしてください:")
    print("1. tree-sitter CLIをインストール: npm install -g tree-sitter-cli")
    print("2. ビルドを実行: tree-sitter generate")
    print("3. または、古いバージョンのtree-sitterを使用してください")
    
    # tree-sitter CLIで生成されたファイルが存在するか確認
    if os.path.exists('src/parser.c'):
        print("\ntree-sitter CLIでビルドが完了しています。")
        print("生成されたファイル:")
        print("- src/parser.c")
        print("- src/grammar.json")
        print("- src/node-types.json")
        print("\nこれらのファイルを使用してPythonでtree-sitterを使用できます。")
        
        # 共有ライブラリをビルドするために、tree-sitter CLIを使用
        print("\n共有ライブラリをビルドするには、以下のコマンドを実行してください:")
        print("tree-sitter build-wasm")
        print("または")
        print("tree-sitter build")
    else:
        print("\ntree-sitter CLIでビルドが完了していません。")
        print("以下のコマンドを実行してください:")
        print("tree-sitter generate")