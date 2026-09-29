# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 04 - Open WebUI Chat API Integration
#
# ## Goal
#
# Demonstrate how to interact with the Open WebUI Chat API (e-INFRA CZ AI service) from a Jupyter notebook. This notebook shows authentication, listing available models, and performing chat completions using the OpenAI-compatible API.
#
# **Runtime**: ~1-2 minutes
#
# **Documentation**: https://docs.cerit-sc.cz/en/docs/web-apps/chat-ai

# %% [markdown]
# ## What You Will Learn
#
# - How to authenticate with Open WebUI Chat API
# - How to list available AI models
# - How to send chat completion requests
# - How to handle streaming and non-streaming responses
# - How to manage API errors and rate limits
# - Best practices for prompt engineering in notebooks

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - Access to e-INFRA CZ AI services
# - API token for Open WebUI

# %% [markdown]
# ### Where to Get Credentials
#
# 1. Visit https://llm.ai.e-infra.cz/
# 2. Log in with your e-INFRA credentials
# 3. Navigate to Settings → Account → API Keys
# 4. Create a new API key
# 5. Copy the generated token (you can't view it again!)

# %% [markdown]
# ### Required Environment Variables
#
# Add these to your `.env` file:
#
# ```bash
# EINFRA_AI_BASE_URL=https://llm.ai.e-infra.cz/v1
# EINFRA_AI_TOKEN=your_api_token_here
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install -e ".[openwebui]"
# ```
#
# Run once from the repo root, from a terminal (not from inside a notebook cell).
#
# **Note**: We use the `openai` package because Open WebUI provides an OpenAI-compatible API.

# %% [markdown]
# ## Setup

# %% [markdown]
# ### Locate `mcnb`
#
# Adds the repo's `src/` to the path if `mcnb` isn't already installed —
# no install, no restart.

# %%
import importlib.util as _importlib_util
from pathlib import Path as _Path

def _find_repo_root():
    """Walk up from CWD searching for pyproject.toml or .git marker."""
    start = _Path().resolve()
    for candidate in [start] + list(start.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return None

if _importlib_util.find_spec("mcnb") is None:
    # Not installed — try adding the repo's src/ to sys.path (no install, no restart).
    import sys as _sys
    _repo_root = _find_repo_root()
    for _p in ([_repo_root / "src"] if _repo_root else []) + [_Path("src"), _Path("../src")]:
        if (_p / "mcnb").exists():
            _sys.path.insert(0, str(_p.resolve()))
            break
    if _importlib_util.find_spec("mcnb") is None:
        raise ImportError(
            "Cannot find mcnb. Either:\n"
            "  1. Run this notebook from within the cloned repository\n"
            "  2. Or install it explicitly: pip install -e /path/to/this/repo"
        )
    print("✓ mcnb found via sys.path (no install needed)")
else:
    print("✓ mcnb installed")

# %% [markdown]
# ### Dependency Check
#
# This only *checks* that dependencies are importable — it never installs
# anything on its own. If something is missing, it tells you the exact
# command to run yourself in a terminal.

# %%
from mcnb.util import require_deps

require_deps({"python-dotenv": "dotenv", "openai": "openai"}, extra="openwebui")
print("✓ Dependencies available")

try:
    from IPython import get_ipython as _get_ipython
    _ip = _get_ipython()
    if _ip is not None:
        _ip.run_line_magic("load_ext", "autoreload")
        _ip.run_line_magic("autoreload", "2")
        print("✓ autoreload enabled")
except Exception:
    pass

from mcnb.env import need, optional, mask
from mcnb.util import print_section, fmt_error
print("✓ mcnb imported")

from openai import OpenAI
import openai
import json
print("✓ openai imported")

# %% [markdown]
# ### Validate Environment Variables

# %%
print_section("Validating Credentials")

try:
    EINFRA_AI_BASE_URL = optional("EINFRA_AI_BASE_URL", "https://llm.ai.e-infra.cz/v1")
    EINFRA_AI_TOKEN = need("EINFRA_AI_TOKEN")
    
    print("✓ All required environment variables found")
    print(f"\nBase URL: {EINFRA_AI_BASE_URL}")
    print(f"API Token: {mask(EINFRA_AI_TOKEN)}")
    
except RuntimeError as e:
    print(f"✗ Missing environment variable: {e}")
    print("\nPlease configure your .env file with:")
    print("  EINFRA_AI_BASE_URL=https://llm.ai.e-infra.cz/v1")
    print("  EINFRA_AI_TOKEN=your_api_token")
    print("\nSee: https://docs.cerit-sc.cz/en/docs/web-apps/chat-ai")
    raise

# %% [markdown]
# ### Create API Client

# %%
print_section("Creating API Client")

try:
    client = OpenAI(
        base_url=EINFRA_AI_BASE_URL,
        api_key=EINFRA_AI_TOKEN,
    )
    
    print("✓ OpenAI client configured successfully")
    print("  (Using OpenAI-compatible API)")
    
except Exception as e:
    print(fmt_error(e, label="create OpenAI client"))
    raise

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. List Available Models

# %%
print_section("Listing Available Models")

try:
    models = client.models.list()
    model_list = list(models)
    
    if model_list:
        print(f"✓ Found {len(model_list)} model(s)\n")
        
        print("Available models:")
        for i, model in enumerate(model_list, 1):
            model_id = model.id
            print(f"  {i:2}. {model_id}")
        
        # Store first model for later use
        DEFAULT_MODEL = model_list[0].id
        print(f"\nUsing '{DEFAULT_MODEL}' as default for this demo")
    else:
        print("⚠️  No models found")
        print("  This may indicate an authentication or permission issue")
        DEFAULT_MODEL = None
        
except openai.AuthenticationError as e:
    print(fmt_error(e, label="list models — authentication"))
    print("  Your API token is invalid or expired. Generate a new one.")
    DEFAULT_MODEL = None
    raise
except openai.APIConnectionError as e:
    print(fmt_error(e, label="list models — connection"))
    print("  Cannot reach the API endpoint. Check EINFRA_AI_BASE_URL and network.")
    DEFAULT_MODEL = None
    raise
except openai.APIError as e:
    print(fmt_error(e, label="list models — API error"))
    DEFAULT_MODEL = None
    raise
except Exception as e:
    print(fmt_error(e, label="list models"))
    print("\nCommon causes:")
    print("  - Invalid API token")
    print("  - Token expired")
    print("  - Network connectivity issues")
    print("  - Wrong base URL")
    DEFAULT_MODEL = None
    raise

# %% [markdown]
# ### 2. Simple Chat Completion

# %%
print_section("Simple Chat Completion")

if DEFAULT_MODEL is None:
    print("⚠️  Skipping - no model available")
else:
    try:
        # Simple test prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant running in a Jupyter notebook on MetaCentrum."
            },
            {
                "role": "user",
                "content": "Hello! Can you confirm you're working? Please respond in one short sentence."
            }
        ]
        
        print(f"Sending request to model: {DEFAULT_MODEL}")
        print(f"Prompt: {messages[-1]['content']}\n")
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
        )

        # Extract response defensively
        if not response.choices:
            print("✗ Chat completion returned empty choices list")
            print(f"  Full response: {response}")
        else:
            try:
                answer = response.choices[0].message.content
            except (IndexError, AttributeError) as e:
                print(fmt_error(e, label="extract response content"))
                print(f"  Raw choices: {response.choices}")
                raise

            print("✓ Chat completion successful!\n")
            print("Response:")
            print("-" * 60)
            print(answer)
            print("-" * 60)

            # Show usage statistics
            if hasattr(response, 'usage') and response.usage:
                print(f"\nToken usage:")
                print(f"  Prompt tokens: {response.usage.prompt_tokens}")
                print(f"  Completion tokens: {response.usage.completion_tokens}")
                print(f"  Total tokens: {response.usage.total_tokens}")

    except openai.AuthenticationError as e:
        print(fmt_error(e, label="chat completion — authentication"))
        print("  Your API token is invalid or expired.")
        raise
    except openai.RateLimitError as e:
        print(fmt_error(e, label="chat completion — rate limit"))
        print("  You have exceeded the API rate limit. Wait and retry.")
        raise
    except openai.APIConnectionError as e:
        print(fmt_error(e, label="chat completion — connection"))
        raise
    except openai.APIError as e:
        print(fmt_error(e, label="chat completion — API error"))
        raise
    except Exception as e:
        print(fmt_error(e, label="chat completion"))
        print("\nCommon causes:")
        print("  - Model not available")
        print("  - Rate limit exceeded")
        print("  - Invalid parameters")
        raise

# %% [markdown]
# ### 3. Multi-turn Conversation

# %%
print_section("Multi-turn Conversation")

if DEFAULT_MODEL is None:
    print("⚠️  Skipping - no model available")
else:
    try:
        # Conversation history
        conversation = [
            {
                "role": "system",
                "content": "You are a helpful data science assistant."
            },
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ]
        
        # First exchange
        try:
            response1 = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=conversation,
                max_tokens=50,
            )
            if not response1.choices:
                print("✗ Turn 1: empty choices returned")
                raise ValueError("No choices in response")
            answer1 = response1.choices[0].message.content
        except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
            print(fmt_error(e, label="multi-turn turn 1"))
            raise
        except (IndexError, AttributeError) as e:
            print(fmt_error(e, label="multi-turn turn 1 — parse response"))
            raise

        conversation.append({"role": "assistant", "content": answer1})

        print("Turn 1:")
        print(f"  User: {conversation[1]['content']}")
        print(f"  Assistant: {answer1}\n")

        # Follow-up question
        conversation.append({
            "role": "user",
            "content": "What is its population?"
        })

        try:
            response2 = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=conversation,
                max_tokens=50,
            )
            if not response2.choices:
                print("✗ Turn 2: empty choices returned")
                raise ValueError("No choices in response")
            answer2 = response2.choices[0].message.content
        except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
            print(fmt_error(e, label="multi-turn turn 2"))
            raise
        except (IndexError, AttributeError) as e:
            print(fmt_error(e, label="multi-turn turn 2 — parse response"))
            raise

        print("Turn 2:")
        print(f"  User: {conversation[-1]['content']}")
        print(f"  Assistant: {answer2}")

        print("\n✓ Multi-turn conversation demonstrated successfully")

    except openai.AuthenticationError as e:
        print(fmt_error(e, label="multi-turn conversation — authentication"))
    except openai.RateLimitError as e:
        print(fmt_error(e, label="multi-turn conversation — rate limit"))
    except openai.APIError as e:
        print(fmt_error(e, label="multi-turn conversation — API error"))
    except Exception as e:
        print(fmt_error(e, label="multi-turn conversation"))

# %% [markdown]
# ### 4. Code Generation Example

# %%
print_section("Code Generation Example")

if DEFAULT_MODEL is None:
    print("⚠️  Skipping - no model available")
else:
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a Python programming assistant. Provide clean, commented code."
            },
            {
                "role": "user",
                "content": "Write a Python function to calculate the factorial of a number using recursion. Keep it simple."
            }
        ]
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.3,  # Lower temperature for more deterministic code
        )
        
        if not response.choices:
            print("✗ Code generation returned empty choices list")
            print(f"  Full response: {response}")
        else:
            try:
                code = response.choices[0].message.content
            except (IndexError, AttributeError) as e:
                print(fmt_error(e, label="extract code from response"))
                print(f"  Raw choices: {response.choices}")
                raise

            print("✓ Code generated successfully\n")
            print("Generated code:")
            print("=" * 60)
            print(code)
            print("=" * 60)

    except openai.APIError as e:
        print(fmt_error(e, label="code generation — API error"))
    except openai.APIConnectionError as e:
        print(fmt_error(e, label="code generation — connection"))
    except Exception as e:
        print(fmt_error(e, label="code generation"))

# %% [markdown]
# ### 5. Streaming Response (Optional)

# %%
print_section("Streaming Response Demo")

if DEFAULT_MODEL is None:
    print("⚠️  Skipping - no model available")
else:
    try:
        messages = [
            {
                "role": "user",
                "content": "Count from 1 to 5, one number per line."
            }
        ]
        
        print("Streaming response:\n")
        
        stream = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=50,
            stream=True,  # Enable streaming
        )
        
        full_response = ""
        for chunk in stream:
            try:
                if not chunk.choices:
                    continue
                delta_content = chunk.choices[0].delta.content
                if delta_content is not None:
                    full_response += delta_content
                    print(delta_content, end='', flush=True)
            except (IndexError, AttributeError) as e:
                print(f"\n⚠️  Chunk parse error: {fmt_error(e)} — skipping chunk")
                continue

        print("\n\n✓ Streaming completed")
        if not full_response:
            print("⚠️  No content received in stream — model may not support streaming")

    except openai.APIError as e:
        print(fmt_error(e, label="streaming — API error"))
        print("  Note: Streaming may not be supported by all models")
    except openai.APIConnectionError as e:
        print(fmt_error(e, label="streaming — connection"))
    except Exception as e:
        print(fmt_error(e, label="streaming"))
        print("  Note: Streaming may not be supported by all models")

# %% [markdown]
# ### 6. Error Handling Example

# %%
print_section("Error Handling Demo")

print("Attempting to use a non-existent model...\n")

try:
    response = client.chat.completions.create(
        model="definitely-not-a-real-model-12345",
        messages=[{"role": "user", "content": "test"}],
    )
    print("Unexpected: Request succeeded")
    
except Exception as e:
    print(f"✓ Error caught successfully (as expected)\n")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nThis demonstrates proper error handling in production code.")

# %% [markdown]
# ## Cleanup
#
# No cleanup needed - API calls are stateless and don't create persistent resources.

# %%
print_section("Cleanup")

print("✓ No cleanup needed - API calls are stateless")
print("\n⚠️  Best practices:")
print("  - Monitor your API usage and costs")
print("  - Use appropriate max_tokens to avoid waste")
print("  - Implement rate limiting for production use")
print("  - Cache responses when appropriate")

# %% [markdown]
# ## Troubleshooting
#
# ### Common Errors
#
# **401 Unauthorized / Authentication Error**
# - Invalid API token
# - Token expired
# - Token not properly formatted in request
# - Generate a new token from the web interface
#
# **404 Model Not Found**
# - Model name misspelled
# - Model not available in your region
# - Model deprecated or removed
# - Use `client.models.list()` to see available models
#
# **429 Rate Limit Exceeded**
# - Too many requests in short time
# - Implement exponential backoff
# - Add delays between requests
# - Check your quota limits
#
# **400 Bad Request**
# - Invalid parameters (e.g., negative max_tokens)
# - Malformed message format
# - Prompt too long for model context
# - Check API documentation for parameter limits
#
# **Connection / Network Errors**
# - Cannot reach API endpoint
# - Firewall blocking requests
# - VPN required?
# - Check base URL is correct

# %% [markdown]
# ### Response Quality Issues
#
# **Model gives poor/wrong answers**
# - Try different model
# - Adjust temperature (lower = more deterministic)
# - Improve system prompt
# - Provide more context in user messages
#
# **Responses cut off mid-sentence**
# - Increase `max_tokens`
# - Model hit its output limit
# - Some models have hard token limits
#
# **Slow responses**
# - Large models are slower
# - High server load
# - Try smaller/faster model
# - Use streaming for better UX

# %% [markdown]
# ### Debugging Tips
#
# ```python
# # Check client configuration
# print(f"Base URL: {client.base_url}")
#
# # Enable verbose error messages
# import logging
# logging.basicConfig(level=logging.DEBUG)
#
# # Test with minimal request
# try:
#     response = client.chat.completions.create(
#         model=DEFAULT_MODEL,
#         messages=[{"role": "user", "content": "hi"}],
#         max_tokens=5,
#     )
#     print("Success!")
# except Exception as e:
#     print(f"Failed: {e}")
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand the Chat API basics, you can:
#
# ### Advanced Usage
#
# - **Function calling** - Let models call your Python functions
# - **RAG (Retrieval Augmented Generation)** - Combine with document search
# - **Agents** - Build autonomous task executors
# - **Fine-tuning** - Customize models for your use case (if supported)
# - **Embeddings** - Generate vector representations for semantic search

# %% [markdown]
# ### Integration Ideas
#
# - **Data analysis assistant** - Generate pandas/SQL code from natural language
# - **Report generation** - Automatically summarize computational results
# - **Code review** - Get AI feedback on generated code
# - **Documentation** - Auto-generate docstrings and README content
# - **Experiment planning** - Brainstorm research ideas

# %% [markdown]
# ### Best Practices
#
# **Prompt Engineering**
# - Use clear, specific instructions
# - Provide examples (few-shot learning)
# - Break complex tasks into steps
# - Iterate on prompts based on results
#
# **Cost Management**
# - Set appropriate max_tokens limits
# - Use smaller models when sufficient
# - Cache common responses
# - Monitor usage regularly
#
# **Safety & Ethics**
# - Validate AI-generated code before execution
# - Don't send sensitive data to external APIs
# - Be aware of model biases
# - Follow usage policies

# %% [markdown]
# ### Related Notebooks
#
# - **05_gpu_container_ai_model.ipynb** - Run local models with GPU
# - **02_invenio_repository.ipynb** - Archive AI-generated results

# %% [markdown]
# ### Documentation
#
# - [CERIT-SC Chat AI Docs](https://docs.cerit-sc.cz/en/docs/web-apps/chat-ai)
# - [OpenAI Python SDK](https://github.com/openai/openai-python)
# - [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
# - [Prompt Engineering Guide](https://www.promptingguide.ai/)
