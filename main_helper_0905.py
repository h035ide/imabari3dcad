import sys
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """設定クラス - 全ての設定を一元管理"""

    def __init__(self):
        self.project_root = Path(__file__).parent

        # Neo4j設定（環境変数から読み込み）
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        # OpenAI設定（環境変数から読み込み）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # ファイルパス設定
        self.parsed_api_result_def_file = (
            "doc_parser/parsed_api_result_def.json"
        )
        self.parsed_api_result_file = "doc_parser/parsed_api_result.json"

        # Chroma設定
        self.chroma_persist_directory = "chroma_db_store"
        self.chroma_collection_name = "api_documentation"

        # LlM設定
        self.setup_llm_config()
        self.setup_embedding_config()
    
    def setup_llm_config(self):
        """LLM設定"""
        # 基本設定
        self.llm_model = "gpt-4o"
        self.response_format = "text"  # "json_object"
        # only for standard models
        self.llm_temperature = 0.1  # or None
        # only for inference models
        self.llm_verbosity = "high"  # "none" or "low" or "medium" or "high"
        self.llm_reasoning_effort = "high"  # "none" or "minimal" or "low" or "medium" or "high"
        
        # モデル判定
        self.is_inference_model = self._is_inference_model()
        
        # 設定辞書を構築
        self._build_llm_configs()
    
    def _is_inference_model(self):
        """推論モデルかどうかを判定"""
        inference_models = [
            "o4-mini", "o4", "gpt-5", "gpt-5-mini", "gpt-5-nano"
        ]
        return any(model in self.llm_model.lower()
                   for model in inference_models)
    
    def _build_llm_configs(self):
        """LLM設定辞書を構築"""
        # 基本設定
        base_config = {
            "api_key": self.openai_api_key
        }
        
        # LangChain用設定
        self.langchain_llm_config = {
            "model_name": self.llm_model,
            **base_config
        }
        
        # LlamaIndex用設定
        self.llamaindex_llm_config = {
            "model": self.llm_model,
            **base_config
        }
        
        # モデル別パラメータを追加
        if self.is_inference_model:
            self._add_inference_model_params()
        else:
            self._add_standard_model_params()
    
    def _add_inference_model_params(self):
        """推論モデル専用パラメータを追加"""
        # 推論モデルではtemperatureは使用しない
        self.llm_temperature = None
        
        inference_params = {
            "reasoning_effort": self.llm_reasoning_effort,
            "output_version": "responses/v1",
            "verbosity": self.llm_verbosity,
            "response_format": self.response_format
        }
        
        for key, value in inference_params.items():
            self.langchain_llm_config[key] = value
            self.llamaindex_llm_config[key] = value
    
    def _add_standard_model_params(self):
        """通常モデルのパラメータを追加"""
        # 通常モデルでは推論モデルパラメータは使用しない
        self.llm_verbosity = None
        self.llm_reasoning_effort = None
        
        # temperatureを追加
        if self.llm_temperature is not None:
            self.langchain_llm_config["temperature"] = self.llm_temperature
            self.llamaindex_llm_config["temperature"] = self.llm_temperature

    def setup_embedding_config(self):
        """埋め込みモデル設定"""
        # 基本設定
        self.embedding_model = "text-embedding-3-small"
        self.embedding_batch_size = 100
        
        # LangChain用設定
        self.langchain_embedding_config = {
            "model": self.embedding_model,
            "api_key": self.openai_api_key
        }
        
        # LlamaIndex用設定
        self.llamaindex_embedding_config = {
            "model": self.embedding_model,
            "batch_size": self.embedding_batch_size,
            "api_key": self.openai_api_key
        }
    
    def print_llm_config(self):
        """LLM設定を表示"""
        print("🤖 LLM設定:")
        print(f"  モデル: {self.llm_model}")
        print(f"  推論モデル: {'✅' if self.is_inference_model else '❌'}")
        print(f"  Temperature: {self.llm_temperature}")
        print(f"  Response Format: {self.response_format}")
        
        if self.is_inference_model:
            print(f"  Verbosity: {self.llm_verbosity}")
            print(f"  Reasoning Effort: {self.llm_reasoning_effort}")
        
        print("\n📋 LangChain設定:")
        for key, value in self.langchain_llm_config.items():
            print(f"  {key}: {value}")
        print("\n📋 LlamaIndex設定:")
        for key, value in self.llamaindex_llm_config.items():
            print(f"  {key}: {value}")
