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
# # 01 - S3 Object Storage Integration
#
# ## Goal
#
# Demonstrate authentication and basic operations with CESNET S3 Object Storage using the boto3 SDK. This notebook shows how to list buckets, upload/download objects, generate presigned URLs, and handle common errors.
#
# **Runtime**: ~2-3 minutes
#
# **Documentation**: https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service

# %% [markdown]
# ## What You Will Learn
#
# - How to authenticate with S3-compatible object storage
# - How to list buckets and objects
# - How to upload and download files
# - How to generate presigned URLs for temporary access
# - How to handle common S3 errors
# - How to properly clean up test objects

# %% [markdown]
# ## Prerequisites
#
# ### Access Requirements
#
# You need:
# - Access to CESNET S3 Object Storage
# - S3 access key and secret key
# - A bucket (existing or create one)

# %% [markdown]
# ### Where to Get Credentials
#
# 1. Register for the S3 service (join a Virtual Organisation or register for the personal S3 service) — see [Getting Access to CESNET S3](https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-getting-access)
# 2. Wait about 30 minutes for the registration to propagate
# 3. Log in to https://gatekeeper.du.cesnet.cz
# 4. Press **+ New key**, name the key pair, and save the access key and secret key (the secret key is shown only once)
# 5. Note the S3 endpoint address shown above the list of keys

# %% [markdown]
# ### Required Environment Variables
#
# Add these to your `.env` file:
#
# ```bash
# S3_ENDPOINT=https://s3.cl4.du.cesnet.cz   # use the endpoint shown in Gatekeeper
# S3_ACCESS_KEY=your_access_key_here
# S3_SECRET_KEY=your_secret_key_here
# S3_BUCKET=your-bucket-name
# ```

# %% [markdown]
# ### Installation
#
# ```bash
# pip install -e ".[s3]"
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

require_deps({"python-dotenv": "dotenv", "boto3": "boto3"}, extra="s3")
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

from mcnb.env import need, mask
from mcnb.util import print_section, fmt_error, safe_get
print("✓ mcnb imported")

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
print("✓ boto3 imported")

# %% [markdown]
# ### Validate Environment Variables

# %%
print_section("Validating Credentials")

try:
    S3_ENDPOINT = need("S3_ENDPOINT")
    S3_ACCESS_KEY = need("S3_ACCESS_KEY")
    S3_SECRET_KEY = need("S3_SECRET_KEY")
    S3_BUCKET = need("S3_BUCKET")
    
    print("✓ All required environment variables found")
    print(f"\nEndpoint: {S3_ENDPOINT}")
    print(f"Access Key: {mask(S3_ACCESS_KEY)}")
    print(f"Secret Key: {mask(S3_SECRET_KEY)}")
    print(f"Bucket: {S3_BUCKET}")
    
except RuntimeError as e:
    print(f"✗ Missing environment variable: {e}")
    print("\nPlease configure your .env file with:")
    print("  S3_ENDPOINT=https://s3.cl4.du.cesnet.cz")
    print("  S3_ACCESS_KEY=your_access_key")
    print("  S3_SECRET_KEY=your_secret_key")
    print("  S3_BUCKET=your-bucket-name")
    print("\nSee: https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service")
    raise

# %% [markdown]
# ### Create S3 Client

# %%
print_section("Creating S3 Client")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)

print("✓ S3 client created successfully")

# %% [markdown]
# ## Minimal Working Demo
#
# **If a step fails**: the notebook stops at that cell. Jump to the
# **Cleanup** section and run its cell so the test object in `mcnb-demo/`
# is not left in your bucket.
#
# ### 1. List Buckets (Validate Access)

# %%
print_section("Listing Buckets")

try:
    response = s3_client.list_buckets()
    buckets = response.get("Buckets", [])
    
    if buckets:
        print(f"✓ Found {len(buckets)} bucket(s):\n")
        for bucket in buckets:
            print(f"  - {bucket['Name']} (created: {bucket['CreationDate']})")
    else:
        print("No buckets found. You may need to create one first.")
        
    # Check if our target bucket exists
    bucket_names = [b["Name"] for b in buckets]
    if S3_BUCKET in bucket_names:
        print(f"\n✓ Target bucket '{S3_BUCKET}' found")
    else:
        print(f"\n⚠️  Warning: Target bucket '{S3_BUCKET}' not found in list")
        print("   This might be due to permissions or the bucket may not exist yet.")
        
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Error listing buckets: {error_code}")
    print(f"  Message: {error_msg}")
    print("\n  Common causes:")
    print("    - Invalid credentials")
    print("    - Wrong endpoint URL")
    print("    - Network/firewall issues")
    raise

# %% [markdown]
# ### 2. Upload a Test Object

# %%
print_section("Uploading Test Object")

# Create test content. The key is unique per run, so this demo can never
# overwrite or delete an object that already exists in your bucket.
_now = datetime.now()
test_key = f"mcnb-demo/hello-{_now.strftime('%Y%m%dT%H%M%S')}.txt"
test_content = "Hello from MetaCentrum Jupyter notebook!\n" + \
               f"Uploaded at: {_now}\n"

print(f"Uploading to: s3://{S3_BUCKET}/{test_key}")
print(f"Content size: {len(test_content)} bytes")

try:
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=test_key,
        Body=test_content.encode("utf-8"),
        ContentType="text/plain",
    )
    print(f"\n✓ Upload successful!")
    
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"\n✗ Upload failed: {error_code}")
    print(f"  Message: {error_msg}")
    print("\n  Common causes:")
    print("    - Bucket does not exist (NoSuchBucket)")
    print("    - No write permission (AccessDenied)")
    print("    - Quota exceeded")
    raise

# %% [markdown]
# ### 3. List Objects in Bucket

# %%
print_section("Listing Objects in Bucket")

try:
    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET,
        Prefix="mcnb-demo/",  # Only list objects in mcnb-demo/ prefix
        MaxKeys=10,
    )

    if "Contents" in response:
        objects = response["Contents"]
        print(f"Found {len(objects)} object(s) with prefix 'mcnb-demo/':\n")
        
        for obj in objects:
            size_kb = obj["Size"] / 1024
            print(f"  - {obj['Key']}")
            print(f"    Size: {size_kb:.2f} KB")
            print(f"    Last modified: {obj['LastModified']}")
            print()
    else:
        print("No objects found with prefix 'mcnb-demo/'")
        
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Error listing objects: {error_code}")
    print(f"  Message: {error_msg}")
    raise

# %% [markdown]
# ### 4. Download and Verify Object

# %%
print_section("Downloading Test Object")

try:
    response = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key=test_key,
    )
    
    downloaded_content = response["Body"].read().decode("utf-8")
    
    print(f"✓ Download successful!")
    print(f"\nContent type: {response['ContentType']}")
    print(f"Content length: {response['ContentLength']} bytes")
    print(f"\nDownloaded content:\n")
    print("-" * 60)
    print(downloaded_content)
    print("-" * 60)
    
    # Verify content matches
    if downloaded_content == test_content:
        print("\n✓ Content verification: PASSED")
    else:
        print("\n✗ Content verification: FAILED")
        
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Download failed: {error_code}")
    print(f"  Message: {error_msg}")
    if error_code == "NoSuchKey":
        print("  The object does not exist. Was the upload step skipped or did it fail?")
    raise

# %% [markdown]
# ### 5. Generate Presigned URL (Optional)

# %%
print_section("Generating Presigned URL")

try:
    # Generate URL valid for 1 hour
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET,
            "Key": test_key,
        },
        ExpiresIn=3600,  # 1 hour
    )
    
    print("✓ Presigned URL generated successfully")
    print(f"\nURL (valid for 1 hour):\n")
    print(presigned_url)
    print("\nYou can access this URL in a browser without credentials.")
    
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Failed to generate presigned URL: {error_code}")
    print(f"  Message: {error_msg}")
except Exception as e:
    print(fmt_error(e, label="presigned URL"))

# %% [markdown]
# ### 6. Get Object Metadata

# %%
print_section("Getting Object Metadata")

try:
    response = s3_client.head_object(
        Bucket=S3_BUCKET,
        Key=test_key,
    )
    
    print(f"✓ Object metadata retrieved:\n")
    print(f"  Content Type: {response.get('ContentType', 'N/A')}")
    print(f"  Content Length: {response.get('ContentLength', 0)} bytes")
    print(f"  Last Modified: {response.get('LastModified', 'N/A')}")
    print(f"  ETag: {response.get('ETag', 'N/A')}")
    
    if "Metadata" in response and response["Metadata"]:
        print(f"\n  Custom Metadata:")
        for key, value in response["Metadata"].items():
            print(f"    {key}: {value}")
    
except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Failed to get metadata: {error_code}")
    print(f"  Message: {error_msg}")

# %% [markdown]
# ## Cleanup
#
# Delete the test object we created:

# %%
print_section("Cleanup: Deleting Test Object")

try:
    s3_client.delete_object(
        Bucket=S3_BUCKET,
        Key=test_key,
    )
    print(f"✓ Test object deleted: {test_key}")
    
    # Verify deletion
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=test_key)
        print("⚠️  Object still exists (eventual consistency?)")
    except ClientError as e:
        if safe_get(e.response, "Error", "Code") == "404":
            print("✓ Deletion verified")
        else:
            error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
            print(f"⚠️  Verification check returned unexpected error: {error_code}")
            raise

except ClientError as e:
    error_code = safe_get(e.response, "Error", "Code", default="UNKNOWN")
    error_msg = safe_get(e.response, "Error", "Message", default=str(e))
    print(f"✗ Cleanup failed: {error_code}")
    print(f"  Message: {error_msg}")
    print("  You may need to delete the object manually")

# %% [markdown]
# ## Troubleshooting
#
# ### Common Errors
#
# **SignatureDoesNotMatch / InvalidAccessKeyId**
# - Wrong access key or secret key
# - Check your credentials in `.env` file
# - Verify endpoint URL is correct
#
# **NoSuchBucket**
# - Bucket doesn't exist
# - Typo in bucket name
# - Bucket belongs to a different account or Virtual Organisation
#
# **AccessDenied / 403**
# - Credentials don't have permission for this operation
# - Bucket policy may restrict access
# - Check that the key was generated for the Virtual Organisation that owns the bucket
#
# **EndpointConnectionError**
# - Wrong endpoint URL
# - Network connectivity issues
# - Firewall blocking connection
#
# **SlowDown / RequestLimitExceeded**
# - Too many requests too quickly
# - Add delays between operations
# - Implement exponential backoff

# %% [markdown]
# ### Debugging Tips
#
# ```python
# # Enable debug logging
# import logging
# logging.basicConfig(level=logging.DEBUG)
#
# # Check boto3 version
# import boto3
# print(f"boto3 version: {boto3.__version__}")
# ```

# %% [markdown]
# ## Next Steps
#
# Now that you understand S3 object storage basics, you can:
#
# ### Advanced Operations
#
# - **Multipart uploads** for large files
# - **Batch operations** for multiple objects
# - **Lifecycle policies** for automatic cleanup
# - **Versioning** to track object changes
# - **Server-side encryption** for sensitive data

# %% [markdown]
# ### Integration Ideas
#
# - Store model checkpoints during training
# - Archive processed datasets
# - Share results with presigned URLs
# - Build a simple data pipeline

# %% [markdown]
# ### Related Notebooks
#
# - **02_invenio_repository.ipynb** - Repository integration
# - **05_gpu_container_ai_model.ipynb** - Use S3 for model storage

# %% [markdown]
# ### Documentation
#
# - [CESNET S3 Service Docs](https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service)
# - [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
# - [AWS S3 API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)
