#!/usr/bin/env python3
# api_document_processor.py
"""
APIドキュメント処理の統合クラス
3つのステップ（パース、LLMリッチ化、Neo4j登録）を統合管理
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 各ステップのクラスをインポート
from refactored_test1 import APIDocumentParser, FunctionData
from refactored_test2 import LLMEnrichmentProcessor, EnrichmentConfig
from refactored_test3 import Neo4jDataUploader, Neo4jConfig

@dataclass
class ProcessingConfig:
    """統合処理の設定"""
    # Step 1: パース設定
    input_document: str = 'api_document.txt'
    parsed_output: str = 'api_functions_data.json'
    
    # Step 2: LLMリッチ化設定
    model: str = "gpt-4o-mini"
    temperature: float = 0
    enriched_output: str = 'api_functions_data_enriched.json'
    
    # Step 3: Neo4j設定
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "your_password"
    neo4j_database: str = "neo4j"
    
    # 処理制御
    skip_parse: bool = False
    skip_enrichment: bool = False
    skip_neo4j_upload: bool = False

class APIDocumentProcessor:
    """APIドキュメント処理の統合クラス"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self._load_environment()
        self._setup_components()
        self.functions_data: List[Dict[str, Any]] = []
        self.processing_stats = {
            'parse_success': False,
            'enrichment_success': False,
            'neo4j_upload_success': False,
            'total_functions': 0,
            'total_params': 0
        }
    
    def _load_environment(self):
        """環境変数を読み込み"""
        load_dotenv()
        
        # 環境変数から設定を更新
        self.config.neo4j_uri = os.environ.get("NEO4J_URI", self.config.neo4j_uri)
        self.config.neo4j_user = os.environ.get("NEO4J_USER", self.config.neo4j_user)
        self.config.neo4j_password = os.environ.get("NEO4J_PASSWORD", self.config.neo4j_password)
        
        # 必要な環境変数のチェック
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
    
    def _setup_components(self):
        """各コンポーネントを設定"""
        # Step 1: パーサー
        self.parser = APIDocumentParser(
            input_file=self.config.input_document,
            output_file=self.config.parsed_output
        )
        
        # Step 2: LLMリッチ化プロセッサー
        enrichment_config = EnrichmentConfig(
            model=self.config.model,
            temperature=self.config.temperature,
            input_file=self.config.parsed_output,
            output_file=self.config.enriched_output
        )
        self.enrichment_processor = LLMEnrichmentProcessor(enrichment_config)
        
        # Step 3: Neo4jアップローダー
        neo4j_config = Neo4jConfig(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
            database=self.config.neo4j_database,
            input_file=self.config.enriched_output
        )
        self.neo4j_uploader = Neo4jDataUploader(neo4j_config)
    
    def step1_parse_document(self) -> bool:
        """Step 1: APIドキュメントのパース"""
        if self.config.skip_parse:
            print("⏭️  Step 1 (パース) をスキップします")
            return True
        
        print("\n" + "=" * 80)
        print("STEP 1: APIドキュメントのパース")
        print("=" * 80)
        
        try:
            self.functions_data = self.parser.process()
            self.processing_stats['parse_success'] = True
            self.processing_stats['total_functions'] = len(self.functions_data)
            self.processing_stats['total_params'] = sum(
                len(func.get('params', [])) for func in self.functions_data
            )
            return True
        except Exception as e:
            print(f"❌ Step 1 でエラーが発生しました: {e}")
            return False
    
    def step2_enrich_with_llm(self) -> bool:
        """Step 2: LLMによる情報リッチ化"""
        if self.config.skip_enrichment:
            print("⏭️  Step 2 (LLMリッチ化) をスキップします")
            return True
        
        print("\n" + "=" * 80)
        print("STEP 2: LLMによる情報リッチ化")
        print("=" * 80)
        
        try:
            self.functions_data = self.enrichment_processor.process()
            self.processing_stats['enrichment_success'] = True
            return True
        except Exception as e:
            print(f"❌ Step 2 でエラーが発生しました: {e}")
            return False
    
    def step3_upload_to_neo4j(self) -> bool:
        """Step 3: Neo4jへのデータ登録"""
        if self.config.skip_neo4j_upload:
            print("⏭️  Step 3 (Neo4j登録) をスキップします")
            return True
        
        print("\n" + "=" * 80)
        print("STEP 3: Neo4jへのデータ登録")
        print("=" * 80)
        
        try:
            success = self.neo4j_uploader.process()
            self.processing_stats['neo4j_upload_success'] = success
            return success
        except Exception as e:
            print(f"❌ Step 3 でエラーが発生しました: {e}")
            return False
    
    def display_final_statistics(self):
        """最終統計を表示"""
        print("\n" + "=" * 80)
        print("📊 最終処理統計")
        print("=" * 80)
        
        print(f"Step 1 (パース): {'✅ 成功' if self.processing_stats['parse_success'] else '❌ 失敗'}")
        print(f"Step 2 (LLMリッチ化): {'✅ 成功' if self.processing_stats['enrichment_success'] else '❌ 失敗'}")
        print(f"Step 3 (Neo4j登録): {'✅ 成功' if self.processing_stats['neo4j_upload_success'] else '❌ 失敗'}")
        
        if self.processing_stats['total_functions'] > 0:
            print(f"\n処理された関数数: {self.processing_stats['total_functions']}")
            print(f"処理されたパラメータ数: {self.processing_stats['total_params']}")
        
        # 各ステップの詳細統計
        if hasattr(self.parser, 'functions_data'):
            print(f"\nStep 1 詳細:")
            print(f"  抽出された関数数: {len(self.parser.functions_data)}")
        
        if hasattr(self.enrichment_processor, 'processed_count'):
            print(f"\nStep 2 詳細:")
            print(f"  処理済みパラメータ数: {self.enrichment_processor.processed_count}")
            print(f"  エラー数: {self.enrichment_processor.error_count}")
        
        if hasattr(self.neo4j_uploader, 'uploaded_functions'):
            print(f"\nStep 3 詳細:")
            print(f"  アップロード済み関数数: {self.neo4j_uploader.uploaded_functions}")
            print(f"  アップロード済み引数数: {self.neo4j_uploader.uploaded_arguments}")
            print(f"  アップロード済み型数: {self.neo4j_uploader.uploaded_types}")
    
    def process(self) -> bool:
        """全処理を実行"""
        print("🚀 APIドキュメント処理パイプライン開始")
        print("=" * 80)
        
        try:
            # Step 1: パース
            if not self.step1_parse_document():
                return False
            
            # Step 2: LLMリッチ化
            if not self.step2_enrich_with_llm():
                return False
            
            # Step 3: Neo4j登録
            if not self.step3_upload_to_neo4j():
                return False
            
            # 最終統計表示
            self.display_final_statistics()
            
            print("\n🎉 全処理が正常に完了しました！")
            return True
            
        except Exception as e:
            print(f"\n💥 処理中に予期せぬエラーが発生しました: {e}")
            return False

def main():
    """メイン関数"""
    # 設定のカスタマイズ例
    config = ProcessingConfig(
        # 特定のステップのみ実行したい場合
        # skip_parse=True,
        # skip_enrichment=True,
        # skip_neo4j_upload=True,
    )
    
    processor = APIDocumentProcessor(config)
    success = processor.process()
    
    if not success:
        print("\n❌ 処理が失敗しました")
        exit(1)

if __name__ == "__main__":
    main() 