import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# 解析対象ファイルのパス
TARGET_FILE = "./evoship/create_test.py"

def main():
    # ファイル読み込み
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        source_code = f.read()
    source_code_bytes = bytes(source_code, "utf8")

    # tree-sitterセットアップ
    py_language = Language(tspython.language())
    parser = Parser(py_language)
    tree = parser.parse(source_code_bytes)

    # 構文木のルートノード取得
    root_node = tree.root_node

    # 構文木を再帰的に表示
    def print_node(node, indent=0):
        prefix = "  " * indent
        node_text = source_code_bytes[node.start_byte:node.end_byte].decode('utf8')
        # 長いテキストは省略
        if len(node_text) > 50:
            node_text = node_text[:47] + "..."
        print(f"{prefix}{node.type}: '{node_text}' (start: {node.start_byte}, end: {node.end_byte})")
        for child in node.children:
            print_node(child, indent + 1)

    print_node(root_node)

if __name__ == "__main__":
    main()
