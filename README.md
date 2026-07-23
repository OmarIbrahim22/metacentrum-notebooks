# MetaCentrum Jupyter Notebooks

Sample Jupyter notebooks demonstrating integration with [MetaCentrum](https://metavo.metacentrum.cz/) and [e-INFRA CZ](https://www.e-infra.cz/) services. Each notebook covers one service, includes step-by-step documentation, and is designed to run on [ondemand.metacentrum.cz](https://ondemand.metacentrum.cz/) and [jupyter.e-infra.cz](https://jupyter.e-infra.cz/).

---

## Notebooks

| # | Notebook | Service | Credentials |
|---|----------|---------|-------------|
| 00 | [Environment Check](notebooks/00_environment_check.ipynb) | Diagnostics & credential setup wizard | None |
| 01 | [S3 Object Storage](notebooks/01_s3_object_storage.ipynb) | [CESNET S3 storage](https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service) | S3 endpoint, access key, secret key, bucket |
| 02 | [Invenio Repository](notebooks/02_invenio_repository.ipynb) | [EOSC CZ / NRP](https://data.narodni-repozitar.cz/) | NRP API token |
| 03 | [OpenStack API](notebooks/03_openstack_api.ipynb) | [e-INFRA Cloud](https://docs.platforms.cloud.e-infra.cz/en/docs/technical-reference/brno-g2-site) | OpenStack application credentials |
| 04 | [Open WebUI Chat API](notebooks/04_open_webui_chat_api.ipynb) | [e-INFRA AI Chat](https://docs.cerit-sc.cz/en/docs/web-apps/chat-ai) | AI API token |
| 05 | [GPU Container + AI Model](notebooks/05_gpu_container_ai_model.ipynb) | Apptainer/Docker with GPU passthrough | None (optional config) |
| 06 | [R Kernel Demo](notebooks/06_r_kernel_demo.ipynb) | R language kernel | None (R kernel required) |
| 07 | [MATLAB Kernel Demo](notebooks/07_matlab_kernel_demo.ipynb) | MATLAB kernel | None (MATLAB kernel required) |

---

## How to Use

### On MetaCentrum / e-INFRA JupyterHub

1. Upload or clone this repository into your JupyterHub home directory.
2. Open **`00_environment_check.ipynb`** and run all cells -- it verifies your environment and walks you through credential setup with an interactive wizard.
3. Open any other notebook and run it. Each notebook auto-installs its dependencies on first run (a one-time kernel restart may be needed).

### Locally

```bash
git clone <this-repo-url>
cd <repo>
pip install -e .
jupyter lab
```

Then start with `00_environment_check.ipynb`.

---

## Credential Setup

Credentials are **never stored in the repository**. Three options:

1. **Interactive wizard (recommended)** -- The setup cell in `00_environment_check.ipynb` calls `setup_env()`, prompts for each value, and saves them to `~/.config/mcnb/env`. Credentials persist across kernel restarts and sessions.

2. **Manual file** -- Copy `env.example` to `.env` (or `env` if your platform blocks dotfiles) and fill in your values.

3. **Home directory config** -- Create `~/.config/mcnb/env` manually. This file has the highest priority.

The file `env.example` lists all variables with links to documentation for obtaining each credential.

---

## What Each Notebook Demonstrates

**00 -- Environment Check**: Detects runtime (local vs MetaCentrum vs e-INFRA), Python version, GPU availability, disk space. Hosts the interactive credential wizard.

**01 -- S3 Object Storage**: Full CRUD cycle using `boto3` -- list buckets, upload a test file, download and verify, generate a presigned URL, retrieve metadata, clean up.

**02 -- Invenio Repository**: Invenio REST API for the National Repository Platform -- create a draft record, upload a file (three-step process), retrieve draft details, clean up.

**03 -- OpenStack API**: Read-only exploration of e-INFRA OpenStack cloud using `openstacksdk` -- authenticate, list flavors/images, check compute quotas, list servers and networks.

**04 -- Open WebUI Chat API**: OpenAI-compatible API for e-INFRA AI chat -- list models, simple chat completion, multi-turn conversation, code generation, streaming responses.

**05 -- GPU Container + AI Model**: Detect container runtime (Apptainer/Singularity/Docker), run a basic container, test GPU passthrough with `nvidia-smi`, run PyTorch inference inside a GPU container.

**06 -- R Kernel Demo**: Basic R usage in Jupyter -- data frames, statistical functions, ggplot2 visualization, package management.

**07 -- MATLAB Kernel Demo**: MATLAB in Jupyter -- arrays, matrices, symbolic math, plotting, file I/O.

---

## Shared Helper Package (`mcnb`)

All Python notebooks import from `src/mcnb/` to keep credential handling and utilities consistent:

| Function | Purpose |
|----------|---------|
| `env.need("VAR")` | Return a required env var or raise a clear error |
| `env.optional("VAR")` | Return an env var or `None` if not set |
| `env.mask(value)` | Mask credentials for safe printing (`****abcd`) |
| `env.setup_env()` | Interactive credential configuration wizard |
| `util.detect_environment()` | Detect platform, Jupyter, MetaCentrum, e-INFRA |
| `util.check_gpu_available()` | Check GPU availability via nvidia-smi |
| `util.fmt_error(e, label)` | Format exceptions consistently |

---

## Requirements

- Python 3.8+
- Jupyter environment (JupyterLab, JupyterHub, or local)
- Service-specific credentials (see table above)
- For notebook 06: R kernel ([IRkernel](https://irkernel.github.io/))
- For notebook 07: MATLAB kernel

---

*Bachelor thesis project -- Faculty of Informatics, Masaryk University*
