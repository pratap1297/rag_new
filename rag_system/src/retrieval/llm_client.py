"""
LLM Client
Multi-provider LLM client for text generation
"""
import logging
import os
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from ..core.error_handling import LLMError, APIKeyError
except ImportError:
    from rag_system.src.core.error_handling import LLMError, APIKeyError

class BaseLLMClient(ABC):
    """Base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

class GroqClient(BaseLLMClient):
    """Groq LLM client with rate limiting"""
    
    # Class-level rate limiting variables
    last_request_time = 0
    min_request_interval = 1.0  # Minimum time between requests in seconds
    request_count = 0
    max_requests_per_minute = 50  # Maximum requests per minute
    
    def __init__(self, api_key: str, model_name: str = "mixtral-8x7b-32768", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            import groq
            self.client = groq.Groq(
                api_key=self.api_key,
                timeout=self.timeout
            )
        except ImportError:
            raise LLMError("Groq package not installed")
        except Exception as e:
            raise APIKeyError("groq")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to avoid hitting API limits"""
        current_time = time.time()
        
        # Check if we need to wait between requests
        time_since_last_request = current_time - GroqClient.last_request_time
        if time_since_last_request < GroqClient.min_request_interval:
            # Wait to maintain minimum interval between requests
            sleep_time = GroqClient.min_request_interval - time_since_last_request
            logging.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Update request count and check rate limits
        GroqClient.request_count += 1
        if GroqClient.request_count >= GroqClient.max_requests_per_minute:
            # If we've hit the rate limit, wait until the next minute
            logging.warning(f"Rate limit approaching: {GroqClient.request_count} requests. Slowing down.")
            time.sleep(2.0)  # Add extra delay when approaching limits
            GroqClient.request_count = 0  # Reset counter
        
        # Update last request time
        GroqClient.last_request_time = time.time()
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        try:
            # Apply rate limiting before making the request
            self._apply_rate_limiting()
            
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            logging.debug(f"Groq API call took {elapsed:.2f} seconds")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Groq generation error: {e}")
            raise LLMError(f"Groq generation failed: {e}", details={"provider": "groq", "model": self.model_name})

class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
        except ImportError:
            raise LLMError("OpenAI package not installed")
        except Exception as e:
            raise APIKeyError("openai")
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI API call took {elapsed:.2f} seconds")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"OpenAI generation error: {e}")
            raise LLMError(f"OpenAI generation failed: {e}", details={"provider": "openai", "model": self.model_name})

class AzureClient(BaseLLMClient):
    """Azure AI Inference LLM client"""
    
    def __init__(self, api_key: str, endpoint: str, model_name: str = "Llama-4-Maverick-17B-128E-Instruct-FP8", timeout: int = 30):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model_name = model_name
        self.timeout = timeout
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key),
                api_version="2024-05-01-preview"
            )
        except ImportError:
            raise LLMError("Azure AI Inference package not installed. Run: pip install azure-ai-inference")
        except Exception as e:
            raise APIKeyError("azure")
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        try:
            from azure.ai.inference.models import SystemMessage, UserMessage
            
            start_time = time.time()
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are a helpful assistant."),
                    UserMessage(content=prompt)
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                model=self.model_name
            )
            elapsed = time.time() - start_time
            logging.debug(f"Azure AI call took {elapsed:.2f} seconds")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Azure generation error: {e}")
            raise LLMError(f"Azure generation failed: {e}", details={"provider": "azure", "model": self.model_name})

class LLMClient:
    """Main LLM client with provider switching"""
    
    def __init__(self, provider: str = "groq", model_name: str = None, 
                 api_key: str = None, temperature: float = 0.1, max_tokens: int = 1000,
                 timeout: int = 30, endpoint: str = None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key or self._get_api_key(provider)
        self.endpoint = endpoint or self._get_endpoint(provider)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = None
        
        self._initialize_client()
        logging.info(f"LLM client initialized: {provider} (timeout: {timeout}s)")
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key from environment"""
        env_keys = {
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_API_KEY"
        }
        
        env_key = env_keys.get(provider)
        if not env_key:
            raise LLMError(f"Unknown provider: {provider}")
        
        api_key = os.getenv(env_key)
        if not api_key:
            raise APIKeyError(provider)
        
        return api_key
    
    def _get_endpoint(self, provider: str) -> str:
        """Get endpoint from environment for providers that need it"""
        if provider == "azure":
            endpoint = os.getenv("AZURE_CHAT_ENDPOINT")
            if not endpoint:
                raise LLMError("Azure endpoint not configured. Set AZURE_CHAT_ENDPOINT environment variable.")
            return endpoint
        return None
    
    def _initialize_client(self):
        """Initialize the appropriate client"""
        if self.provider == "groq":
            model = self.model_name or "meta-llama/llama-4-maverick-17b-128e-instruct"
            self.client = GroqClient(self.api_key, model, self.timeout)
        elif self.provider == "openai":
            model = self.model_name or "gpt-3.5-turbo"
            self.client = OpenAIClient(self.api_key, model, self.timeout)
        elif self.provider == "azure":
            model = self.model_name or "Llama-4-Maverick-17B-128E-Instruct-FP8"
            self.client = AzureClient(self.api_key, self.endpoint, model, self.timeout)
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text using the configured LLM"""
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        try:
            return self.client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test LLM connection"""
        try:
            response = self.generate("Hello", max_tokens=5)
            return bool(response)
        except Exception as e:
            logging.error(f"LLM connection test failed: {e}")
            return False 