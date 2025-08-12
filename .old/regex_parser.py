#!/usr/bin/env python3
# regex_parser.py
"""
正規表現ベースのAPIドキュメントパーサー
grammar.jsの構文定義を参考に実装
"""

import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class APIDocNode:
    """APIドキュメントのノードを表すクラス"""
    type: str
    text: str
    children: List['APIDocNode']
    start_pos: int
    end_pos: int
    
    def to_dict(self) -> Dict[str, Any]:
        """ノードを辞書形式に変換"""
        return {
            'type': self.type,
            'text': self.text,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'children': [child.to_dict() for child in self.children]
        }

class RegexAPIParser:
    """正規表現ベースのAPIドキュメントパーサー"""
    
    def __init__(self):
        # 正規表現パターンの定義（grammar.jsを参考）
        self.patterns = {
            # 空白文字（改行含む）
            'whitespace': r'\s+',
            
            # 行頭の*や、/**, */などの記号
            'comment_symbols': r'\*+!?',
            
            # 型定義: {型}
            'type': r'\{[^{}\n]+\}',
            
            # 識別子: 関数名や変数名
            'identifier': r'[a-zA-Z_][a-zA-Z0-9_]*',
            
            # 説明: タグ行の残りの説明部分
            'description': r'[^\n]*',
            
            # タグ以外のテキスト行
            'doc_text': r'[^@*/\s][^\n]*',
            
            # 各種タグ
            'function_tag': r'@function\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'class_tag': r'@class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'param_tag': r'@param\s+(\{[^{}\n]+\})\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([^\n]*)',
            'property_tag': r'@property\s+(\{[^{}\n]+\})\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([^\n]*)',
            'returns_tag': r'@returns\s+(\{[^{}\n]+\})\s+([^\n]*)',
            
            # ドキュメントコメントの開始と終了
            'doc_start': r'/\*\*',
            'doc_end': r'\*/',
        }
        
        # コンパイルされた正規表現
        self.compiled_patterns = {
            key: re.compile(pattern, re.MULTILINE | re.DOTALL)
            for key, pattern in self.patterns.items()
        }
    
    def parse(self, text: str) -> APIDocNode:
        """テキストをパースしてASTを生成"""
        # ソースファイルノードを作成
        source_file = APIDocNode(
            type='source_file',
            text=text,
            children=[],
            start_pos=0,
            end_pos=len(text)
        )
        
        # ドキュメントコメントを検索
        doc_comments = self._find_doc_comments(text)
        
        for doc_comment in doc_comments:
            source_file.children.append(doc_comment)
        
        return source_file
    
    def _find_doc_comments(self, text: str) -> List[APIDocNode]:
        """ドキュメントコメントを検索"""
        doc_comments = []
        
        # /** と */ のペアを検索
        doc_start_pattern = self.compiled_patterns['doc_start']
        doc_end_pattern = self.compiled_patterns['doc_end']
        
        start_matches = list(doc_start_pattern.finditer(text))
        end_matches = list(doc_end_pattern.finditer(text))
        
        # 開始と終了のペアを作成
        pairs = []
        for start_match in start_matches:
            start_pos = start_match.end()
            # 対応する終了位置を探す
            for end_match in end_matches:
                if end_match.start() > start_pos:
                    end_pos = end_match.start()
                    pairs.append((start_pos, end_pos, start_match.start(), end_match.end()))
                    break
        
        # 各ペアをパース
        for content_start, content_end, full_start, full_end in pairs:
            content = text[content_start:content_end]
            full_text = text[full_start:full_end]
            
            doc_comment = APIDocNode(
                type='doc_comment',
                text=full_text,
                children=[],
                start_pos=full_start,
                end_pos=full_end
            )
            
            # 内容をパース
            children = self._parse_doc_content(content, content_start)
            doc_comment.children = children
            
            doc_comments.append(doc_comment)
        
        return doc_comments
    
    def _parse_doc_content(self, content: str, offset: int) -> List[APIDocNode]:
        """ドキュメントコメントの内容をパース"""
        children = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines):
            line_start = offset + sum(len(l) + 1 for l in lines[:line_num])
            line_end = line_start + len(line)
            
            # 行をパース
            line_nodes = self._parse_line(line, line_start)
            children.extend(line_nodes)
        
        return children
    
    def _parse_line(self, line: str, offset: int) -> List[APIDocNode]:
        """1行をパース"""
        nodes = []
        
        # 空白と*記号をスキップ
        line = line.strip()
        if not line:
            return nodes
        
        # *記号で始まる場合は除去
        if line.startswith('*'):
            line = line[1:].strip()
            if not line:
                return nodes
        
        # 各種タグをチェック
        tag_patterns = [
            ('function_tag', self.compiled_patterns['function_tag']),
            ('class_tag', self.compiled_patterns['class_tag']),
            ('param_tag', self.compiled_patterns['param_tag']),
            ('property_tag', self.compiled_patterns['property_tag']),
            ('returns_tag', self.compiled_patterns['returns_tag']),
        ]
        
        for tag_type, pattern in tag_patterns:
            match = pattern.match(line)
            if match:
                if tag_type == 'function_tag':
                    node = self._create_function_tag_node(match, offset)
                elif tag_type == 'class_tag':
                    node = self._create_class_tag_node(match, offset)
                elif tag_type == 'param_tag':
                    node = self._create_param_tag_node(match, offset)
                elif tag_type == 'property_tag':
                    node = self._create_property_tag_node(match, offset)
                elif tag_type == 'returns_tag':
                    node = self._create_returns_tag_node(match, offset)
                
                nodes.append(node)
                return nodes
        
        # タグでない場合はdoc_textとして扱う
        if line and not line.startswith('@'):
            node = APIDocNode(
                type='doc_text',
                text=line,
                children=[],
                start_pos=offset,
                end_pos=offset + len(line)
            )
            nodes.append(node)
        
        return nodes
    
    def _create_function_tag_node(self, match, offset: int) -> APIDocNode:
        """@functionタグのノードを作成"""
        identifier = match.group(1)
        
        node = APIDocNode(
            type='function_tag',
            text=match.group(0),
            children=[
                APIDocNode(
                    type='identifier',
                    text=identifier,
                    children=[],
                    start_pos=offset + match.start(1),
                    end_pos=offset + match.end(1)
                )
            ],
            start_pos=offset + match.start(),
            end_pos=offset + match.end()
        )
        
        return node
    
    def _create_class_tag_node(self, match, offset: int) -> APIDocNode:
        """@classタグのノードを作成"""
        identifier = match.group(1)
        
        node = APIDocNode(
            type='class_tag',
            text=match.group(0),
            children=[
                APIDocNode(
                    type='identifier',
                    text=identifier,
                    children=[],
                    start_pos=offset + match.start(1),
                    end_pos=offset + match.end(1)
                )
            ],
            start_pos=offset + match.start(),
            end_pos=offset + match.end()
        )
        
        return node
    
    def _create_param_tag_node(self, match, offset: int) -> APIDocNode:
        """@paramタグのノードを作成"""
        param_type = match.group(1)
        identifier = match.group(2)
        description = match.group(3)
        
        node = APIDocNode(
            type='param_tag',
            text=match.group(0),
            children=[
                APIDocNode(
                    type='type',
                    text=param_type,
                    children=[],
                    start_pos=offset + match.start(1),
                    end_pos=offset + match.end(1)
                ),
                APIDocNode(
                    type='identifier',
                    text=identifier,
                    children=[],
                    start_pos=offset + match.start(2),
                    end_pos=offset + match.end(2)
                ),
                APIDocNode(
                    type='description',
                    text=description,
                    children=[],
                    start_pos=offset + match.start(3),
                    end_pos=offset + match.end(3)
                )
            ],
            start_pos=offset + match.start(),
            end_pos=offset + match.end()
        )
        
        return node
    
    def _create_property_tag_node(self, match, offset: int) -> APIDocNode:
        """@propertyタグのノードを作成"""
        property_type = match.group(1)
        identifier = match.group(2)
        description = match.group(3)
        
        node = APIDocNode(
            type='property_tag',
            text=match.group(0),
            children=[
                APIDocNode(
                    type='type',
                    text=property_type,
                    children=[],
                    start_pos=offset + match.start(1),
                    end_pos=offset + match.end(1)
                ),
                APIDocNode(
                    type='identifier',
                    text=identifier,
                    children=[],
                    start_pos=offset + match.start(2),
                    end_pos=offset + match.end(2)
                ),
                APIDocNode(
                    type='description',
                    text=description,
                    children=[],
                    start_pos=offset + match.start(3),
                    end_pos=offset + match.end(3)
                )
            ],
            start_pos=offset + match.start(),
            end_pos=offset + match.end()
        )
        
        return node
    
    def _create_returns_tag_node(self, match, offset: int) -> APIDocNode:
        """@returnsタグのノードを作成"""
        return_type = match.group(1)
        description = match.group(2)
        
        node = APIDocNode(
            type='returns_tag',
            text=match.group(0),
            children=[
                APIDocNode(
                    type='type',
                    text=return_type,
                    children=[],
                    start_pos=offset + match.start(1),
                    end_pos=offset + match.end(1)
                ),
                APIDocNode(
                    type='description',
                    text=description,
                    children=[],
                    start_pos=offset + match.start(2),
                    end_pos=offset + match.end(2)
                )
            ],
            start_pos=offset + match.start(),
            end_pos=offset + match.end()
        )
        
        return node

def print_ast(node: APIDocNode, depth: int = 0):
    """ASTを表示"""
    indent = "  " * depth
    text_preview = node.text[:50] + "..." if len(node.text) > 50 else node.text
    print(f"{indent}{node.type}: '{text_preview}' [{node.start_pos}-{node.end_pos}]")
    
    for child in node.children:
        print_ast(child, depth + 1)

def main():
    """メイン関数"""
    print("🔧 正規表現ベースAPIドキュメントパーサー")
    print("=" * 50)
    
    # テスト用のコード
    test_code = '''
/**
 * @function calculateSum
 * 2つの数値を足し算する関数
 * @param {number} a - 最初の数値
 * @param {number} b - 2番目の数値
 * @returns {number} 合計値
 */
function calculateSum(a, b) {
    return a + b;
}

/**
 * @class Calculator
 * 計算機クラス
 * @property {string} name - 計算機の名前
 */
class Calculator {
    constructor(name) {
        this.name = name;
    }
}
'''
    
    # パーサーを作成
    parser = RegexAPIParser()
    
    # パースを実行
    print("📝 パースを開始...")
    ast = parser.parse(test_code)
    
    print("✅ パースが完了しました！")
    print("\n🌳 AST構造:")
    print_ast(ast)
    
    # JSON形式で出力
    print("\n📄 JSON形式:")
    print(json.dumps(ast.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 