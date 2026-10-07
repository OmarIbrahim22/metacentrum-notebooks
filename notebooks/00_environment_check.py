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
# # 00 - Environment Check & Diagnostics
#
# ## Goal
#
# This notebook confirms your runtime environment (local vs MetaCentrum/e-INFRA), basic tools, GPU presence, Python version, and filesystem paths. Use this as a baseline diagnostic before running other notebooks.
#
# **Runtime**: ~1-2 minutes

# %% [markdown]
# ## What You Will Learn
#
# - How to detect your runtime environment
# - How to check Python version and OS information
# - How to verify GPU availability
# - How to use shared helper utilities from `mcnb` package
# - Basic filesystem and path information

# %% [markdown]
# ## Prerequisites
#
# **No credentials required** - this notebook runs without any API keys or tokens.
#
# ### Access Requirements
#
# - Python 3.8+
# - Jupyter environment (local, ondemand.metacentrum.cz, or jupyter.e-infra.cz)

# %% [markdown]
# ### Installation (if running locally)
#
# ```bash
# pip install -e .
# ```
#
# Run once from the repo root, from a terminal (not from inside a notebook cell).

# %% [markdown]
# ## Setup
#
# ### Locate `mcnb`
#
# Adds the repo's `src/` to the path if `mcnb` isn't already installed —
# no install, no restart.

# %%
import sys
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
    _repo_root = _find_repo_root()
    for _p in ([_repo_root / "src"] if _repo_root else []) + [_Path("src"), _Path("../src")]:
        if (_p / "mcnb").exists():
            sys.path.insert(0, str(_p.resolve()))
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
# This only *checks* that `python-dotenv` is importable — it never installs
# anything on its own. If something is missing, it tells you the exact
# command to run yourself in a terminal.

# %%
from mcnb.util import require_deps

require_deps({"python-dotenv": "dotenv"})
print("✓ All core dependencies available")

# %% [markdown]
# Import the rest of the shared utilities from the `mcnb` package:

# %%
try:
    from IPython import get_ipython as _get_ipython
    _ip = _get_ipython()
    if _ip is not None:
        _ip.run_line_magic("load_ext", "autoreload")
        _ip.run_line_magic("autoreload", "2")
        print("✓ autoreload enabled")
except Exception:
    pass

from mcnb.util import (
    detect_environment,
    format_env_report,
    check_gpu_available,
    print_section,
    fmt_error,
)
print("✓ mcnb imported")

# %% [markdown]
# ## Credential Setup
#
# Run this cell to configure your credentials interactively. They are saved to
# `~/.config/mcnb/env` and persist across kernel restarts and sessions.
#
# **Workshop / shared credentials:** upload a pre-filled `env.example` to the
# repo root, then run this cell — it will copy all values for you.
#
# **Personal credentials:** run this cell and type your own values when prompted.
#
# To reset: `rm ~/.config/mcnb/env` in a terminal, then re-run this cell.

# %%
from mcnb.env import setup_env

setup_env()

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. Environment Detection

# %%
print_section("Environment Detection")

try:
    env_info = detect_environment()
    print(format_env_report(env_info))
    if env_info.get("_error"):
        print(f"\n⚠️  Detection encountered an error: {env_info['_error']}")
except Exception as e:
    print(fmt_error(e, label="environment detection"))
    env_info = {}  # fallback so later cells can check safely

# %% [markdown]
# ### 2. Detailed Environment Information

# %%
import platform
import os

print_section("Detailed System Information")

try:
    print(f"Python version: {platform.python_version()}")
    print(f"Python implementation: {platform.python_implementation()}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"System: {platform.system()}")
    print(f"Node (hostname): {platform.node()}")
    print()
    print(f"Current working directory: {os.getcwd()}")
    print(f"Home directory: {os.path.expanduser('~')}")
    print(f"Python executable: {sys.executable}")
except Exception as e:
    print(fmt_error(e, label="system info"))

# %% [markdown]
# ### 3. GPU Check

# %%
print_section("GPU Availability Check")

try:
    gpu_info = check_gpu_available()

    if gpu_info["available"]:
        print("✓ GPU detected!")
        print("\nnvidia-smi output:")
        print(gpu_info["output"])
    else:
        print("✗ No GPU detected or nvidia-smi not available")
        print(f"\nDetails: {gpu_info['output']}")

    if gpu_info["devices"]:
        print(f"\nGPU devices found: {', '.join(gpu_info['devices'])}")
    else:
        print("\nNo /dev/nvidia* devices found")
except Exception as e:
    print(fmt_error(e, label="GPU check"))
    gpu_info = {"available": False, "output": "", "devices": []}

# %% [markdown]
# ### 4. Filesystem Check

# %%
import shutil

print_section("Filesystem and Disk Space")

# Check disk space
try:
    disk_usage = shutil.disk_usage(os.path.expanduser("~"))
    total_gb = disk_usage.total / (1024**3)
    used_gb = disk_usage.used / (1024**3)
    free_gb = disk_usage.free / (1024**3)

    print(f"Home directory disk space:")
    print(f"  Total: {total_gb:.2f} GB")
    print(f"  Used:  {used_gb:.2f} GB")
    print(f"  Free:  {free_gb:.2f} GB")
except (PermissionError, OSError) as e:
    print(fmt_error(e, label="disk usage"))
print()

# Check if common paths exist
common_paths = [
    "/storage",  # MetaCentrum
    "/auto",     # MetaCentrum auto-mounted homes
    "/tmp",
    os.path.expanduser("~"),
]

print("Common paths:")
for path in common_paths:
    try:
        exists = "✓" if os.path.exists(path) else "✗"
    except (PermissionError, OSError) as e:
        exists = f"? ({type(e).__name__})"
    print(f"  {exists} {path}")

# %% [markdown]
# ### 5. Python Environment Check

# %%
print_section("Python Environment")

# Check if running in virtual environment
in_venv = sys.prefix != sys.base_prefix
print(f"Running in virtual environment: {in_venv}")

if in_venv:
    print(f"  Virtual env path: {sys.prefix}")

# Check for IPython/Jupyter
try:
    import IPython
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython:
        print(f"✓ Running in IPython/Jupyter")
        print(f"  IPython version: {IPython.__version__}")
    else:
        print("Running in standard Python")
except ImportError:
    print("IPython not available")

# %% [markdown]
# ### 6. Environment Summary (PASS/FAIL Checklist)

# %%
print_section("Environment Summary")

# Build checklist
try:
    ver_tuple = platform.python_version_tuple()
    py38_ok = ver_tuple[0] == '3' and int(ver_tuple[1]) >= 8
except (IndexError, ValueError) as e:
    print(f"⚠️  Could not parse Python version tuple: {e}")
    py38_ok = False

checks = [
    ("Python 3.8+", py38_ok),
    ("Jupyter available", env_info.get('is_jupyter', False)),
    ("GPU available", gpu_info.get('available', False)),
    ("mcnb package accessible", True),  # If we got here, it's accessible
]

print("Status Checklist:")
print()
for check_name, passed in checks:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status:8} - {check_name}")

print()
all_critical_passed = checks[0][1] and checks[3][1]  # Python version and mcnb package
if all_critical_passed:
    print("🎉 Critical checks passed! Environment is ready.")
else:
    print("⚠️  Some critical checks failed. Please review above.")

# %% [markdown]
# ## Troubleshooting
#
# ### Common Issues
#
# **ModuleNotFoundError: No module named 'mcnb'**
# - Make sure you're running the notebook from inside the cloned repository
# - The setup cell searches upward for the repo root and adds its `src` directory to your Python path
# - Verify that `src/mcnb/util.py` and `src/mcnb/env.py` exist
# - Or install the package once from a terminal: `pip install -e .`
#
# **GPU not detected but you have one**
# - Check if nvidia drivers are installed: `nvidia-smi` should work in terminal
# - On MetaCentrum, you may need to request a GPU node explicitly
# - Some JupyterHub instances may not expose GPU by default
#
# **Platform detection says "No" for everything**
# - This is normal for local development
# - The detection heuristics are best-effort and may not match all configurations
# - As long as Python and Jupyter work, you're fine
#
# **Permission denied errors**
# - Some system paths may not be accessible
# - This is normal and won't affect most notebook functionality

# %% [markdown]
# ## Cleanup
#
# No cleanup needed - this notebook doesn't create any resources or files.

# %% [markdown]
# ## Next Steps
#
# Now that you've confirmed your environment is working, you can proceed to:
#
# 1. **01_s3_object_storage.ipynb** - Learn how to interact with S3 object storage
# 2. **04_open_webui_chat_api.ipynb** - Try the Open WebUI chat API (requires token)
# 3. **02_invenio_repository.ipynb** - Work with the EOSC CZ repository
#
# ### Customization Ideas
#
# - Add more environment-specific checks for your needs
# - Extend `detect_environment()` in `src/mcnb/util.py` with custom heuristics
# - Create a script version that runs automatically before other notebooks
