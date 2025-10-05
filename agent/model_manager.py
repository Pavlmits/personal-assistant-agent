"""
Model Manager for AI Agent
Handles multiple AI model providers and configurations
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import openai
except ImportError:
    openai = None

try:
    import ollama
except ImportError:
    ollama = None

class ModelProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: ModelProvider
    model_id: str
    max_tokens: int = 300
    temperature: float = 0.7
    requires_api_key: bool = False
    local: bool = False
    description: str = ""

class ModelManager:
    """
    Manages different AI models for the agent
    """
    
    def __init__(self, config_file: str = "model_config.json"):
        self.config_file = config_file
        self.available_models = self._initialize_models()
        self.current_model = self._load_current_model()
        self._setup_clients()
    
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize available models"""
        models = {
            # Ollama models (local, open-source)
            "llama3.1": ModelConfig(
                name="Llama 3.1 8B",
                provider=ModelProvider.OLLAMA,
                model_id="llama3.1:8b",
                max_tokens=400,
                temperature=0.7,
                requires_api_key=False,
                local=True,
                description="Meta's Llama 3.1 8B - excellent open-source model for conversation"
            ),
            "mistral": ModelConfig(
                name="Mistral 7B",
                provider=ModelProvider.OLLAMA,
                model_id="mistral:7b",
                max_tokens=300,
                temperature=0.7,
                requires_api_key=False,
                local=True,
                description="Mistral 7B - fast and efficient open-source model"
            ),
            # OpenAI models
            "gpt-4": ModelConfig(
                name="GPT-4",
                provider=ModelProvider.OPENAI,
                model_id="gpt-4",
                max_tokens=300,
                temperature=0.7,
                requires_api_key=True,
                local=False,
                description="OpenAI's GPT-4 - most capable but slower and more expensive"
            ),
        }
        
        return models
    
    def _load_current_model(self) -> str:
        """Load current model selection from config"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('current_model', 'llama3.1')  # Default to Llama 3.1
            except:
                pass
        
        return 'llama3.1'  # Default to open-source Llama 3.1
    
    def _save_current_model(self):
        """Save current model selection to config"""
        config = {'current_model': self.current_model}
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)
                    existing_config.update(config)
                    config = existing_config
            except:
                pass
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _setup_clients(self):
        """Setup API clients for different providers"""
        self.clients = {}
        
        # OpenAI client
        if openai and os.getenv('OPENAI_API_KEY'):
            try:
                self.clients[ModelProvider.OPENAI] = openai.OpenAI(
                    api_key=os.getenv('OPENAI_API_KEY')
                )
            except Exception as e:
                print(f"Failed to setup OpenAI client: {e}")
        
        # Ollama client (local)
        if ollama:
            try:
                # Test if Ollama is running
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    self.clients[ModelProvider.OLLAMA] = ollama
            except Exception:
                print("Ollama not available. Install Ollama and run 'ollama serve' to use local models.")
    
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Get all available models"""
        available = {}
        
        for model_key, config in self.available_models.items():
            if self._is_model_available(config):
                available[model_key] = config
        
        return available
    
    def _is_model_available(self, config: ModelConfig) -> bool:
        """Check if a model is available"""
        if config.provider == ModelProvider.OLLAMA:
            if ModelProvider.OLLAMA not in self.clients:
                return False
            
            # Check if model is downloaded
            try:
                models = ollama.list()
                model_names = [model.model for model in models.models]
                return any(config.model_id in name for name in model_names)
            except:
                return False
        
        elif config.provider in [ModelProvider.OPENAI]:
            return config.provider in self.clients
        
        return False
    
    def set_model(self, model_key: str) -> bool:
        """Set the current model"""
        if model_key not in self.available_models:
            return False
        
        config = self.available_models[model_key]
        if not self._is_model_available(config):
            return False
        
        self.current_model = model_key
        self._save_current_model()
        return True
    
    def get_current_model(self) -> ModelConfig:
        """Get current model configuration"""
        return self.available_models[self.current_model]
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using current model"""
        config = self.get_current_model()
        
        # Override default parameters with kwargs
        max_tokens = kwargs.get('max_tokens', config.max_tokens)
        temperature = kwargs.get('temperature', config.temperature)
        
        try:
            if config.provider == ModelProvider.OLLAMA:
                return self._generate_ollama_response(config, messages, max_tokens, temperature)
            elif config.provider == ModelProvider.OPENAI:
                return self._generate_openai_response(config, messages, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
        
        except Exception as e:
            print(f"Error generating response with {config.name}: {e}")
            return self._generate_fallback_response(messages[-1]['content'] if messages else "")
    
    def _generate_ollama_response(self, config: ModelConfig, messages: List[Dict], max_tokens: int, temperature: float) -> str:
        """Generate response using Ollama"""
        # Convert messages to Ollama format
        prompt = self._messages_to_prompt(messages)
        
        response = ollama.generate(
            model=config.model_id,
            prompt=prompt,
            options={
                'num_predict': max_tokens,
                'temperature': temperature,
            }
        )
        
        return response['response'].strip()
    
    def _generate_openai_response(self, config: ModelConfig, messages: List[Dict], max_tokens: int, temperature: float) -> str:
        """Generate response using OpenAI"""
        client = self.clients[ModelProvider.OPENAI]
        
        response = client.chat.completions.create(
            model=config.model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
    
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert messages to a single prompt string"""
        prompt = ""
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'user':
                prompt += f"Human: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        return prompt
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Generate fallback response when models are unavailable"""
        fallback_responses = [
            "I understand you're asking about that. Let me help you with what I can.",
            "That's an interesting point. I'm here to assist you as best I can.",
            "I see what you're getting at. How can I be most helpful with that?",
            "Thanks for sharing that. What would be the most useful way I can help?",
            "I appreciate you bringing that up. Let me think about how to best assist you."
        ]
        
        import random
        return random.choice(fallback_responses)
    
    def download_model(self, model_key: str) -> bool:
        """Download a model (for Ollama)"""
        if model_key not in self.available_models:
            return False
        
        config = self.available_models[model_key]
        
        if config.provider != ModelProvider.OLLAMA:
            print(f"Model {config.name} doesn't need downloading")
            return True
        
        if ModelProvider.OLLAMA not in self.clients:
            print("Ollama not available. Please install Ollama first.")
            return False
        
        try:
            print(f"Downloading {config.name}...")
            ollama.pull(config.model_id)
            print(f"Successfully downloaded {config.name}")
            return True
        except Exception as e:
            print(f"Failed to download {config.name}: {e}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        status = {
            'current_model': self.current_model,
            'current_model_info': self.get_current_model(),
            'available_models': {},
            'providers_status': {}
        }
        
        # Check provider status
        status['providers_status'] = {
            'ollama': ModelProvider.OLLAMA in self.clients,
            'openai': ModelProvider.OPENAI in self.clients,
        }
        
        # Check model availability
        for key, config in self.available_models.items():
            status['available_models'][key] = {
                'name': config.name,
                'provider': config.provider.value,
                'available': self._is_model_available(config),
                'local': config.local,
                'description': config.description
            }
        
        return status
    
    def recommend_model(self) -> str:
        """Recommend the best available model"""
        available = self.get_available_models()
        
        if not available:
            return None
        
        # Priority order: Local models first, then cloud models
        priority_order = [
            'llama3.1',      # Best local model
            'mistral',       # Fast local alternative
            'gpt-4', # Good cloud fallback
        ]
        
        for model_key in priority_order:
            if model_key in available:
                return model_key
        
        return next(iter(available.keys()))
    
    def setup_default_model(self) -> str:
        """Setup the default recommended model"""
        recommended = self.recommend_model()
        
        if recommended:
            self.set_model(recommended)
            return recommended
        
        return None
