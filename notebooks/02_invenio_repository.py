# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 02 - Invenio Repository Integration (EOSC CZ / NRP)
#
# ## Goal
#
# Demonstrate authentication and basic operations with the National Repository Platform (NRP) using the Invenio REST API. This notebook shows how to authenticate, validate access, create draft records, upload files, and handle common API errors.
#
# **Runtime**: ~2-3 minutes
#
# **Documentation**: https://data.narodni-repozitar.cz/

# %% [markdown]
# ## What You Will Learn
#
# - How to authenticate with Invenio REST API using personal access tokens
# - How to validate API access and check permissions
# - How to create draft records programmatically
# - How to upload files to draft records
# - How to handle common API errors and permission issues
# - How to clean up draft records

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - An account on https://data.narodni-repozitar.cz/
# - A personal access token with appropriate permissions

# %% [markdown]
# ### Where to Get Credentials
#
# 1. Visit https://data.narodni-repozitar.cz/
# 2. Log in with your credentials
# 3. Navigate to your account settings / Applications
# 4. Create a new personal access token
# 5. Select appropriate scopes (deposit:write, deposit:actions)
# 6. Copy the generated token

# %% [markdown]
# ### Required Environment Variables
#
# Add these to your `.env` file:
#
# ```bash
# NRP_BASE=https://data.narodni-repozitar.cz
# NRP_TOKEN=your_personal_access_token_here
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install --user requests python-dotenv
# ```

# %% [markdown]
# ## Setup

# %% [markdown]
# ### Dependency Bootstrap

# %%
import subprocess as _subprocess, sys as _sys
_DEPS = {"python-dotenv": "dotenv", "requests": "requests"}
_restart_needed = False
for _pip_name, _import_name in _DEPS.items():
    try:
        __import__(_import_name)
    except ImportError:
        print(f"Installing {_pip_name}...")
        try:
            _subprocess.check_call([_sys.executable, "-m", "pip", "install", "--user", _pip_name])
            _restart_needed = True
        except _subprocess.CalledProcessError:
            print(f"✗ Failed to install {_pip_name}. Run manually: pip install --user {_pip_name}")
            raise SystemExit(1)
if _restart_needed:
    print("\n⚠  Restart kernel and re-run from the top.")
else:
    print("✓ Dependencies available")

# %%
import sys as _sys, subprocess as _subprocess, importlib.util as _importlib_util
from pathlib import Path as _Path

def _find_repo_root():
    """Walk up from CWD searching for pyproject.toml or .git marker."""
    start = _Path().resolve()
    for candidate in [start] + list(start.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return None

if _importlib_util.find_spec("mcnb") is None:
    _repo_root = _find_repo_root()
    if _repo_root and (_repo_root / "src" / "mcnb").exists():
        print(f"Installing mcnb from {_repo_root} ...")
        _subprocess.check_call(
            [_sys.executable, "-m", "pip", "install", "--user", "-e", str(_repo_root)],
            stdout=_subprocess.DEVNULL,
        )
        print("⚠  mcnb installed — please restart the kernel and re-run from the top.")
        raise SystemExit(0)
    elif _repo_root:
        _sys.path.insert(0, str(_repo_root / "src"))
    else:
        for _p in ["src", "../src"]:
            _sys.path.insert(0, str(_Path(_p).resolve()))
    if _importlib_util.find_spec("mcnb") is None:
        raise ImportError(
            "Cannot find mcnb. Either:\n"
            "  1. pip install --user -e /path/to/this/repo  (persistent)\n"
            "  2. Upload src/ to your JupyterHub home directory"
        )
    print("✓ mcnb found via sys.path")
else:
    print("✓ mcnb installed")

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
from mcnb.util import print_section, fmt_error, safe_get
print("✓ mcnb imported")

try:
    import requests
    import json
    from datetime import datetime
    print("✓ requests imported")
except ImportError as e:
    print(f"✗ ImportError: {e}")
    print("  Run: pip install requests")
    raise

# %% [markdown]
# ### Validate Environment Variables

# %%
print_section("Validating Credentials")

try:
    NRP_BASE = optional("NRP_BASE", "https://data.narodni-repozitar.cz")
    NRP_TOKEN = need("NRP_TOKEN")
    
    print("✓ All required environment variables found")
    print(f"\nBase URL: {NRP_BASE}")
    print(f"Token: {mask(NRP_TOKEN)}")
    
except RuntimeError as e:
    print(f"✗ Missing environment variable: {e}")
    print("\nPlease configure your .env file with:")
    print("  NRP_BASE=https://data.narodni-repozitar.cz")
    print("  NRP_TOKEN=your_personal_access_token")
    print("\nSee: https://data.narodni-repozitar.cz/")
    raise

# %% [markdown]
# ### Create API Client Helper

# %%
print_section("Setting Up API Client")

# Create session with authentication
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {NRP_TOKEN}",
    "Content-Type": "application/json",
})

print("✓ API client configured successfully")

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. Validate API Access

# %%
print_section("Validating API Access")

try:
    # Try to list user's records (requires authentication)
    response = session.get(f"{NRP_BASE}/api/user/records", timeout=30)

    if response.status_code == 200:
        print("✓ Authentication successful!")
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(fmt_error(e, label="parse JSON response"))
            print(f"  Raw response (first 500 chars): {response.text[:500]}")
            raise

        hits = data.get("hits", {})
        total = hits.get("total", 0)

        print(f"\nYou have {total} record(s) in the repository")

        if total > 0:
            print("\nRecent records:")
            for record in hits.get("hits", [])[:3]:
                metadata = record.get("metadata", {})
                title = metadata.get("title", "Untitled")
                record_id = record.get("id", "N/A")
                print(f"  - [{record_id}] {title}")
    else:
        print(f"✗ Authentication failed (HTTP {response.status_code})")
        print(f"  Response: {response.text}")

except requests.exceptions.ConnectionError as e:
    print(fmt_error(e, label="API connection"))
    print("  Could not reach the server. Check network connectivity and NRP_BASE URL.")
    raise
except requests.exceptions.Timeout as e:
    print(fmt_error(e, label="API timeout"))
    print("  Request timed out after 30s. The server may be unreachable or slow.")
    raise
except requests.exceptions.RequestException as e:
    print(fmt_error(e, label="API request"))
    print("\nCommon causes:")
    print("  - Invalid token")
    print("  - Token expired")
    print("  - Network connectivity issues")
    print("  - Wrong base URL")
    raise

# %% [markdown]
# ### 2. Create a Draft Record

# %%
print_section("Creating Draft Record")

# Minimal metadata for a draft record
draft_metadata = {
    "metadata": {
        "title": f"Test Record from Jupyter Notebook - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "resource_type": {"id": "dataset"},
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Jupyter User",
                    "family_name": "User",
                    "given_name": "Jupyter"
                }
            }
        ],
        "publisher": "MetaCentrum Testing",
        "publication_date": datetime.now().strftime("%Y-%m-%d"),
    }
}

try:
    response = session.post(
        f"{NRP_BASE}/api/records",
        json=draft_metadata,
        timeout=30,
    )

    if response.status_code in [201, 200]:
        try:
            draft = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(fmt_error(e, label="parse create-draft response"))
            print(f"  Raw response: {response.text}")
            DRAFT_ID = None
            DRAFT_DATA = None
            raise

        draft_id = draft.get("id")
        draft_link = draft.get("links", {}).get("self", "N/A")

        print("✓ Draft record created successfully!")
        print(f"\nDraft ID: {draft_id}")
        print(f"Draft URL: {draft_link}")

        # Store for later use
        DRAFT_ID = draft_id
        DRAFT_DATA = draft

    else:
        print(f"✗ Failed to create draft (HTTP {response.status_code})")
        print(f"  Response: {response.text}")

        # Set to None so cleanup doesn't fail
        DRAFT_ID = None
        DRAFT_DATA = None

        if response.status_code == 403:
            print("\n⚠️  Permission denied. Your token may not have deposit:write scope.")
        elif response.status_code == 422:
            print("\n⚠️  Validation error. Check the metadata fields.")

except requests.exceptions.ConnectionError as e:
    print(fmt_error(e, label="create draft — connection"))
    DRAFT_ID = None
    DRAFT_DATA = None
    raise
except requests.exceptions.Timeout as e:
    print(fmt_error(e, label="create draft — timeout"))
    DRAFT_ID = None
    DRAFT_DATA = None
    raise
except requests.exceptions.RequestException as e:
    print(fmt_error(e, label="create draft"))
    DRAFT_ID = None
    DRAFT_DATA = None
    raise

# %% [markdown]
# ### 3. Upload a File to Draft Record

# %%
print_section("Uploading File to Draft")

if DRAFT_ID is None:
    print("⚠️  Skipping file upload - no draft record available")
else:
    try:
        # Create a test file content
        file_content = f"""Test file from MetaCentrum Jupyter Notebook
Generated at: {datetime.now()}
Draft ID: {DRAFT_ID}

This is a minimal working demo of the Invenio repository API.
"""
        
        file_name = "test_file.txt"
        
        # Start file upload
        files_link = DRAFT_DATA.get("links", {}).get("files", f"{NRP_BASE}/api/records/{DRAFT_ID}/files")
        
        # Initialize file upload
        try:
            init_response = session.post(
                files_link,
                json=[{"key": file_name}],
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(fmt_error(e, label="file upload init"))
            raise

        if init_response.status_code not in [200, 201]:
            print(f"✗ File initialization failed (HTTP {init_response.status_code})")
            print(f"  Response: {init_response.text}")
            raise RuntimeError(f"File init failed with HTTP {init_response.status_code}")

        print(f"✓ File upload initialized: {file_name}")

        try:
            file_info = init_response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(fmt_error(e, label="parse file-init response"))
            print(f"  Raw response: {init_response.text}")
            raise

        entries = file_info.get("entries", [])
        if not entries:
            print("✗ No upload entries returned from file init")
            print(f"  Full response: {file_info}")
            raise RuntimeError("No upload entries returned")

        upload_link = entries[0].get("links", {}).get("content")
        if not upload_link:
            print("✗ No content upload link in response")
            print(f"  Entry links: {entries[0].get('links', {})}")
            raise RuntimeError("Missing content upload link")

        # Upload file content
        try:
            upload_response = session.put(
                upload_link,
                data=file_content.encode('utf-8'),
                headers={"Content-Type": "application/octet-stream"},
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(fmt_error(e, label="file content upload"))
            raise

        if upload_response.status_code not in [200, 201]:
            print(f"✗ File upload failed (HTTP {upload_response.status_code})")
            print(f"  Response: {upload_response.text}")
            raise RuntimeError(f"Content upload failed with HTTP {upload_response.status_code}")

        print(f"✓ File content uploaded successfully")
        print(f"  Size: {len(file_content)} bytes")

        # Commit the file
        commit_link = entries[0].get("links", {}).get("commit")
        if not commit_link:
            print("✗ No commit link in response — cannot finalize file")
            print(f"  Entry links: {entries[0].get('links', {})}")
            raise RuntimeError("Missing commit link")

        try:
            commit_response = session.post(commit_link, timeout=30)
        except requests.exceptions.RequestException as e:
            print(fmt_error(e, label="file commit"))
            raise

        if commit_response.status_code in [200, 201]:
            print(f"✓ File committed to draft")
        else:
            print(f"⚠️  File commit returned HTTP {commit_response.status_code}")
            print(f"  Response: {commit_response.text}")

    except requests.exceptions.RequestException as e:
        print(fmt_error(e, label="file upload"))
    except RuntimeError:
        pass  # already printed above
    except Exception as e:
        print(fmt_error(e, label="file upload — unexpected error"))

# %% [markdown]
# ### 4. Retrieve Draft Record Details

# %%
print_section("Retrieving Draft Details")

if DRAFT_ID is None:
    print("⚠️  Skipping - no draft record available")
else:
    try:
        response = session.get(f"{NRP_BASE}/api/records/{DRAFT_ID}/draft", timeout=30)

        if response.status_code == 200:
            try:
                draft = response.json()
            except requests.exceptions.JSONDecodeError as e:
                print(fmt_error(e, label="parse draft details response"))
                print(f"  Raw response: {response.text}")
                raise

            metadata = draft.get("metadata", {})

            print("✓ Draft record retrieved successfully")
            print(f"\nMetadata:")
            print(f"  Title: {metadata.get('title', 'N/A')}")
            print(f"  Resource Type: {metadata.get('resource_type', {}).get('id', 'N/A')}")
            print(f"  Publication Date: {metadata.get('publication_date', 'N/A')}")

            # List files
            files = draft.get("files", {}).get("entries", [])
            if files:
                print(f"\n  Files ({len(files)}):")
                for f in files:
                    print(f"    - {f.get('key', 'N/A')} ({f.get('size', 0)} bytes)")
            else:
                print("\n  No files attached")
        else:
            print(f"✗ Failed to retrieve draft (HTTP {response.status_code})")
            print(f"  Response: {response.text}")

    except requests.exceptions.ConnectionError as e:
        print(fmt_error(e, label="retrieve draft — connection"))
    except requests.exceptions.Timeout as e:
        print(fmt_error(e, label="retrieve draft — timeout"))
    except requests.exceptions.RequestException as e:
        print(fmt_error(e, label="retrieve draft"))
    except Exception as e:
        print(fmt_error(e, label="retrieve draft — unexpected"))

# %% [markdown]
# ### 5. Check Available Actions

# %%
print_section("Available Actions")

if DRAFT_DATA is None:
    print("⚠️  Skipping - no draft record available")
else:
    links = DRAFT_DATA.get("links", {})
    
    print("Available API endpoints for this draft:\n")
    
    important_links = ["self", "files", "publish", "edit", "versions"]
    
    for key in important_links:
        if key in links:
            print(f"  ✓ {key:12} : {links[key]}")
        else:
            print(f"  ✗ {key:12} : Not available")
    
    print("\n⚠️  Note: Publishing requires additional permissions and validation.")
    print("    This demo creates and manages drafts only.")

# %% [markdown]
# ## Cleanup
#
# Delete the draft record we created:

# %%
print_section("Cleanup: Deleting Draft Record")

if DRAFT_ID is None:
    print("⚠️  No draft to clean up")
else:
    try:
        response = session.delete(f"{NRP_BASE}/api/records/{DRAFT_ID}/draft", timeout=30)

        if response.status_code in [204, 200]:
            print(f"✓ Draft record deleted: {DRAFT_ID}")

            # Verify deletion
            try:
                verify = session.get(f"{NRP_BASE}/api/records/{DRAFT_ID}/draft", timeout=30)
                if verify.status_code == 404:
                    print("✓ Deletion verified")
                else:
                    print(f"⚠️  Draft might still exist (HTTP {verify.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Could not verify deletion: {fmt_error(e)}")
        else:
            print(f"✗ Failed to delete draft (HTTP {response.status_code})")
            print(f"  Response: {response.text}")
            print("\n  You may need to delete it manually from the web interface.")

    except requests.exceptions.ConnectionError as e:
        print(fmt_error(e, label="cleanup — connection"))
        print("  You may need to delete the draft manually.")
    except requests.exceptions.Timeout as e:
        print(fmt_error(e, label="cleanup — timeout"))
        print("  You may need to delete the draft manually.")
    except requests.exceptions.RequestException as e:
        print(fmt_error(e, label="cleanup"))
        print("  You may need to delete the draft manually.")
    except Exception as e:
        print(fmt_error(e, label="cleanup — unexpected"))
        print("  You may need to delete the draft manually.")

# %% [markdown]
# ## Troubleshooting
#
# ### Common Errors
#
# **401 Unauthorized**
# - Token is invalid or expired
# - Token not included in request headers
# - Generate a new token from your account settings
#
# **403 Forbidden**
# - Token doesn't have required permissions
# - Check token scopes (need deposit:write, deposit:actions)
# - Regenerate token with correct permissions
#
# **400 Bad Request**
# - Invalid metadata format
# - Missing required fields
# - Check error message for specific validation issues
#
# **404 Not Found**
# - Draft ID doesn't exist
# - Draft was already deleted or published
# - Wrong base URL
#
# **422 Unprocessable Entity**
# - Metadata validation failed
# - Required fields missing or invalid format
# - Check Invenio schema requirements

# %% [markdown]
# ### Permission Issues
#
# If you can't create drafts:
# - Verify your account is activated
# - Check if you have deposit permissions
# - Contact repository administrators
#
# If you can't publish:
# - Publishing may require additional review/approval
# - Some repositories restrict publishing to specific users
# - Use the web interface to understand requirements

# %% [markdown]
# ### Debugging Tips
#
# ```python
# # Enable verbose logging
# import logging
# logging.basicConfig(level=logging.DEBUG)
#
# # Check API response in detail
# response = session.get(f"{NRP_BASE}/api/user/records")
# print(f"Status: {response.status_code}")
# print(f"Headers: {response.headers}")
# print(f"Body: {response.text}")
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand Invenio repository basics, you can:
#
# ### Advanced Operations
#
# - **Complete metadata** - Add descriptions, keywords, licenses
# - **Multiple files** - Upload datasets with many files
# - **Versioning** - Create new versions of published records
# - **Communities** - Submit to specific communities
# - **Access control** - Set embargo dates or restricted access

# %% [markdown]
# ### Integration Ideas
#
# - Automatically deposit research outputs
# - Archive computation results from notebooks
# - Create datasets from analysis workflows
# - Link with S3 storage for large files

# %% [markdown]
# ### Related Notebooks
#
# - **01_s3_object_storage.ipynb** - Store large files, then link in Invenio
# - **05_gpu_container_ai_model.ipynb** - Archive model outputs

# %% [markdown]
# ### Documentation
#
# - [National Repository Platform](https://data.narodni-repozitar.cz/)
# - [Invenio RDM Documentation](https://inveniordm.docs.cern.ch/)
# - [InvenioRDM REST API](https://inveniordm.docs.cern.ch/reference/rest_api_index/)
