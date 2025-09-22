from pathlib import Path

import pytest

from help_preprocessor.vector_generator import HelpVectorGenerator
from help_preprocessor.schemas import HelpSection


def make_section(content: str) -> HelpSection:
    return HelpSection(
        section_id="sec-1",
        title="Overview",
        content=content,
        anchors=["overview"],
        links=[],
        media=[],
    )


def test_build_chunks_respects_size_and_overlap() -> None:
    generator = HelpVectorGenerator(chunk_size=8, chunk_overlap=2)
    section = make_section("abcdefghijklmnop")
    chunks = generator.build_chunks(section)

    assert len(chunks) == 3
    assert chunks[0]["text"] == "abcdefgh"
    assert chunks[1]["text"].startswith("gh"), "chunks should overlap by two characters"
    assert chunks[0]["metadata"]["offset"] == 0
    assert chunks[1]["metadata"]["offset"] == 6


def test_build_chunks_handles_empty_text() -> None:
    generator = HelpVectorGenerator(chunk_size=5, chunk_overlap=1)
    section = make_section("   \n\t")
    assert generator.build_chunks(section) == []


def test_invalid_chunk_configuration() -> None:
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=0, chunk_overlap=0)
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=10, chunk_overlap=10)
    with pytest.raises(ValueError):
        HelpVectorGenerator(chunk_size=10, chunk_overlap=-1)


def test_embed_chunks_requires_openai_model() -> None:
    generator = HelpVectorGenerator()
    chunks = [{"id": "test", "text": "test content", "metadata": {}}]
    
    with pytest.raises(ValueError, match="OpenAI model must be specified"):
        list(generator.embed_chunks(chunks))


def test_embed_chunks_missing_openai_package(monkeypatch: pytest.MonkeyPatch) -> None:
    generator = HelpVectorGenerator()
    chunks = [{"id": "test", "text": "test content", "metadata": {}}]
    
    # Mock import failure
    import builtins
    original_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name == "openai":
            raise ImportError("No module named 'openai'")
        return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr(builtins, "__import__", mock_import)
    
    with pytest.raises(ImportError, match="OpenAI package required"):
        list(generator.embed_chunks(chunks, openai_model="text-embedding-3-small"))


def test_embed_chunks_with_mock_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test embedding functionality with mocked OpenAI client."""
    generator = HelpVectorGenerator()
    chunks = [
        {"id": "test1", "text": "first content", "metadata": {"section": "intro"}},
        {"id": "test2", "text": "second content", "metadata": {"section": "body"}},
    ]
    
    # Mock OpenAI client
    class MockEmbeddingResponse:
        def __init__(self, embedding):
            self.data = [type('obj', (object,), {'embedding': embedding})]
    
    class MockOpenAIClient:
        def __init__(self):
            self.call_count = 0
        
        def embeddings_create(self, model, input):
            self.call_count += 1
            # Return different embeddings for different inputs
            if "first" in input:
                return MockEmbeddingResponse([0.1, 0.2, 0.3])
            else:
                return MockEmbeddingResponse([0.4, 0.5, 0.6])
    
    mock_client = MockOpenAIClient()
    
    # Mock the openai module and Client
    import sys
    mock_openai = type('module', (), {
        'Client': lambda: type('client', (), {
            'embeddings': type('embeddings', (), {
                'create': mock_client.embeddings_create
            })
        })()
    })
    sys.modules['openai'] = mock_openai
    
    # Test embedding
    result = list(generator.embed_chunks(chunks, openai_model="text-embedding-3-small"))
    
    assert len(result) == 2
    assert result[0]["id"] == "test1"
    assert result[0]["embedding"] == [0.1, 0.2, 0.3]
    assert result[1]["id"] == "test2" 
    assert result[1]["embedding"] == [0.4, 0.5, 0.6]
    assert mock_client.call_count == 2
    
    # Clean up
    del sys.modules['openai']
