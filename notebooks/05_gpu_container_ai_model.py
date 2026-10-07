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
# # 05 - GPU Container with AI Model
#
# ## Goal
#
# Demonstrate running containers with GPU passthrough to execute AI workloads. This notebook shows how to verify GPU availability, run containers (Apptainer/Singularity), pass GPU devices to containers, and execute AI inference workloads.
#
# **Runtime**: ~3-5 minutes (depending on container availability)
#
# **Note**: This notebook degrades gracefully if GPU or container runtime is not available.

# %% [markdown]
# ## What You Will Learn
#
# - How to detect GPU availability in your environment
# - How to check for container runtime (Apptainer/Singularity)
# - How to run containers with GPU passthrough
# - How to verify GPU access inside containers
# - How to execute AI inference workloads in containers
# - Best practices for containerized GPU workloads

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - GPU node access (on MetaCentrum: request with `#PBS -l select=1:ncpus=1:ngpus=1`)
# - Container runtime: Apptainer (Singularity) or Docker
# - Container image with AI framework (PyTorch, TensorFlow, ONNX)

# %% [markdown]
# ### Where to Get Container Images
#
# **Option 1: Pre-built images**
# - NVIDIA NGC Catalog: https://catalog.ngc.nvidia.com/
# - Docker Hub: https://hub.docker.com/
#
# **Option 2: MetaCentrum/e-INFRA provided images**
# - Check `/cvmfs/singularity.metacentrum.cz/` (if available)
# - Or build your own container image

# %% [markdown]
# ### Required Environment Variables
#
# Add these to your `.env` file (optional - notebook will detect automatically):
#
# ```bash
# CONTAINER_RUNTIME=apptainer  # or singularity, docker
# CONTAINER_IMAGE=/path/to/image.sif  # optional: path to specific image
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install -e .
# ```
#
# Run once from the repo root, from a terminal (not from inside a notebook cell).
# No packages beyond the base utilities are needed for this notebook.
#
# **On MetaCentrum**: Container runtimes are usually pre-installed.

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

import subprocess
import os
import tempfile

# %% [markdown]
# ### Load Configuration

# %%
print_section("Loading Configuration")

# Optional configuration
CONTAINER_RUNTIME = optional("CONTAINER_RUNTIME", "apptainer")
CONTAINER_IMAGE = optional("CONTAINER_IMAGE", None)

print(f"Container runtime preference: {CONTAINER_RUNTIME}")
if CONTAINER_IMAGE:
    print(f"Container image: {CONTAINER_IMAGE}")
else:
    print("Container image: Will auto-detect or use minimal demo")

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. Check GPU Availability (Host)

# %%
print_section("Checking GPU Availability on Host")

gpu_info = check_gpu_available()

if gpu_info["available"]:
    print("✓ GPU detected on host!\n")
    print("nvidia-smi output:")
    print("=" * 60)
    print(gpu_info["output"])
    print("=" * 60)
    
    GPU_AVAILABLE = True
else:
    print("✗ No GPU detected on host\n")
    print(f"Details: {gpu_info['output']}")
    print("\n⚠️  This notebook can still run but will use CPU mode")
    print("\nOn MetaCentrum, request GPU with:")
    print("  #PBS -l select=1:ncpus=1:ngpus=1")
    
    GPU_AVAILABLE = False

# Check for GPU devices
if gpu_info["devices"]:
    print(f"\nGPU devices found: {', '.join(gpu_info['devices'])}")
else:
    print("\nNo /dev/nvidia* devices found")

# %% [markdown]
# ### 2. Detect Container Runtime

# %%
print_section("Detecting Container Runtime")

def check_runtime(runtime_name):
    """Check if a container runtime is available AND functional."""
    try:
        result = run(f"{runtime_name} --version", timeout=5, check=False)
        # A working runtime prints its version; empty output means the binary
        # exists but is non-functional (e.g. Docker stub with no daemon socket).
        if result and "version" in result.lower():
            return True, result
        return False, f"{runtime_name}: found but not functional (output: {result!r})"
    except FileNotFoundError:
        return False, f"{runtime_name}: command not found"
    except PermissionError as e:
        return False, f"{runtime_name}: permission denied — {e}"
    except Exception as e:
        return False, fmt_error(e, label=runtime_name)

import os as _os

# Detect if we are already running inside a container.
# On MetaCentrum/ondemand, Jupyter itself runs inside Apptainer — Docker-in-Docker
# is blocked. On a local dev machine, /.singularity.d does not exist, so Docker is probed.
INSIDE_CONTAINER = _os.path.exists("/.singularity.d") or _os.path.exists("/.dockerenv")
if INSIDE_CONTAINER:
    print("ℹ  Running inside a container — Docker-in-Docker is not available.")
    print("   Only Apptainer/Singularity will be probed.\n")

# Build probe list: user preference first, then Apptainer/Singularity,
# then Docker only if we are on a bare host.
_seen = set()
runtimes_to_check = []
for _r in [CONTAINER_RUNTIME, "apptainer", "singularity"]:
    if _r and _r not in _seen:
        _seen.add(_r)
        runtimes_to_check.append(_r)
if not INSIDE_CONTAINER:
    runtimes_to_check.append("docker")

RUNTIME_CMD = None
RUNTIME_NAME = None

for runtime in runtimes_to_check:
    available, version = check_runtime(runtime)
    if available:
        RUNTIME_CMD = runtime
        RUNTIME_NAME = runtime
        print(f"✓ Found container runtime: {runtime}")
        print(f"  Version: {version.split(chr(10))[0]}")
        break

if RUNTIME_CMD is None:
    print("✗ No container runtime found")
    print("\nTried: " + ", ".join(runtimes_to_check))
    print("\n⚠️  Container demos will be skipped")
    print("\nOn MetaCentrum, load module:")
    print("  module load apptainer")

# %% [markdown]
# ### 3. Test Container Execution (Basic)

# %%
print_section("Testing Basic Container Execution")

if RUNTIME_CMD is None:
    print("⚠️  Skipping - no container runtime available")
else:
    try:
        # Use a minimal test - most runtimes support running from Docker Hub
        if RUNTIME_NAME in ["apptainer", "singularity"]:
            # Apptainer/Singularity can run Docker images directly
            cmd = f"{RUNTIME_CMD} exec docker://alpine:latest echo 'Hello from container!'"
        else:  # docker
            cmd = f"{RUNTIME_CMD} run --rm alpine:latest echo 'Hello from container!'"
        
        print(f"Running: {cmd}\n")
        
        output = run(cmd, timeout=60, check=False)
        
        if "Hello from container" in output:
            print("✓ Container execution successful!")
            print(f"\nOutput: {output}")
            CONTAINER_WORKS = True
        else:
            print("⚠️  Container ran but output unexpected")
            print(f"Output: {output}")
            CONTAINER_WORKS = False
            
    except Exception as e:
        print(fmt_error(e, label="container execution"))
        print("\nThis may be due to:")
        print("  - Network access required to pull images")
        print("  - Permission issues")
        print("  - Container runtime not properly configured")
        CONTAINER_WORKS = False

# %% [markdown]
# ### 4. Test GPU Passthrough to Container

# %%
print_section("Testing GPU Passthrough to Container")

if RUNTIME_CMD is None:
    print("⚠️  Skipping - no container runtime available")
elif not GPU_AVAILABLE:
    print("⚠️  Skipping - no GPU available on host")
else:
    try:
        # Build GPU-enabled container command
        if RUNTIME_NAME in ["apptainer", "singularity"]:
            # Apptainer/Singularity use --nv flag for NVIDIA GPU support
            if CONTAINER_IMAGE and os.path.exists(CONTAINER_IMAGE):
                container_ref = CONTAINER_IMAGE
            else:
                # Use NVIDIA CUDA container from Docker Hub
                container_ref = "docker://nvidia/cuda:12.0.0-base-ubuntu22.04"
            
            cmd = f"{RUNTIME_CMD} exec --nv {container_ref} nvidia-smi"
            
        else:  # docker
            if CONTAINER_IMAGE:
                container_ref = CONTAINER_IMAGE
            else:
                container_ref = "nvidia/cuda:12.0.0-base-ubuntu22.04"
            
            cmd = f"{RUNTIME_CMD} run --rm --gpus all {container_ref} nvidia-smi"
        
        print(f"Running: {cmd}\n")
        print("(This may take a moment if the image needs to be pulled)\n")
        
        output = run(cmd, timeout=180, check=False)
        
        if "NVIDIA-SMI" in output:
            print("✓ GPU passthrough successful!\n")
            print("nvidia-smi output from inside container:")
            print("=" * 60)
            print(output)
            print("=" * 60)
            GPU_IN_CONTAINER = True
        else:
            print("✗ GPU passthrough failed")
            print(f"\nOutput: {output[:500]}")
            GPU_IN_CONTAINER = False
            
    except Exception as e:
        print(fmt_error(e, label="GPU passthrough test"))
        print("\nCommon causes:")
        print("  - Container runtime doesn't support GPU passthrough")
        print("  - NVIDIA container toolkit not installed (Docker)")
        print("  - Wrong GPU flags for this runtime")
        GPU_IN_CONTAINER = False

# %% [markdown]
# ### 5. Simple AI Inference Demo

# %%
print_section("AI Inference Demo (Python in Container)")

if RUNTIME_CMD is None or not CONTAINER_WORKS:
    print("⚠️  Skipping - container runtime not available or not working")
else:
    try:
        # Create a simple Python script to test PyTorch GPU availability
        test_script = '''
import sys
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        print(f"GPU name: {torch.cuda.get_device_name(0)}")
        
        # Simple tensor operation on GPU
        x = torch.rand(5, 3).cuda()
        print(f"\\nCreated tensor on GPU: {x.device}")
        print(f"Tensor shape: {x.shape}")
        print("✓ GPU tensor operations working!")
    else:
        print("Running in CPU mode")
        x = torch.rand(5, 3)
        print(f"Created tensor: {x.shape}")
except ImportError:
    print("PyTorch not available in this container")
    print("This is OK - demonstrates container execution")
except Exception as e:
    print(f"Error: {e}")
'''
        
        # Write script to a uniquely named temp file
        try:
            _fd, script_path = tempfile.mkstemp(prefix="mcnb_gpu_test_", suffix=".py")
            with os.fdopen(_fd, "w") as f:
                f.write(test_script)
        except OSError as e:
            print(fmt_error(e, label="write temp script"))
            print("  Cannot write to the temp directory — skipping AI inference demo.")
            script_path = None

        if script_path is None:
            pass  # already reported above
        else:
            try:
                print("Testing PyTorch GPU availability in container...\n")

                # Build container command
                if RUNTIME_NAME in ["apptainer", "singularity"]:
                    gpu_flag = "--nv" if GPU_AVAILABLE else ""
                    container_ref = CONTAINER_IMAGE if CONTAINER_IMAGE else "docker://pytorch/pytorch:latest"
                    cmd = f"{RUNTIME_CMD} exec {gpu_flag} {container_ref} python {script_path}"
                else:  # docker
                    gpu_flag = "--gpus all" if GPU_AVAILABLE else ""
                    container_ref = CONTAINER_IMAGE if CONTAINER_IMAGE else "pytorch/pytorch:latest"
                    cmd = f"{RUNTIME_CMD} run --rm {gpu_flag} -v {script_path}:{script_path} {container_ref} python {script_path}"

                print(f"Running: {cmd}\n")
                print("(This may take a moment if pulling PyTorch image)\n")

                output = run(cmd, timeout=300, check=False)

                print("Output:")
                print("=" * 60)
                print(output if output else "(no output)")
                print("=" * 60)

                if "PyTorch version" in output or "PyTorch not available" in output:
                    print("\n✓ Container execution successful!")
                    if "GPU tensor operations working" in output:
                        print("✓ GPU operations confirmed working in container!")
                else:
                    print("\n⚠️  Execution completed but output was unexpected or empty")

            except Exception as e:
                print(fmt_error(e, label="AI inference demo"))
                print("\nThis is often due to:")
                print("  - Image pull timeout or network issues")
                print("  - Container doesn't have PyTorch installed")
                print("  - Insufficient resources")
            finally:
                # Always clean up temp file
                try:
                    os.remove(script_path)
                except OSError:
                    pass  # already gone or never written

    except Exception as e:
        print(fmt_error(e, label="AI inference demo — unexpected error"))
        print("\nThis is often due to:")
        print("  - Image pull timeout or network issues")
        print("  - Container doesn't have PyTorch installed")
        print("  - Insufficient resources")

# %% [markdown]
# ### 6. Environment Summary

# %%
print_section("GPU Container Environment Summary")

print("Capability Checklist:\n")

checks = [
    ("GPU available on host", GPU_AVAILABLE),
    ("Container runtime available", RUNTIME_CMD is not None),
    ("Container execution works", CONTAINER_WORKS if 'CONTAINER_WORKS' in locals() else False),
    ("GPU passthrough works", GPU_IN_CONTAINER if 'GPU_IN_CONTAINER' in locals() else False),
]

for check_name, passed in checks:
    status = "✓ YES" if passed else "✗ NO "
    print(f"  {status}  - {check_name}")

print("\nConfiguration:")
print(f"  Runtime: {RUNTIME_NAME if RUNTIME_CMD else 'None'}")
if CONTAINER_IMAGE:
    print(f"  Image: {CONTAINER_IMAGE}")

print("\n" + "=" * 60)
if GPU_AVAILABLE and RUNTIME_CMD and checks[2][1]:
    print("✓ Environment ready for GPU-accelerated containerized AI workloads!")
elif RUNTIME_CMD and checks[2][1]:
    print("✓ Environment ready for CPU containerized AI workloads")
    print("  (Request GPU node for GPU acceleration)")
else:
    print("⚠️  Some capabilities missing - see checklist above")
print("=" * 60)

# %% [markdown]
# ## Cleanup
#
# Clean up any temporary files created during the demo:

# %%
print_section("Cleanup")

# The inference demo removes its temp script itself; this is a safety net
# in case that cell was interrupted.
cleanup_paths = [p for p in [globals().get("script_path")] if p]

for path in cleanup_paths:
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✓ Removed: {path}")
        except Exception as e:
            print(f"⚠️  Could not remove {path}: {e}")

print("\n✓ Cleanup complete")
print("\nNote: Container images may be cached by the runtime.")
print("      This is normal and helps performance on subsequent runs.")

# %% [markdown]
# ## Troubleshooting
#
# ### GPU Issues
#
# **No GPU detected on host**
# - Not running on a GPU node
# - On MetaCentrum: Use `#PBS -l select=1:ncpus=1:ngpus=1`
# - Check `nvidia-smi` works in terminal
# - Verify NVIDIA drivers installed
#
# **GPU detected but not in container**
# - Missing GPU flags (`--nv` for Apptainer, `--gpus all` for Docker)
# - Docker: Install NVIDIA Container Toolkit
# - Check container runtime supports GPU passthrough

# %% [markdown]
# ### Container Runtime Issues
#
# **Container runtime not found**
# - On MetaCentrum: `module load apptainer`
# - Check runtime is in PATH: `which apptainer`
# - Install locally if needed
#
# **Permission denied errors**
# - Docker: Add user to docker group (or use rootless mode)
# - Apptainer: Usually runs as user (no special permissions needed)
# - Check file permissions on container images
#
# **Cannot pull images**
# - Network connectivity required
# - Some sites block Docker Hub
# - Use pre-downloaded .sif files instead
# - Check proxy settings

# %% [markdown]
# ### Container Execution Issues
#
# **"library not found" errors**
# - Container missing required CUDA libraries
# - Use NVIDIA-provided base images
# - Check CUDA version compatibility
#
# **Slow execution**
# - First run pulls image (can be large)
# - Subsequent runs use cached image
# - Pre-download images for production use
#
# **Container can't access files**
# - Bind mount needed: `apptainer exec -B /path:/path ...`
# - Docker: Use `-v /path:/path` flag
# - Check file paths are absolute

# %% [markdown]
# ### AI Framework Issues
#
# **PyTorch/TensorFlow not found**
# - Container doesn't have framework installed
# - Use framework-specific images (e.g., `pytorch/pytorch`)
# - Or install in container during build
#
# **CUDA version mismatch**
# - Container CUDA version != host driver version
# - Use containers with compatible CUDA
# - NVIDIA drivers are backward compatible (usually)

# %% [markdown]
# ### Debugging Tips
#
# ```bash
# # Check GPU on host
# nvidia-smi
#
# # Check runtime version
# apptainer --version
#
# # Test basic container
# apptainer exec docker://alpine:latest cat /etc/os-release
#
# # Test GPU in container
# apptainer exec --nv docker://nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
#
# # Interactive shell in container
# apptainer shell --nv docker://pytorch/pytorch:latest
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand GPU containers, you can:
#
# ### Advanced Container Usage
#
# - **Build custom images** - Create Singularity/Docker definition files
# - **Multi-GPU setups** - Utilize multiple GPUs in parallel
# - **Container orchestration** - Use Kubernetes for scaling
# - **MPI in containers** - Distributed computing across nodes

# %% [markdown]
# ### AI/ML Workloads
#
# - **Model training** - Train neural networks with GPU acceleration
# - **Batch inference** - Process large datasets efficiently
# - **Model serving** - Deploy models as containerized services
# - **Distributed training** - Multi-node, multi-GPU training

# %% [markdown]
# ### Integration Ideas
#
# - **S3 + Containers** - Load data from object storage, process in container
# - **Repository integration** - Archive trained models to Invenio
# - **OpenStack + Containers** - Launch GPU VMs with containerized workloads
# - **Workflow pipelines** - Chain notebooks for end-to-end ML pipelines

# %% [markdown]
# ### Performance Tips
#
# **Container optimization**
# - Use minimal base images
# - Layer caching for faster builds
# - Pre-download datasets into image
# - Use bind mounts for large data
#
# **GPU optimization**
# - Batch size tuning
# - Mixed precision training (FP16)
# - Gradient accumulation
# - Profile with nvidia-smi, nvprof
#
# **MetaCentrum-specific**
# - Use scratch storage for temporary data
# - Request appropriate walltime
# - Monitor job efficiency
# - Use GPU quotas wisely

# %% [markdown]
# ### Related Notebooks
#
# - **01_s3_object_storage.ipynb** - Store models and datasets
# - **03_openstack_api.ipynb** - Launch GPU instances
# - **04_open_webui_chat_api.ipynb** - Compare with API-based AI

# %% [markdown]
# ### Documentation
#
# - [Apptainer Documentation](https://apptainer.org/docs/)
# - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
# - [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/)
# - [MetaCentrum GPU Computing](https://docs.metacentrum.cz/en/docs/computing/gpu-comput/nvidia)
# - [MetaCentrum Containers](https://docs.metacentrum.cz/en/docs/software/containers)
# - [PyTorch Docker Images](https://github.com/pytorch/pytorch#docker-image)
# - [TensorFlow Docker Images](https://www.tensorflow.org/install/docker)
