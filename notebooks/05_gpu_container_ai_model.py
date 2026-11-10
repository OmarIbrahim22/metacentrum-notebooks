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
# # 05 - GPU and a Local AI Model
#
# ## Goal
#
# Use the GPU of your session directly from Python, then run a language model on that GPU and chat with it through the same OpenAI-compatible API as in notebook 04. On MetaCentrum OnDemand, the GPU requested for the Jupyter session is available inside the notebook, so no container is needed. Containers are covered as an optional last step, with a PBS job script for running them on a GPU node.
#
# **Runtime**: ~5 minutes on the first run (model download), ~1 minute afterwards
#
# **Note**: This notebook degrades gracefully: without a GPU, PyTorch, Ollama or a container runtime, the affected steps are skipped with instructions.

# %% [markdown]
# ## What You Will Learn
#
# - How to check that your session has a GPU
# - How to run a computation on the GPU with PyTorch and compare it with the CPU
# - How to run a language model on your own GPU with Ollama, without root or containers
# - How to talk to that model with the OpenAI client from notebook 04
# - When containers work from OnDemand, and how to run them from a PBS job instead

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - A GPU in your session: on OnDemand, choose a GPU when starting the Jupyter session; in a PBS job, request one with `#PBS -l select=1:ncpus=1:ngpus=1`
# - About 4 GB free in your home directory (Ollama plus a small model) and a few GB more for PyTorch

# %% [markdown]
# ### Install Ollama (once, no root needed)
#
# Run this in a terminal (on OnDemand: a terminal in the same session):
#
# ```bash
# mkdir -p ~/ollama
# python3 -m pip install pyzstd     # unpacks .tar.zst archives; OnDemand images have no zstd tool
# curl -fL -o ~/ollama.tar.zst https://ollama.com/download/ollama-linux-amd64.tar.zst
# python3 -m pyzstd -d ~/ollama.tar.zst --tar-output-dir ~/ollama
# rm ~/ollama.tar.zst                # the 1.5 GB download is no longer needed
# ~/ollama/bin/ollama --version
# ```
#
# Where the `zstd` tool is installed (`zstd --version`), `tar` can download and unpack
# in one step: `curl -fL https://ollama.com/download/ollama-linux-amd64.tar.zst | tar --zstd -x -C ~/ollama`
#
# The notebook finds Ollama on `PATH` or in `~/ollama/bin/`. It starts and stops the
# server itself.
#
# **Note**: OnDemand sessions can start with a different home directory setup; check
# that `~/ollama` and your Python packages are still there before a demo.

# %% [markdown]
# ### Optional Environment Variables
#
# Add these to your env file only if you want to change the defaults:
#
# ```bash
# LOCAL_LLM_MODEL=qwen2.5:1.5b    # any model from https://ollama.com/library
# OLLAMA_BIN=/path/to/ollama      # if Ollama is installed elsewhere
# CONTAINER_RUNTIME=apptainer     # preferred runtime for the optional step 6
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install -e ".[openwebui]"   # openai client, used to chat with the local model
# pip install torch               # PyTorch with CUDA (a few GB)
# ```
#
# Run once from the repo root, from a terminal (not from inside a notebook cell),
# then restart the kernel. Both are optional: steps that need a missing package are
# skipped with this hint.

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
# command to run yourself in a terminal. PyTorch and `openai` are optional
# here: the steps that need them are skipped with an install hint.

# %%
from mcnb.util import require_deps

require_deps({"python-dotenv": "dotenv"})
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

from mcnb.env import optional
from mcnb.util import print_section, check_gpu_available, run, fmt_error
print("✓ mcnb imported")

import importlib.util
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_OPENAI = importlib.util.find_spec("openai") is not None
print(f"PyTorch installed: {'yes' if HAS_TORCH else 'no (step 2 will be skipped)'}")
print(f"openai installed:  {'yes' if HAS_OPENAI else 'no (step 5 will be skipped)'}")

# %% [markdown]
# ### Load Configuration

# %%
print_section("Loading Configuration")

# Which model to run locally. Small models load in seconds and fit on any
# MetaCentrum GPU; see https://ollama.com/library for others.
LOCAL_LLM_MODEL = optional("LOCAL_LLM_MODEL", "qwen2.5:1.5b")

# Ollama binary: OLLAMA_BIN, else `ollama` on PATH, else ~/ollama/bin/ollama
# (where the install command in the Prerequisites puts it).
OLLAMA_BIN = optional("OLLAMA_BIN", None)
if not OLLAMA_BIN:
    _home_bin = os.path.expanduser("~/ollama/bin/ollama")
    OLLAMA_BIN = shutil.which("ollama") or (_home_bin if os.path.exists(_home_bin) else None)

CONTAINER_RUNTIME = optional("CONTAINER_RUNTIME", "apptainer")

print(f"Local model:       {LOCAL_LLM_MODEL}")
print(f"Ollama binary:     {OLLAMA_BIN or 'not found (steps 3-5 will be skipped)'}")
print(f"Container runtime: {CONTAINER_RUNTIME} (preference for the optional step 6)")

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. Check GPU Availability
#
# On OnDemand, a GPU requested for the session is visible directly inside the
# Jupyter session. No extra container is needed to use it.

# %%
print_section("Checking GPU Availability")

gpu_info = check_gpu_available()

if gpu_info["available"]:
    print("✓ GPU detected!\n")
    print("nvidia-smi output:")
    print("=" * 60)
    print(gpu_info["output"])
    print("=" * 60)

    GPU_AVAILABLE = True
else:
    print("✗ No GPU detected\n")
    print(f"Details: {gpu_info['output']}")
    print("\n⚠️  This notebook can still run but will use CPU mode")
    print("\nOn OnDemand, start the Jupyter session with a GPU (GPU field in the form).")
    print("In a PBS job, request one with:")
    print("  #PBS -l select=1:ncpus=1:ngpus=1")

    GPU_AVAILABLE = False

# Check for GPU devices
if gpu_info["devices"]:
    print(f"\nGPU devices found: {', '.join(gpu_info['devices'])}")
else:
    print("\nNo /dev/nvidia* devices found")

# %% [markdown]
# ### 2. Use the GPU from Python (PyTorch)
#
# The same matrix multiplication runs on the CPU and on the GPU. The first GPU
# call includes CUDA start-up, so it is run once before timing.

# %%
print_section("PyTorch on the GPU")

TORCH_CUDA = False

if not HAS_TORCH:
    print("⚠️  Skipping - PyTorch is not installed")
    print("\nInstall it from a terminal (a few GB, includes the CUDA libraries):")
    print("  pip install torch")
    print("then restart the kernel.")
else:
    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available:  {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            TORCH_CUDA = True
            print(f"GPU name:        {torch.cuda.get_device_name(0)}")

            size = 4096
            a_cpu = torch.rand(size, size)
            b_cpu = torch.rand(size, size)

            start = time.perf_counter()
            a_cpu @ b_cpu
            cpu_s = time.perf_counter() - start

            a_gpu, b_gpu = a_cpu.cuda(), b_cpu.cuda()
            a_gpu @ b_gpu  # warm-up
            torch.cuda.synchronize()
            start = time.perf_counter()
            a_gpu @ b_gpu
            torch.cuda.synchronize()
            gpu_s = time.perf_counter() - start

            print(f"\n{size}x{size} matrix multiplication:")
            print(f"  CPU: {cpu_s * 1000:8.1f} ms")
            print(f"  GPU: {gpu_s * 1000:8.1f} ms  ({cpu_s / gpu_s:.0f}x faster)")
            print("\n✓ GPU computation works from this notebook")
        elif GPU_AVAILABLE:
            print("\n✗ A GPU is present, but this PyTorch build cannot use it")
            print("  It is probably a CPU-only build; reinstall with: pip install torch")
        else:
            print("\nNo GPU - PyTorch runs on the CPU only")

    except Exception as e:
        print(fmt_error(e, label="PyTorch GPU test"))

# %% [markdown]
# ### 3. Start a Local LLM Server (Ollama)
#
# [Ollama](https://ollama.com) runs language models on the GPU and serves them
# over an OpenAI-compatible HTTP API. It is a single user-space program: no
# root, no container. The notebook starts its own server on a free port
# (another user on the same node may already use Ollama's default port) and
# stops it in Cleanup.

# %%
print_section("Starting a Local LLM Server")


def free_port():
    """Return a TCP port on localhost that is free right now."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def server_is_up(host):
    """True when the Ollama API at host answers."""
    try:
        with urllib.request.urlopen(f"http://{host}/api/version", timeout=2):
            return True
    except OSError:
        return False


# Re-running this cell reuses a server it already started.
OLLAMA_PROC = globals().get("OLLAMA_PROC")
SERVER_UP = OLLAMA_PROC is not None and OLLAMA_PROC.poll() is None

if SERVER_UP:
    print(f"✓ Server already running at http://{OLLAMA_HOST}")
elif OLLAMA_BIN is None:
    print("⚠️  Skipping - Ollama is not installed")
    print("\nInstall it from a terminal (no root needed, about 2 GB):")
    print("  mkdir -p ~/ollama")
    print("  python3 -m pip install pyzstd")
    print("  curl -fL -o ~/ollama.tar.zst https://ollama.com/download/ollama-linux-amd64.tar.zst")
    print("  python3 -m pyzstd -d ~/ollama.tar.zst --tar-output-dir ~/ollama")
    print("  rm ~/ollama.tar.zst")
    print("then re-run the Load Configuration cell and this one.")
else:
    try:
        OLLAMA_HOST = f"127.0.0.1:{free_port()}"
        OLLAMA_ENV = dict(os.environ, OLLAMA_HOST=OLLAMA_HOST)
        OLLAMA_LOG = os.path.join(tempfile.gettempdir(), f"mcnb_ollama_{os.getpid()}.log")

        print(f"Running: {OLLAMA_BIN} serve  (OLLAMA_HOST={OLLAMA_HOST})")
        with open(OLLAMA_LOG, "w") as log:
            OLLAMA_PROC = subprocess.Popen(
                [OLLAMA_BIN, "serve"], env=OLLAMA_ENV, stdout=log, stderr=subprocess.STDOUT
            )

        for _ in range(30):
            if server_is_up(OLLAMA_HOST) or OLLAMA_PROC.poll() is not None:
                break
            time.sleep(1)

        with open(OLLAMA_LOG) as log:
            log_lines = log.read().splitlines()

        if server_is_up(OLLAMA_HOST):
            SERVER_UP = True
            print(f"✓ Server running at http://{OLLAMA_HOST}")
            # Ollama logs which GPU (or CPU) it will use.
            compute = [l for l in log_lines if "inference compute" in l]
            if compute:
                print(f"\nOllama compute device:\n  {compute[-1].strip()}")
        else:
            print("✗ The server did not start")
            print(f"\nLast lines of {OLLAMA_LOG}:")
            for line in log_lines[-10:] or ["(empty)"]:
                print(f"  {line}")
            if OLLAMA_PROC.poll() is None:
                OLLAMA_PROC.terminate()
            OLLAMA_PROC = None

    except Exception as e:
        print(fmt_error(e, label="start Ollama"))
        OLLAMA_PROC = None

# %% [markdown]
# ### 4. Download a Small Model
#
# The first run downloads the model (about 1 GB for the default) to
# `~/.ollama/models`; later runs reuse it.

# %%
print_section("Downloading the Model")

MODEL_READY = False

if not SERVER_UP:
    print("⚠️  Skipping - the local server is not running (see step 3)")
else:
    try:
        print(f"Running: ollama pull {LOCAL_LLM_MODEL}")
        print("(This may take a few minutes the first time)\n")
        result = subprocess.run(
            [OLLAMA_BIN, "pull", LOCAL_LLM_MODEL],
            env=OLLAMA_ENV, capture_output=True, text=True, timeout=900,
        )
        if result.returncode == 0:
            MODEL_READY = True
            print(f"✓ Model '{LOCAL_LLM_MODEL}' is ready")
        else:
            print(f"✗ Download failed (exit code {result.returncode})")
            for line in (result.stderr or result.stdout).strip().splitlines()[-3:]:
                print(f"  {line}")
            print("\nCheck the model name at https://ollama.com/library and the network.")

    except subprocess.TimeoutExpired:
        print("✗ Download did not finish within 15 minutes; re-run this cell to resume")
    except Exception as e:
        print(fmt_error(e, label="ollama pull"))

# %% [markdown]
# ### 5. Chat with the Local Model
#
# This is the same OpenAI client as in notebook 04. Only `base_url` changes:
# from the hosted e-INFRA CZ service to the model on your own GPU.

# %%
print_section("Chat with the Local Model")

LOCAL_CHAT_OK = False
MODEL_ON_GPU = False
MAX_TOKENS = 1024  # same budget as notebook 04

if not MODEL_READY:
    print("⚠️  Skipping - no local model available (see steps 3 and 4)")
elif not HAS_OPENAI:
    print("⚠️  Skipping - the openai package is not installed")
    print("\nInstall it from a terminal, from the repo root:")
    print('  pip install -e ".[openwebui]"')
    print("then restart the kernel.")
else:
    try:
        from openai import OpenAI

        # Ollama ignores the API key, but the client requires one.
        local_client = OpenAI(base_url=f"http://{OLLAMA_HOST}/v1", api_key="ollama")

        messages = [
            {"role": "system", "content": "You are a helpful assistant running on a MetaCentrum GPU."},
            {"role": "user", "content": "In two sentences, what is a GPU and why is it useful for AI?"},
        ]
        print(f"Model:  {LOCAL_LLM_MODEL}")
        print(f"Prompt: {messages[-1]['content']}\n")

        start = time.perf_counter()
        response = local_client.chat.completions.create(
            model=LOCAL_LLM_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        elapsed = time.perf_counter() - start

        answer = response.choices[0].message.content if response.choices else None
        if answer and answer.strip():
            LOCAL_CHAT_OK = True
            print("Response:")
            print("-" * 60)
            print(answer.strip())
            print("-" * 60)
            tokens = response.usage.completion_tokens if response.usage else None
            if tokens:
                print(f"\n{tokens} tokens in {elapsed:.1f} s ({tokens / elapsed:.0f} tokens/s, includes model loading on first call)")
        else:
            finish = response.choices[0].finish_reason if response.choices else None
            print(f"✗ The model returned no text (finish_reason={finish})")

        # `ollama ps` shows where the loaded model runs, e.g. "100% GPU".
        ps = subprocess.run(
            [OLLAMA_BIN, "ps"], env=OLLAMA_ENV, capture_output=True, text=True, timeout=10
        )
        print("\nollama ps:")
        print(ps.stdout.strip() or ps.stderr.strip())
        MODEL_ON_GPU = "GPU" in ps.stdout
        if LOCAL_CHAT_OK:
            if MODEL_ON_GPU:
                print("\n✓ The model answered from this node's GPU")
            else:
                print("\n⚠️  The model answered, but it runs on the CPU (see Troubleshooting)")

    except Exception as e:
        print(fmt_error(e, label="local chat"))

# %% [markdown]
# ### 6. Optional: Containers
#
# Apptainer containers are MetaCentrum's usual way to bring your own software
# (for example a specific PyTorch build) to a GPU node, with `--nv` to pass the
# GPU in. On OnDemand, though, Jupyter itself already runs inside Apptainer, so
# starting a container from here nests one container in another. That only
# works with an unprivileged (user-namespace) runtime; this step tests whether
# it works in your session.
#
# Where nested containers fail, run the container from a PBS job instead, for
# example with this job script (`qsub gpu_container.sh`):
#
# ```bash
# #PBS -N gpu-container
# #PBS -l select=1:ncpus=2:ngpus=1:mem=16gb:scratch_local=20gb
# #PBS -l walltime=00:30:00
#
# # Keep the image cache and build files off the home quota.
# export SINGULARITY_CACHEDIR=$SCRATCHDIR SINGULARITY_TMPDIR=$SCRATCHDIR
# singularity exec --nv docker://pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime \
#   python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# ```

# %%
print_section("Optional: Container Runtime")


def check_runtime(runtime_name):
    """Check if a container runtime is available AND functional."""
    try:
        result = run(f"{runtime_name} --version", timeout=5, check=False)
        # A working runtime prints its version; empty output means the binary
        # exists but is non-functional (e.g. Docker stub with no daemon socket).
        if result and "version" in result.lower():
            return True, result
        return False, f"{runtime_name}: found but not functional (output: {result!r})"
    except Exception as e:
        return False, fmt_error(e, label=runtime_name)


def run_container(cmd, timeout):
    """Run a container command and return (exit code, output).

    Unlike run(), this keeps the exit code: the runtime can print a lot
    (image pull progress) and still fail before the container starts.
    """
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    output = "\n".join(s.strip() for s in (result.stdout, result.stderr) if s.strip())
    return result.returncode, output


# On OnDemand, Jupyter runs inside Apptainer and Docker is not available.
INSIDE_CONTAINER = os.path.exists("/.singularity.d") or os.path.exists("/.dockerenv")
if INSIDE_CONTAINER:
    print("ℹ  Running inside a container - only Apptainer/Singularity are probed.\n")

runtimes_to_check = list(dict.fromkeys([CONTAINER_RUNTIME, "apptainer", "singularity"]))
if not INSIDE_CONTAINER:
    runtimes_to_check.append("docker")

RUNTIME_CMD = None
for runtime in runtimes_to_check:
    available, version = check_runtime(runtime)
    if available:
        RUNTIME_CMD = runtime
        print(f"✓ Found container runtime: {runtime}")
        print(f"  Version: {version.splitlines()[0]}\n")
        break

CONTAINER_WORKS = False

if RUNTIME_CMD is None:
    print("⚠️  No container runtime found (tried: " + ", ".join(runtimes_to_check) + ")")
    print("   That is fine for steps 1-5. In a PBS job: module load apptainer")
else:
    if RUNTIME_CMD == "docker":
        cmd = "docker run --rm alpine:latest echo 'Hello from container!'"
    else:
        cmd = f"{RUNTIME_CMD} exec docker://alpine:latest echo 'Hello from container!'"
    print(f"Running: {cmd}\n")

    try:
        exit_code, output = run_container(cmd, timeout=120)
        if exit_code == 0 and "Hello from container" in output:
            CONTAINER_WORKS = True
            print("✓ Containers can be started from this session")
        else:
            print(f"✗ Container could not start (exit code {exit_code})\n")
            lines = output.splitlines()
            errors = [l.strip() for l in lines if l.lstrip().startswith(("ERROR", "FATAL"))]
            print("Runtime error:")
            for line in errors or lines[-5:] or ["(no output)"]:
                print(f"  {line}")
            if "setuid" in output:
                print("\nThis runtime needs setuid, which does not work inside the OnDemand")
                print("container. This is expected here: steps 1-5 use the GPU without a")
                print("container, and the PBS job script above runs containers on a GPU node.")
    except subprocess.TimeoutExpired:
        print("✗ The container did not finish within 2 minutes (image pull too slow?)")
    except Exception as e:
        print(fmt_error(e, label="container test"))

# %% [markdown]
# ### 7. Summary

# %%
print_section("Summary")

checks = [
    ("GPU visible in this session", GPU_AVAILABLE),
    ("PyTorch computes on the GPU", TORCH_CUDA),
    ("Local LLM server running", SERVER_UP),
    ("Local model answered", LOCAL_CHAT_OK),
    ("Local model runs on the GPU", MODEL_ON_GPU),
]
# Step 6 is optional: listed only when it was run.
if "CONTAINER_WORKS" in globals():
    checks.append(("Containers start from this session (optional)", CONTAINER_WORKS))

for check_name, passed in checks:
    status = "✓ YES" if passed else "✗ NO "
    print(f"  {status}  - {check_name}")

print("\n" + "=" * 60)
if LOCAL_CHAT_OK and MODEL_ON_GPU:
    print("✓ A language model is running on this session's GPU")
elif LOCAL_CHAT_OK:
    print("✓ A language model is running locally (on the CPU)")
else:
    print("⚠️  Some steps were skipped or failed - see the messages above")
print("=" * 60)

# %% [markdown]
# ## Cleanup
#
# Stops the Ollama server this notebook started and removes its log. The
# downloaded model stays in `~/.ollama/models` for the next run; delete it with
# `~/ollama/bin/ollama rm <model>` (while a server runs) or remove that folder.

# %%
print_section("Cleanup")

_proc = globals().get("OLLAMA_PROC")
if _proc is not None and _proc.poll() is None:
    _proc.terminate()
    try:
        _proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _proc.kill()
    print("✓ Stopped the Ollama server")
else:
    print("No Ollama server was started by this notebook")
OLLAMA_PROC = None
SERVER_UP = False

_log = globals().get("OLLAMA_LOG")
if _log and os.path.exists(_log):
    try:
        os.remove(_log)
        print(f"✓ Removed: {_log}")
    except OSError as e:
        print(f"⚠️  Could not remove {_log}: {e}")

print("\n✓ Cleanup complete")
print("\nNote: the model and any container images stay cached for later runs.")

# %% [markdown]
# ## Troubleshooting
#
# ### GPU Issues
#
# **No GPU detected**
# - On OnDemand: start the Jupyter session with a GPU (GPU field in the form)
# - In a PBS job: `#PBS -l select=1:ncpus=1:ngpus=1`
# - Check that `nvidia-smi` works in a terminal of the same session
#
# **PyTorch: `CUDA available: False` although a GPU is present**
# - A CPU-only build is installed; `pip install torch` from PyPI includes CUDA on Linux
# - The kernel runs Python 3.9 on OnDemand, so pip picks the last PyTorch release for 3.9; that still works

# %% [markdown]
# ### Local LLM Issues
#
# **`zstd: Cannot exec` / `tar: Child died with signal 13` / `curl: (23) Failure writing output`**
# - The Ollama release is a `.tar.zst` archive; `tar --zstd` needs the `zstd` tool, which the OnDemand images (e.g. `debian11.sif`) do not have
# - The `curl` error is a follow-up: `tar` stopped, so the download had nowhere to go
# - Use the `pyzstd` commands from "Install Ollama" above; see the [Ollama Linux docs](https://docs.ollama.com/linux) for other install options
#
# **The server does not start**
# - The cell prints the end of the server log; read the error there
# - Check the binary runs: `~/ollama/bin/ollama --version`
#
# **The model runs on the CPU (`ollama ps` shows `100% CPU`)**
# - The session has no GPU, or Ollama could not find the CUDA libraries
# - The `inference compute` line from step 3 shows what Ollama detected
#
# **Download is slow or fails**
# - The first download is about 1 GB; re-running the cell resumes it
# - Check the model name at https://ollama.com/library
#
# **Home quota exceeded**
# - Ollama (~2 GB) and models live in your home directory
# - Remove unused models: `~/ollama/bin/ollama rm <model>`

# %% [markdown]
# ### Container Issues
#
# **`No setuid installation found` (OnDemand)**
# - Jupyter on OnDemand already runs in Apptainer; setuid does not work in a nested container
# - Run containers from a PBS job (script in step 6) or a frontend shell
#
# **Container runtime not found**
# - In a PBS job or on a frontend: `module load apptainer`
# - Check that the runtime is in PATH: `which apptainer singularity`
#
# **Cannot pull images**
# - Network connectivity required
# - Use pre-downloaded `.sif` files instead
# - Set `SINGULARITY_CACHEDIR` to scratch to avoid filling the home quota

# %% [markdown]
# ### Debugging Tips
#
# ```bash
# # GPU in this session
# nvidia-smi
#
# # Ollama by hand (default port 11434)
# ~/ollama/bin/ollama serve &
# ~/ollama/bin/ollama run qwen2.5:1.5b "Hello"
# ~/ollama/bin/ollama ps
#
# # OpenAI-compatible API
# curl http://127.0.0.1:11434/v1/models
#
# # Containers (PBS job or frontend)
# apptainer exec --nv docker://nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
# ```

# %% [markdown]
# ## Next Steps
#
# ### Bigger or Different Models
#
# - Set `LOCAL_LLM_MODEL` in your env file, e.g. `llama3.2:3b` or `qwen2.5:7b`
# - Larger models need more GPU memory; `nvidia-smi` shows how much the GPU has
# - Use the local model in notebook 04's code by changing only `base_url`

# %% [markdown]
# ### GPU Workloads Beyond Chat
#
# - **Model training** - Train neural networks with PyTorch on the GPU
# - **Batch inference** - Process large datasets in a PBS job
# - **Containers** - Pin exact software versions with Apptainer images in PBS jobs
# - **Multi-GPU** - Request more GPUs with `ngpus=2` and higher

# %% [markdown]
# ### Integration Ideas
#
# - **S3 + local model** - Summarise documents stored in object storage
# - **Repository integration** - Archive trained models to Invenio
# - **OpenStack** - Run a model server on a GPU virtual machine

# %% [markdown]
# ### Related Notebooks
#
# - **01_s3_object_storage.ipynb** - Store models and datasets
# - **03_openstack_api.ipynb** - Launch GPU instances
# - **04_open_webui_chat_api.ipynb** - The same chat code against the hosted e-INFRA CZ service

# %% [markdown]
# ### Documentation
#
# - [MetaCentrum GPU Computing](https://docs.metacentrum.cz/en/docs/computing/gpu-comput/nvidia)
# - [MetaCentrum Containers](https://docs.metacentrum.cz/en/docs/software/containers)
# - [Ollama Linux install](https://docs.ollama.com/linux)
# - [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
# - [Ollama model library](https://ollama.com/library)
# - [PyTorch CUDA semantics](https://pytorch.org/docs/stable/notes/cuda.html)
# - [Apptainer Documentation](https://apptainer.org/docs/)
