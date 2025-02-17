"""
LLM interface for model interactions.
"""
from typing import Dict, List, Any, Optional
import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline
)

class LLMInterface:
    """Interface for LLM interactions."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # For testing, use a mock LLM
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                openai_api_key="sk-mock-key-for-testing"
            )
            return
        
        # Initialize appropriate model
        if "gpt" in self.model_name.lower():
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.7,
                openai_api_key=api_key
            )
        else:
            # Load local model
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15
            )
            
            self.llm = HuggingFacePipeline(pipeline=pipe)
    
    def create_chain(
        self,
        template: str,
        output_key: str = "text"
    ) -> LLMChain:
        """Create LLM chain with template."""
        prompt = PromptTemplate(
            template=template,
            input_variables=["input"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key=output_key
        )
    
    async def generate(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """Generate text from prompt."""
        chain = self.create_chain(prompt)
        result = await chain.arun(input=kwargs)
        return result
    
    async def analyze(
        self,
        text: str,
        instruction: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Analyze text with instruction."""
        template = f"""
        Analyze the following text according to these instructions:
        {instruction}
        
        Text: {text}
        
        Analysis:
        """
        
        chain = self.create_chain(template)
        result = await chain.arun(input=kwargs)
        
        return {
            "text": text,
            "instruction": instruction,
            "analysis": result
        }