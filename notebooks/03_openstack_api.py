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
# # 03 - OpenStack API Integration
#
# ## Goal
#
# Demonstrate authentication and basic operations with OpenStack API using application credentials. This notebook shows how to connect to OpenStack, list compute resources (flavors, images), and understand the platform capabilities.
#
# **Runtime**: ~2-3 minutes
#
# **Documentation**: https://docs.platforms.cloud.e-infra.cz/en/docs/technical-reference/brno-g2-site

# %% [markdown]
# ## What You Will Learn
#
# - How to authenticate with OpenStack using application credentials
# - How to list available compute flavors (VM sizes)
# - How to list available images (OS templates)
# - How to list projects and check quotas
# - How to handle common OpenStack API errors
# - Best practices for safe API exploration

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - Access to e-INFRA CZ OpenStack platform
# - OpenStack application credentials
# - Project membership

# %% [markdown]
# ### Where to Get Credentials
#
# 1. Visit https://dashboard.cloud.e-infra.cz/
# 2. Log in with your credentials
# 3. Navigate to Identity → Application Credentials
# 4. Create a new application credential
# 5. Download the credentials (you can't view the secret again!)
# 6. Note your region name (e.g., `brno-g2`, `liberec3-ngn`)

# %% [markdown]
# ### Required Environment Variables
#
# Add these to your `.env` file:
#
# ```bash
# OS_AUTH_URL=https://identity.cloud.e-infra.cz/v3
# OS_APPLICATION_CREDENTIAL_ID=your_credential_id
# OS_APPLICATION_CREDENTIAL_SECRET=your_credential_secret
# OS_REGION_NAME=brno-g2
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install -e ".[openstack]"
# ```
#
# Run once from the repo root, from a terminal (not from inside a notebook cell).

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

require_deps({"python-dotenv": "dotenv", "openstacksdk": "openstack"}, extra="openstack")
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

import openstack
from openstack.exceptions import OpenStackCloudException
print("✓ openstacksdk imported")

# %% [markdown]
# ### Validate Environment Variables

# %%
print_section("Validating Credentials")

try:
    OS_AUTH_URL = need("OS_AUTH_URL")
    OS_APPLICATION_CREDENTIAL_ID = need("OS_APPLICATION_CREDENTIAL_ID")
    OS_APPLICATION_CREDENTIAL_SECRET = need("OS_APPLICATION_CREDENTIAL_SECRET")
    OS_REGION_NAME = optional("OS_REGION_NAME", "brno-g2")
    
    print("✓ All required environment variables found")
    print(f"\nAuth URL: {OS_AUTH_URL}")
    print(f"Credential ID: {mask(OS_APPLICATION_CREDENTIAL_ID)}")
    print(f"Credential Secret: {mask(OS_APPLICATION_CREDENTIAL_SECRET)}")
    print(f"Region: {OS_REGION_NAME}")
    
except RuntimeError as e:
    print(f"✗ Missing environment variable: {e}")
    print("\nPlease configure your .env file with:")
    print("  OS_AUTH_URL=https://identity.cloud.e-infra.cz/v3")
    print("  OS_APPLICATION_CREDENTIAL_ID=your_id")
    print("  OS_APPLICATION_CREDENTIAL_SECRET=your_secret")
    print("  OS_REGION_NAME=brno-g2")
    print("\nSee: https://docs.platforms.cloud.e-infra.cz/")
    raise

# %% [markdown]
# ### Create OpenStack Connection

# %%
print_section("Creating OpenStack Connection")

try:
    conn = openstack.connect(
        auth_url=OS_AUTH_URL,
        application_credential_id=OS_APPLICATION_CREDENTIAL_ID,
        application_credential_secret=OS_APPLICATION_CREDENTIAL_SECRET,
        region_name=OS_REGION_NAME,
        auth_type="v3applicationcredential",
    )
    
    print("✓ OpenStack connection created successfully")
    
except OpenStackCloudException as e:
    print(fmt_error(e, label="create OpenStack connection"))
    print("\nCommon causes:")
    print("  - Invalid application credentials")
    print("  - Wrong auth URL")
    raise
except Exception as e:
    print(fmt_error(e, label="create OpenStack connection"))
    print("\nCommon causes:")
    print("  - Invalid credentials")
    print("  - Wrong auth URL")
    print("  - Network connectivity issues")
    raise

# %% [markdown]
# ## Minimal Working Demo
#
# ### 1. Verify Authentication

# %%
print_section("Verifying Authentication")

try:
    # Get current project info
    current_project = conn.current_project
    
    if current_project:
        print("✓ Authentication successful!")
        print(f"\nCurrent Project:")
        print(f"  Name: {current_project.get('name', 'N/A')}")
        print(f"  ID: {current_project.get('id', 'N/A')}")
        print(f"  Domain: {current_project.get('domain_id', 'N/A')}")
    else:
        print("⚠️  Authentication succeeded but no project info available")
        
except OpenStackCloudException as e:
    print(fmt_error(e, label="authentication verification"))
    print("  Check your application credential ID/secret and auth URL.")
except Exception as e:
    print(fmt_error(e, label="authentication verification"))

# %% [markdown]
# ### 2. List Available Flavors (VM Sizes)

# %%
print_section("Listing Compute Flavors")

try:
    flavors = list(conn.compute.flavors())
    
    if flavors:
        print(f"✓ Found {len(flavors)} flavor(s)")
        print("\nSample flavors (first 10):\n")
        
        # Sort by RAM for better display
        sorted_flavors = sorted(flavors, key=lambda f: f.ram)[:10]
        
        print(f"{'Name':<30} {'VCPUs':>6} {'RAM (MB)':>10} {'Disk (GB)':>10}")
        print("-" * 60)
        
        for flavor in sorted_flavors:
            print(f"{flavor.name:<30} {flavor.vcpus:>6} {flavor.ram:>10} {flavor.disk:>10}")
    else:
        print("⚠️  No flavors found (may be a permission issue)")
        
except OpenStackCloudException as e:
    print(fmt_error(e, label="list flavors"))
    print("\nCommon causes:")
    print("  - No compute service access")
    print("  - Wrong region name")
    print("  - Insufficient permissions")
except Exception as e:
    print(fmt_error(e, label="list flavors — unexpected error"))

# %% [markdown]
# ### 3. List Available Images (OS Templates)

# %%
print_section("Listing Available Images")

try:
    # List only active images to reduce noise
    images = list(conn.compute.images())
    
    if images:
        print(f"✓ Found {len(images)} image(s)")
        print("\nSample images (first 10):\n")
        
        for i, image in enumerate(images[:10], 1):
            name = image.name or "Unnamed"
            status = image.status or "Unknown"
            print(f"  {i:2}. {name:<50} [{status}]")
            
        # for full list comment

        if len(images) > 10:
            print(f"\n  ... and {len(images) - 10} more")

        # until here
    else:
        print("⚠️  No images found")
        
except OpenStackCloudException as e:
    print(fmt_error(e, label="list images"))
except Exception as e:
    print(fmt_error(e, label="list images — unexpected error"))

# %% [markdown]
# ### 4. Check Compute Quotas

# %%
print_section("Checking Compute Quotas")

QUOTA_OK = False
try:
    # Get current project ID
    project_id = conn.current_project_id
    
    # Get compute quotas
    quotas = conn.get_compute_quotas(project_id)
    
    if quotas:
        QUOTA_OK = True
        print("✓ Quota information retrieved\n")

        important_quotas = [
            ("Instances", "instances"),
            ("VCPUs", "cores"),
            ("RAM (MB)", "ram"),
            ("Volumes", "volumes"),
            ("Floating IPs", "floating_ips"),
        ]
        
        print(f"{'Resource':<20} {'Limit':>10}")
        print("-" * 32)
        
        for label, key in important_quotas:
            value = getattr(quotas, key, "N/A")
            if value == -1:
                value = "Unlimited"
            print(f"{label:<20} {str(value):>10}")
    else:
        print("⚠️  No quota information available")
        
except OpenStackCloudException as e:
    QUOTA_OK = False
    print(fmt_error(e, label="quota check"))
    print("  This may be normal — quota API requires additional permissions.")
except Exception as e:
    QUOTA_OK = False
    print(fmt_error(e, label="quota check — unexpected error"))

# %% [markdown]
# ### 5. List Current Servers (if any)

# %%
print_section("Listing Current Servers")

try:
    servers = list(conn.compute.servers())
    
    if servers:
        print(f"✓ Found {len(servers)} server(s)\n")
        
        print(f"{'Name':<30} {'Status':<12} {'Flavor':<20}")
        print("-" * 65)
        
        for server in servers:
            name = server.name or "Unnamed"
            status = server.status or "Unknown"
            flavor_id = server.flavor.get('id', 'N/A') if server.flavor else 'N/A'
            
            print(f"{name:<30} {status:<12} {flavor_id:<20}")
    else:
        print("✓ No servers currently running in this project")
        print("  (This is normal for a fresh project)")
        
except OpenStackCloudException as e:
    print(fmt_error(e, label="list servers"))
except Exception as e:
    print(fmt_error(e, label="list servers — unexpected error"))

# %% [markdown]
# ### 6. Network Information

# %%
print_section("Network Information")

try:
    networks = list(conn.network.networks())
    
    if networks:
        print(f"✓ Found {len(networks)} network(s)\n")
        
        for net in networks:
            name = net.name or "Unnamed"
            is_external = "External" if net.is_router_external else "Internal"
            status = net.status or "Unknown"
            
            print(f"  - {name}")
            print(f"    Type: {is_external}, Status: {status}")
            print(f"    ID: {net.id}")
            print()
    else:
        print("⚠️  No networks found")
        
except OpenStackCloudException as e:
    print(fmt_error(e, label="network info"))
    print("  Network service may not be accessible with these credentials.")
except Exception as e:
    print(fmt_error(e, label="network info — unexpected error"))

# %% [markdown]
# ## Cleanup
#
# This notebook only performs read operations, so no cleanup is needed.
#
# **Important**: If you were to create resources (servers, volumes, etc.), you should always clean them up to avoid charges or quota exhaustion.

# %%
print_section("Cleanup")

print("✓ No cleanup needed - this notebook only performed read operations")
print("\n⚠️  If you create resources in the future, remember to:")
print("  1. Delete all servers/instances")
print("  2. Delete volumes")
print("  3. Release floating IPs")
print("  4. Delete security groups (if custom ones were created)")

# %% [markdown]
# ## Troubleshooting
#
# ### Common Errors
#
# **401 Unauthorized**
# - Invalid application credentials
# - Credentials expired
# - Wrong auth URL
# - Check your credential ID and secret
#
# **403 Forbidden**
# - Application credential doesn't have required permissions
# - Project access revoked
# - Recreate credentials with appropriate roles
#
# **404 Not Found - Endpoint not found**
# - Wrong region name
# - Service not available in this region
# - Check `OS_REGION_NAME` value
#
# **Connection timeout / Network errors**
# - Cannot reach OpenStack endpoints
# - Firewall blocking access
# - VPN required?
#
# **Empty lists (no flavors/images)**
# - May be normal in some projects
# - Check if you're in the right region
# - Verify project membership

# %% [markdown]
# ### Region Issues
#
# e-INFRA CZ has multiple regions:
# - `brno-g2` - Brno site (G2)
# - `liberec3-ngn` - Liberec site
# - `praha1` - Prague site
#
# Make sure you use the region your project is in.

# %% [markdown]
# ### Debugging Tips
#
# ```python
# # Enable debug logging
# import logging
# openstack.enable_logging(debug=True)
#
# # Check SDK version
# import openstack
# print(f"OpenStack SDK version: {openstack.version.__version__}")
#
# # List all available services
# for service in conn.service_catalog:
#     print(f"{service.type}: {service.name}")
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand OpenStack API basics, you can:
#
# ### Advanced Operations
#
# - **Create instances** - Launch VMs programmatically
# - **Manage volumes** - Create and attach block storage
# - **Network management** - Set up networks, subnets, routers
# - **Security groups** - Configure firewall rules
# - **Floating IPs** - Assign public IPs to instances
# - **Snapshots** - Backup instances and volumes

# %% [markdown]
# ### Integration Ideas
#
# - Auto-scale compute based on workload
# - Create temporary VMs for batch processing
# - Provision GPU instances for ML training
# - Build infrastructure-as-code workflows
# - Integrate with container orchestration

# %% [markdown]
# ### Safety Tips
#
# When creating resources:
# - Always use try/finally for cleanup
# - Set resource tags for tracking
# - Monitor quota usage
# - Delete resources when done
# - Use smallest flavors for testing

# %% [markdown]
# ### Related Notebooks
#
# - **05_gpu_container_ai_model.ipynb** - Launch GPU instances for AI
# - **01_s3_object_storage.ipynb** - Combine with object storage

# %% [markdown]
# ### Documentation
#
# - [e-INFRA CZ Cloud Docs](https://docs.platforms.cloud.e-infra.cz/)
# - [OpenStack SDK Documentation](https://docs.openstack.org/openstacksdk/)
# - [OpenStack API Reference](https://docs.openstack.org/api-ref/)
# - [Brno G2 Site Guide](https://docs.platforms.cloud.e-infra.cz/en/docs/technical-reference/brno-g2-site)
