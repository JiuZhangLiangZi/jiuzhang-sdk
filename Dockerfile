# JiuZhang SDK JupyterHub singleuser image.
#
# Build:
#   docker build -t jiuzhang-sdk-notebook:v0.1.0 .
#
# Simulate the ACK initContainer locally:
#   docker run --rm --user root \
#     -v jiuzhang-sdk-home:/home/jovyan \
#     jiuzhang-sdk-notebook:v0.1.0 \
#     python3 /opt/jiuzhang/init/init-home.py
#
# Execute the bundled notebook from the initialized home:
#   docker run --rm \
#     -v jiuzhang-sdk-home:/home/jovyan \
#     -e JIUZHANG_API_KEY=<cloud-api-key> \
#     -e JIUZHANG_PROJECT_ID=<project-id> \
#     jiuzhang-sdk-notebook:v0.1.0 \
#     /opt/conda/envs/jiuzhang-sdk/bin/jupyter nbconvert --to notebook \
#       --execute /home/jovyan/sdk_usage.ipynb \
#       --output /tmp/sdk_usage.executed.ipynb \
#       --ExecutePreprocessor.timeout=2100

FROM quay.io/jupyterhub/singleuser:5.4.3

USER root

ARG CONDA_MAIN_CHANNEL=https://mirrors.ustc.edu.cn/anaconda/pkgs/main
ARG CONDA_R_CHANNEL=https://mirrors.ustc.edu.cn/anaconda/pkgs/r

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NB_USER=jovyan \
    NB_UID=1000 \
    NB_GID=100 \
    HOME=/home/jovyan \
    JIUZHANG_HOME_TEMPLATE=/opt/jiuzhang/init/user-home-template \
    JUPYTER_ENABLE_LAB=yes

WORKDIR /opt/jiuzhang/app

# JupyterHub singleuser 5.4.3 currently ships with Python 3.13. The SDK demo
# and the Xanadu local-programming stack are kept in a Python 3.12 conda env.
RUN mamba create --override-channels --yes --name jiuzhang-sdk \
        --channel ${CONDA_MAIN_CHANNEL} \
        --channel ${CONDA_R_CHANNEL} \
        python=3.12 pip \
    && mamba clean --all --force-pkgs-dirs --yes

RUN /opt/conda/envs/jiuzhang-sdk/bin/python -m pip install --upgrade pip wheel "setuptools<81"

# Notebook execution/runtime tools and Xanadu local-programming packages.
#
# `strawberryfields` brings `quantum-blackbird`, `quantum-xir`, and
# `xanadu-cloud-client`; versions are pinned around the Python 3.12-compatible
# range used by this SDK demo image.
RUN /opt/conda/envs/jiuzhang-sdk/bin/python -m pip install \
        "httpx>=0.27,<0.29" \
        "ipykernel>=6" \
        "ipython>=8" \
        "jupyterlab>=4" \
        "matplotlib>=3.8" \
        "nbclient>=0.10" \
        "nbconvert>=7" \
        "nbformat>=5" \
        "requests>=2.32" \
        "numpy>=1.26,<2" \
        "scipy>=1.10,<1.14" \
        "pennylane==0.42.3" \
        "strawberryfields==0.23.0" \
        "thewalrus==0.21.0" \
        "quantum-xir==0.2.2" \
        "xanadu-cloud-client==0.3.2"

# Install the SDK from this repository source tree, not from PyPI.
COPY code/ /opt/jiuzhang/app/code/
RUN /opt/conda/envs/jiuzhang-sdk/bin/python -m pip install -e "/opt/jiuzhang/app/code[jupyter]"

# Bundle files for the root initContainer. The directory name intentionally
# describes the target user home template instead of using a generic welcome.
RUN mkdir -p ${JIUZHANG_HOME_TEMPLATE}
COPY usage/sdk_usage.ipynb ${JIUZHANG_HOME_TEMPLATE}/sdk_usage.ipynb
COPY docker/init-home.py /opt/jiuzhang/init/init-home.py
RUN chmod 755 /opt/jiuzhang/init/init-home.py \
    && /opt/conda/envs/jiuzhang-sdk/bin/python - <<'PY'
import json
from pathlib import Path

path = Path("/opt/jiuzhang/init/user-home-template/sdk_usage.ipynb")
data = json.loads(path.read_text(encoding="utf-8"))
data.setdefault("metadata", {})["kernelspec"] = {
    "display_name": "Python (jiuzhang-sdk)",
    "language": "python",
    "name": "jiuzhang-sdk",
}
data["metadata"].setdefault("language_info", {})["name"] = "python"
path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
PY

RUN /opt/conda/envs/jiuzhang-sdk/bin/python -m ipykernel install \
        --sys-prefix \
        --name jiuzhang-sdk \
        --display-name "Python (jiuzhang-sdk)" \
    && /opt/conda/envs/jiuzhang-sdk/bin/python -m ipykernel install \
        --prefix=/opt/conda \
        --name jiuzhang-sdk \
        --display-name "Python (jiuzhang-sdk)" \
    && /opt/conda/envs/jiuzhang-sdk/bin/python - <<'PY'
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

RUN chown -R root:root /opt/jiuzhang/init \
    && find /opt/jiuzhang/init -type d -exec chmod 755 {} \; \
    && find /opt/jiuzhang/init -type f -exec chmod 644 {} \; \
    && chmod 755 /opt/jiuzhang/init/init-home.py \
    && mkdir -p ${HOME} \
    && chown -R ${NB_UID}:${NB_GID} ${HOME} \
    && chmod 755 ${HOME}

USER ${NB_UID}
WORKDIR ${HOME}

EXPOSE 8888
CMD ["start-singleuser.py"]
