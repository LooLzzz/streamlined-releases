FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

ARG GIT_CLIFF_VERSION=2.12.0
ARG TARGETARCH

# install system dependencies
RUN apt-get update \
    && apt-get install -y \
    git \
    wget \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# fetch latest git-cliff version
# RUN version=$(curl -Ls -o /dev/null -w %{url_effective} https://github.com/orhun/git-cliff/releases/latest)
# RUN version=${version##*/v}

# install git-cliff
RUN case "${TARGETARCH}" in \
        arm64) ARCH="aarch64" ;; \
        *)     ARCH="x86_64"  ;; \
    esac \
    && wget -O /tmp/git-cliff.tar.gz "https://github.com/orhun/git-cliff/releases/download/v${GIT_CLIFF_VERSION}/git-cliff-${GIT_CLIFF_VERSION}-${ARCH}-unknown-linux-gnu.tar.gz"
RUN tar -xvzf /tmp/git-cliff.tar.gz -C /tmp
RUN mv /tmp/git-cliff-${GIT_CLIFF_VERSION}/git-cliff /usr/local/bin/git-cliff
RUN rm -rf /tmp/git-cliff*

# copy the application code
COPY . .

# install Python dependencies
RUN uv pip install --system -e .

# ENTRYPOINT [ "uv", "run", "-m" ]
ENTRYPOINT [ "python3", "-m" ]
CMD [ "streamlined_releases" ]