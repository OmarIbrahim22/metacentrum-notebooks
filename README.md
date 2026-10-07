# MetaCentrum Jupyter Notebooks

Sample Jupyter notebooks demonstrating integration with [MetaCentrum](https://metavo.metacentrum.cz/) and [e-INFRA CZ](https://www.e-infra.cz/) services. Each notebook covers one service, includes step-by-step documentation, and is designed to run on [ondemand.metacentrum.cz](https://ondemand.metacentrum.cz/) and [jupyter.e-infra.cz](https://jupyter.e-infra.cz/).

---

## Notebooks

| # | Notebook | Service | Credentials |
|---|----------|---------|-------------|
| 00 | [Environment Check](notebooks/00_environment_check.ipynb) | Diagnostics & credential setup wizard | None |
| 01 | [S3 Object Storage](notebooks/01_s3_object_storage.ipynb) | [CESNET S3 storage](https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service) | S3 endpoint, access key, secret key, bucket |
| 02 | [Invenio Repository](notebooks/02_invenio_repository.ipynb) | [NRP Data Catch-all Repository](https://datarepo.eosc.cz) | NRP API token |
| 03 | [OpenStack API](notebooks/03_openstack_api.ipynb) | [e-INFRA Cloud](https://docs.platforms.cloud.e-infra.cz/en/docs/iaas-cloud/technical-reference/brno-g2-site) | OpenStack application credentials |
| 04 | [Open WebUI Chat API](notebooks/04_open_webui_chat_api.ipynb) | [e-INFRA AI Chat](https://docs.cerit.io/en/docs/ai-as-a-service/chat-ai) | AI API token |
| 05 | [GPU Container + AI Model](notebooks/05_gpu_container_ai_model.ipynb) | Apptainer/Docker with GPU passthrough | None (optional config) |
| 06 | [R Kernel Demo](notebooks/06_r_kernel_demo.ipynb) | R language kernel | None (R kernel required) |
| 07 | [MATLAB Kernel Demo](notebooks/07_matlab_kernel_demo.ipynb) | MATLAB kernel | None (MATLAB kernel required) |

---

## For Reviewers

Each notebook is self-contained, so you only need the one for your service.

1. Clone the repository and install the dependencies for your notebook (see [How to Use](#how-to-use)).
2. Put your own credentials for that service into `.env` -- the variables are listed in `env.example` and at the top of the notebook.
3. Run the notebook top to bottom.

Notebooks are committed without outputs on purpose. Notebooks 01 and 02 create one test object / one draft record and delete it again in their Cleanup section; 03 and 04 only read. Notebooks 06 and 07 need an R or MATLAB kernel and no credentials.

---

## How to Use

### On MetaCentrum / e-INFRA JupyterHub

1. Upload or clone this repository into your JupyterHub home directory.
2. Open a terminal in JupyterLab and run `pip install -e ".[all]"` once (see the table below if you'd rather install only what a specific notebook needs).
3. Open **`00_environment_check.ipynb`** and run all cells -- it verifies your environment and walks you through credential setup with an interactive wizard.
4. Open any other notebook and run it. Each notebook's first cell only *checks* that its dependencies are importable; it never installs anything on your behalf. If something is missing, it prints the exact `pip install -e ".[...]"` command to run.

### Locally

```bash
git clone https://github.com/OmarIbrahim22/metacentrum-notebooks.git
cd metacentrum-notebooks
python -m venv .venv && source .venv/bin/activate   # recommended
pip install -e ".[all]"
jupyter lab
```

Then start with `00_environment_check.ipynb`. `.[all]` installs every notebook's dependencies in one go; use one of the narrower extras below if you only need a subset.

| Extra | Installs | Needed by |
|-------|----------|-----------|
| `.[s3]` | `boto3` | 01 - S3 Object Storage |
| `.[invenio]` | `requests` | 02 - Invenio Repository |
| `.[openstack]` | `openstacksdk` | 03 - OpenStack API |
| `.[openwebui]` | `openai` | 04 - Open WebUI Chat API |
| `.[all]` | all of the above | everything |

Notebooks 00 and 05 need no extras beyond the base `pip install -e .`.

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

**01 -- S3 Object Storage**: Full CRUD cycle using `boto3` -- list buckets, upload a uniquely named test object, download and verify, generate a presigned URL, retrieve metadata, clean up.

**02 -- Invenio Repository**: Invenio REST API for the National Repository Platform (default: Data Catch-all Repository) -- create a draft record, upload a file (three-step process), retrieve draft details, delete the draft. Nothing is published.

**03 -- OpenStack API**: Read-only exploration of e-INFRA OpenStack cloud using `openstacksdk` -- authenticate, list flavors/images, check compute quotas, list servers and networks.

**04 -- Open WebUI Chat API**: OpenAI-compatible API for e-INFRA AI chat -- list models and pick a chat-capable one, simple chat completion, multi-turn conversation, code generation, streaming responses.

**05 -- GPU Container + AI Model**: Detect container runtime (Apptainer/Singularity/Docker), run a basic container, test GPU passthrough with `nvidia-smi`, run PyTorch inference inside a GPU container.

**06 -- R Kernel Demo**: Basic R usage in Jupyter -- vectors and data frames, base R graphics, correlation and linear regression, the built-in `iris` dataset, checking for installed packages.

**07 -- MATLAB Kernel Demo**: MATLAB in Jupyter -- arrays and matrices, plotting, solving a linear system, basic statistics, numerical integration, symbolic math (if the toolbox is available).

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
| `util.check_deps(deps)` | Return the pip names of any missing dependencies |
| `util.require_deps(deps, extra)` | Raise `ImportError` with the install command if anything is missing (never installs) |

---

## Requirements

- Python 3.8+
- Jupyter environment (JupyterLab, JupyterHub, or local)
- Service-specific credentials (see table above)
- For notebook 06: R kernel ([IRkernel](https://irkernel.github.io/))
- For notebook 07: MATLAB kernel

---

*Bachelor thesis project -- Faculty of Informatics, Masaryk University*
