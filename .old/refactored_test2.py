#!/usr/bin/env python3
# refactored_test2.py
"""
LLMによるAPI引数情報のリッチ化処理（クラスベース版）
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

@dataclass
class EnrichmentConfig:
    """LLMリッチ化の設定"""
    model: str = "gpt-4o-mini"
    temperature: float = 0
    input_file: str = 'api_functions_data.json'
    output_file: str = 'api_functions_data_enriched.json'

class LLMEnrichmentProcessor:
    """LLMによるAPI引数情報リッチ化クラス"""
    
    def __init__(self, config: Optional[EnrichmentConfig] = None):
        self.config = config or EnrichmentConfig()
        self._load_environment()
        self._setup_llm_components()
        self.functions_data: List[Dict[str, Any]] = []
        self.processed_count = 0
        self.error_count = 0
    
    def _load_environment(self):
        """環境変数を読み込み"""
        load_dotenv()
        
        # 必要な環境変数のチェック
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
    
    def _setup_llm_components(self):
        """LLMコンポーネントを設定"""
        # LLMモデルの定義
        self.model = ChatOpenAI(
            model=self.config.model, 
            temperature=self.config.temperature
        )
        
        # 出力パーサーの定義
        self.parser = JsonOutputParser()
        
        # プロンプトテンプレートの定義
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたはAPIドキュメントを分析する専門家です。ユーザーの指示に従い、分析結果を必ず指定されたJSON形式で出力してください。"),
            ("human", """
                以下のAPI引数の説明文を分析してください。

                # 説明文
                {description}

                # 抽出する情報
                1. "summary": 説明文を30字以内で簡潔に要約したもの。
                2. "constraints": 説明文に含まれる制約。"[空文字不可]"は"non-empty"、"[空文字可]"は"optional"として配列に格納する。

                # 出力フォーマット
                {format_instructions}
            """)
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        # チェーンの結合
        self.chain = self.prompt | self.model | self.parser
    
    def load_functions_data(self) -> List[Dict[str, Any]]:
        """JSONファイルから関数データを読み込み"""
        try:
            with open(self.config.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 関数データを読み込みました: {self.config.input_file}")
            print(f"   関数数: {len(data)}")
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"エラー: {self.config.input_file} が見つかりません")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONファイルの形式が正しくありません: {e}")
    
    def enrich_parameter(self, func_name: str, param: Dict[str, Any]) -> bool:
        """単一のパラメータをリッチ化"""
        try:
            print(f"Processing: {func_name} -> {param.get('name', 'N/A')}")
            
            # LLMチェーンを実行
            llm_result = self.chain.invoke({
                "description": param["description_raw"]
            })
            
            # 結果を更新
            param["summary_llm"] = llm_result.get("summary")
            param["constraints_llm"] = llm_result.get("constraints", [])
            
            self.processed_count += 1
            return True
            
        except OutputParserException as e:
            print(f"  - エラー: LLMの出力がJSON形式ではありませんでした。スキップします。 Error: {e}")
            self.error_count += 1
            return False
        except Exception as e:
            print(f"  - エラー: LLMの呼び出し中に予期せぬエラーが発生しました。スキップします。 Error: {e}")
            self.error_count += 1
            return False
    
    def enrich_function(self, func: Dict[str, Any]) -> int:
        """単一の関数の全パラメータをリッチ化"""
        if "params" not in func:
            return 0
        
        processed_params = 0
        for param in func["params"]:
            if self.enrich_parameter(func.get('name', 'N/A'), param):
                processed_params += 1
        
        return processed_params
    
    def enrich_all_functions(self, functions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """全関数のパラメータをリッチ化"""
        print("🚀 LLMによる情報リッチ化を開始します...")
        print("=" * 60)
        
        total_functions = len(functions_data)
        total_params = sum(len(func.get("params", [])) for func in functions_data)
        
        print(f"対象関数数: {total_functions}")
        print(f"対象パラメータ数: {total_params}")
        print("-" * 60)
        
        for i, func in enumerate(functions_data, 1):
            print(f"\n[{i}/{total_functions}] 関数: {func.get('name', 'N/A')}")
            processed = self.enrich_function(func)
            print(f"  処理済みパラメータ: {processed}/{len(func.get('params', []))}")
        
        return functions_data
    
    def save_enriched_data(self, functions_data: List[Dict[str, Any]]):
        """リッチ化されたデータを保存"""
        try:
            with open(self.config.output_file, 'w', encoding='utf-8') as f:
                json.dump(functions_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 リッチ化されたデータを保存しました: {self.config.output_file}")
        except Exception as e:
            raise IOError(f"ファイル保存に失敗しました: {e}")
    
    def display_statistics(self):
        """処理統計を表示"""
        print("\n" + "=" * 60)
        print("📊 処理統計")
        print("=" * 60)
        print(f"処理済みパラメータ数: {self.processed_count}")
        print(f"エラー数: {self.error_count}")
        print(f"成功率: {self.processed_count / (self.processed_count + self.error_count) * 100:.1f}%")
        
        if self.functions_data:
            print(f"\n最初の関数の最初のパラメータの処理結果:")
            first_func = self.functions_data[0]
            if first_func.get('params'):
                first_param = first_func['params'][0]
                print(json.dumps(first_param, indent=2, ensure_ascii=False))
    
    def process(self) -> List[Dict[str, Any]]:
        """メイン処理を実行"""
        print("🔧 LLMによるAPI引数情報リッチ化開始")
        print("=" * 60)
        
        # 1. データ読み込み
        self.functions_data = self.load_functions_data()
        
        # 2. リッチ化処理
        self.functions_data = self.enrich_all_functions(self.functions_data)
        
        # 3. 結果保存
        self.save_enriched_data(self.functions_data)
        
        # 4. 統計表示
        self.display_statistics()
        
        print("\nStep 2: LLMによる情報リッチ化が完了しました。")
        return self.functions_data

def main():
    """メイン関数"""
    config = EnrichmentConfig()
    processor = LLMEnrichmentProcessor(config)
    processor.process()

if __name__ == "__main__":
    main() 