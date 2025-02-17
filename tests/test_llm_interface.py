"""Tests for flexible LLM interface."""
import pytest
import torch
from unittest.mock import Mock, patch
import os
from typing import Dict, Any

from nova_aegis.llm_interface import (
    LLMInterface,
    LLMConfig,
    LocalQuantizedLLM,
    CloudLLM
)

# Test prompts and expected responses
TEST_PROMPTS = {
    "code_review": "Review this code: def add(a, b): return a + b",
    "code_explanation": "Explain how async/await works in Python",
    "code_suggestion": "Suggest improvements for: for i in range(len(list)): print(list[i])"
}

@pytest.fixture
def mock_gpu_environment():
    """Mock high-RAM GPU environment."""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.get_device_properties') as mock_props:
        # Mock 32GB VRAM
        mock_props.return_value = Mock(total_memory=32 * 1024**3)
        yield

@pytest.fixture
def mock_low_gpu_environment():
    """Mock low-RAM GPU environment."""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.get_device_properties') as mock_props:
        # Mock 8GB VRAM
        mock_props.return_value = Mock(total_memory=8 * 1024**3)
        yield

@pytest.fixture
def mock_cpu_environment():
    """Mock CPU-only environment."""
    with patch('torch.cuda.is_available', return_value=False):
        yield

@pytest.fixture
def mock_cloud_environment():
    """Mock environment with cloud API key."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        yield

@pytest.fixture
def mock_local_model():
    """Mock local model responses."""
    with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         patch('transformers.pipeline') as mock_pipeline:
        
        # Mock pipeline responses
        mock_pipeline.return_value = lambda x: [{"generated_text": f"Test response for: {x}"}]
        yield

@pytest.mark.asyncio
async def test_high_vram_gpu_setup(mock_gpu_environment, mock_local_model):
    """Test LLM setup with high VRAM GPU."""
    interface = LLMInterface()
    assert isinstance(interface.llm, LocalQuantizedLLM)
    assert interface.llm.config.model_name == "meta-llama/Llama-2-13b-chat-hf"
    assert interface.llm.config.device == "cuda"
    assert interface.llm.config.quantization == "4bit"

@pytest.mark.asyncio
async def test_low_vram_gpu_setup(mock_low_gpu_environment, mock_local_model):
    """Test LLM setup with low VRAM GPU."""
    interface = LLMInterface()
    assert isinstance(interface.llm, LocalQuantizedLLM)
    assert interface.llm.config.model_name == "meta-llama/Llama-2-7b-chat-hf"
    assert interface.llm.config.device == "cuda"
    assert interface.llm.config.quantization == "4bit"

@pytest.mark.asyncio
async def test_cpu_setup(mock_cpu_environment, mock_local_model):
    """Test LLM setup on CPU-only environment."""
    interface = LLMInterface()
    assert isinstance(interface.llm, LocalQuantizedLLM)
    assert interface.llm.config.model_name == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    assert interface.llm.config.device == "cpu"
    assert interface.llm.config.quantization == "4bit"

@pytest.mark.asyncio
async def test_cloud_setup(mock_cloud_environment):
    """Test LLM setup with cloud API."""
    interface = LLMInterface()
    assert isinstance(interface.llm, CloudLLM)
    assert interface.llm.config.model_name == "gpt-3.5-turbo"
    assert interface.llm.config.api_key == "test-key"

@pytest.mark.asyncio
async def test_local_generation(mock_cpu_environment, mock_local_model):
    """Test text generation with local model."""
    interface = LLMInterface()
    
    for prompt_name, prompt in TEST_PROMPTS.items():
        response = await interface.generate(prompt)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_context_generation(mock_cpu_environment, mock_local_model):
    """Test generation with additional context."""
    interface = LLMInterface()
    context = {
        "language": "python",
        "framework": "asyncio",
        "complexity": "intermediate"
    }
    
    response = await interface.generate_with_context(
        TEST_PROMPTS["code_explanation"],
        context
    )
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_error_handling(mock_cpu_environment):
    """Test error handling during model initialization and generation."""
    with patch('transformers.AutoModelForCausalLM.from_pretrained', 
              side_effect=Exception("Model load failed")):
        with pytest.raises(Exception) as exc_info:
            interface = LLMInterface()
        assert "Model load failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_quantization_config(mock_gpu_environment, mock_local_model):
    """Test quantization configuration."""
    interface = LLMInterface()
    assert interface.llm.config.quantization == "4bit"
    
    # Verify quantization config was passed to model loading
    mock_local_model.assert_called_once()
    call_kwargs = mock_local_model.call_args[1]
    assert "quantization_config" in call_kwargs
    assert call_kwargs["quantization_config"].load_in_4bit is True

@pytest.mark.asyncio
async def test_model_switching(mock_cloud_environment, mock_local_model):
    """Test switching between cloud and local models."""
    # Start with cloud model
    interface = LLMInterface()
    assert isinstance(interface.llm, CloudLLM)
    
    # Remove API key to force local model
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
        interface = LLMInterface()
        assert isinstance(interface.llm, LocalQuantizedLLM)

@pytest.mark.asyncio
async def test_concurrent_generation(mock_cpu_environment, mock_local_model):
    """Test concurrent generation requests."""
    interface = LLMInterface()
    
    # Generate multiple responses concurrently
    tasks = [
        interface.generate(prompt)
        for prompt in TEST_PROMPTS.values()
    ]
    
    responses = await asyncio.gather(*tasks)
    assert len(responses) == len(TEST_PROMPTS)
    assert all(isinstance(r, str) for r in responses)
    assert all(len(r) > 0 for r in responses)