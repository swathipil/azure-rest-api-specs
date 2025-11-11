#!/usr/bin/env python3
"""LLM client creation and unified API wrapper for OpenAI and Anthropic."""

import os
from typing import List, Dict, Any


def create_llm_client(provider: str = None):
    """Create and return an LLM client based on provider or environment variables.
    
    Args:
        provider: "openai" or "anthropic". If None, uses LLM_PROVIDER env var.
    
    Supports:
    - OpenAI API (standard)
    - Azure OpenAI (with endpoint and key/credential)
    - Anthropic Claude
    
    Environment variables:
    - LLM_PROVIDER: "openai" (default) or "anthropic"
    - AZURE_OPENAI_ENDPOINT: If set, uses Azure OpenAI
    - AZURE_OPENAI_API_KEY: API key for Azure OpenAI (optional, uses DefaultAzureCredential if not set)
    - OPENAI_API_KEY: API key for standard OpenAI
    - ANTHROPIC_API_KEY: API key for Claude
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
    else:
        provider = provider.lower()
    
    if provider == "anthropic":
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Run: pip install anthropic"
            )
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required for Anthropic provider")
        
        return AsyncAnthropic(api_key=api_key)
    
    elif provider == "openai":
        # Check for Azure OpenAI first
        az_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        az_key = os.getenv("AZURE_OPENAI_API_KEY")
        std_key = os.getenv("OPENAI_API_KEY")
        
        if az_endpoint:
            from openai import AsyncAzureOpenAI
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
            
            if az_key:
                return AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=api_version,
                    api_key=az_key
                )
            else:
                credential = DefaultAzureCredential()
                return AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=api_version,
                    azure_ad_token_provider=get_bearer_token_provider(
                        credential,
                        "https://cognitiveservices.azure.com/.default"
                    ),
                )
        else:
            # Standard OpenAI
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=std_key or az_key)
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Supported: 'openai', 'anthropic'")


async def call_llm(
    client: Any,
    messages: List[Dict[str, str]],
    model: str,
    max_tokens: int = 2000,
    provider: str = None,
    temperature: float = 0.0
) -> str:
    """Unified LLM API call supporting OpenAI and Anthropic.
    
    Args:
        client: LLM client (AsyncAzureOpenAI, AsyncOpenAI, or AsyncAnthropic)
        messages: List of message dicts with "role" and "content" keys
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
        max_tokens: Maximum tokens to generate
        provider: "openai" or "anthropic" (auto-detected if None)
        temperature: Temperature for sampling
        
    Returns:
        Response text content
    """
    # Detect client type by checking for specific attributes or use provider hint
    if provider:
        is_anthropic = provider.lower() == "anthropic"
    else:
        client_type = type(client).__name__
        is_anthropic = "Anthropic" in client_type
    
    if is_anthropic:
        # Claude API format
        # Separate system messages from user/assistant messages
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        system_prompt = "\n\n".join(system_msgs) if system_msgs else None
        
        # Filter to user/assistant messages only
        conversation = [m for m in messages if m["role"] in ("user", "assistant")]
        
        response = await client.messages.create(
            model=model,
            system=system_prompt if system_prompt else "",
            messages=conversation,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.content[0].text.strip()
    
    else:
        # OpenAI API format (works for both AsyncOpenAI and AsyncAzureOpenAI)
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            # Add debug info for Azure OpenAI 404 errors
            if "404" in str(e):
                import sys
                print(f"\n❌ 404 Error - Model/Deployment Not Found", file=sys.stderr)
                print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'N/A')}", file=sys.stderr)
                print(f"   Model/Deployment: {model}", file=sys.stderr)
                print(f"   API Version: {os.getenv('AZURE_OPENAI_API_VERSION', 'N/A')}", file=sys.stderr)
                print(f"\n   Possible causes:", file=sys.stderr)
                print(f"   1. Deployment '{model}' doesn't exist in your Azure OpenAI resource", file=sys.stderr)
                print(f"   2. API version is incorrect (try '2024-10-21' or '2024-08-01-preview')", file=sys.stderr)
                print(f"   3. Endpoint URL is incorrect\n", file=sys.stderr)
            raise


def get_model_name(provider: str = None) -> str:
    """Get the model name based on provider and environment variables.
    
    For Azure OpenAI, returns the deployment name (AZURE_OPENAI_DEPLOYMENT).
    For OpenAI/Anthropic, returns the model name.
    
    Args:
        provider: "openai" or "anthropic". If None, uses LLM_PROVIDER env var.
    
    Returns:
        Model/deployment name to use for LLM calls
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
    else:
        provider = provider.lower()
    
    if provider == "anthropic":
        # Allow override via MODEL env var, otherwise use latest Claude
        return os.getenv("MODEL", "claude-3-5-sonnet-20241022")
    else:
        # OpenAI/Azure OpenAI
        # For Azure, prefer AZURE_OPENAI_DEPLOYMENT (deployment name), otherwise MODEL
        az_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if az_endpoint:
            # Azure OpenAI - use deployment name
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
            if deployment:
                return deployment
        
        # Standard OpenAI or fallback
        return os.getenv("MODEL", "gpt-4o")
