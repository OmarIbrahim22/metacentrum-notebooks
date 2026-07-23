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
# pip install --user python-dotenv
# ```

# %% [markdown]
# ## Dependency Bootstrap
#
# This cell installs `python-dotenv` if it is not already present.
# If it prints "restart needed", use **Kernel → Restart Kernel**, then re-run from the top.

# %%
import subprocess as _subprocess
import sys as _sys

_DEPS = {"python-dotenv": "dotenv"}
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
    print("\n⚠  Packages installed — please restart the kernel and re-run from the top.")
else:
    print("✓ All core dependencies available")

# %% [markdown]
# ## Setup
#
# Import the shared utilities from the `mcnb` package:

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
    str(Path.home()),
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
# - Make sure you're running the notebook from the repository root directory
# - The `sys.path.append` in the setup cell should add the `src` directory to your Python path
# - Verify that `src/mcnb/util.py` and `src/mcnb/env.py` exist
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
