# syntax=docker/dockerfile:1
#
# JiuZhang SDK notebook runtime image.
#
# Build:
#   docker build -t jiuzhang-sdk-notebook:local .
#
# Run JupyterLab:
#   docker run --rm -it -p 8888:8888 jiuzhang-sdk-notebook:local
#
# Execute the full notebook once:
#   docker run --rm -it -e JIUZHANG_API_KEY=<cloud-api-key> jiuzhang-sdk-notebook:local \
#     jupyter nbconvert --to notebook --execute /workspace/sdk_usage.ipynb \
#       --output /tmp/sdk_full_usage.executed.ipynb \
#       --ExecutePreprocessor.timeout=1900

FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /workspace

RUN python -m pip install --upgrade pip "setuptools<81" wheel

# Install notebook execution/runtime tools and Xanadu ecosystem packages.
#
# Notes:
# - `strawberryfields` pulls `quantum-blackbird`, `quantum-xir`, and
#   `xanadu-cloud-client`.
# - Python 3.12 is used because the current jiuzhang-sdk package requires
#   Python >= 3.12.
# - `pennylane==0.42.3` keeps compatibility with the NumPy/SciPy range needed
#   by Strawberry Fields 0.23.
# - `thewalrus==0.21.0` plus SciPy < 1.14 keeps the legacy
#   `scipy.integrate.simps` API required by Strawberry Fields.
# - Do not install the legacy PyPI package named `xir`; Strawberry Fields uses
#   `quantum-xir`, which exposes the import module named `xir`.
# - `mrmustard==0.3.0` is used as a stable TensorFlow-based local photonics
#   design dependency.
# - The legacy PyPI package named `blackbird` is intentionally not installed;
#   Strawberry Fields uses `quantum-blackbird`, while `blackbird` has an old
#   build script that is brittle under modern isolated builds.
RUN python -m pip install \
        "httpx>=0.27,<0.29" \
        "ipykernel>=7" \
        "jupyterlab>=4" \
        "matplotlib>=3.10" \
        "nbclient>=0.10" \
        "nbconvert>=7" \
        "requests>=2.32" \
        "numpy>=1.26,<2" \
        "scipy>=1.10,<1.14" \
        "pennylane==0.42.3" \
        "strawberryfields==0.23.0" \
        "thewalrus==0.21.0" \
        "mrmustard==0.3.0" \
        "quantum-xir==0.2.2" \
        "xanadu-cloud-client==0.3.2"

# Install the SDK from this GitLab repository source tree, not from PyPI.
COPY code/ /workspace/code/
RUN python -m pip install -e "/workspace/code[jupyter]"

# Copy runnable notebooks and local validation helpers into the image.
COPY sdk_usage.ipynb /workspace/sdk_full_usage.ipynb
COPY local_test/ /workspace/local_test/
COPY doc/cloud-platform/sdk_test.ipynb /workspace/doc/cloud-platform/sdk_test.ipynb

RUN python -m ipykernel install --sys-prefix --name jiuzhang-sdk --display-name "Python (jiuzhang-sdk)" \
    && python - <<'PY'
import jiuzhang
import pennylane
import strawberryfields
import thewalrus
import xir
import xcc

print("jiuzhang", jiuzhang.__version__)
print("pennylane", pennylane.__version__)
print("strawberryfields", strawberryfields.__version__)
print("thewalrus", thewalrus.__version__)
print("xir", xir.__version__)
print("xanadu-cloud-client", xcc.__version__)
PY

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=", "--ServerApp.password="]
