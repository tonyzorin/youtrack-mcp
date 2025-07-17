FROM python:3.13-alpine

WORKDIR /app

# Install build dependencies and compile Git from source to get the latest version
RUN apk add --no-cache wget tar gcc musl-dev python3-dev libffi-dev openssl-dev \
                       zlib-dev curl-dev expat-dev gettext make autoconf && \
    cd /tmp && \
    wget https://mirrors.edge.kernel.org/pub/software/scm/git/git-2.50.1.tar.gz && \
    tar -xzf git-2.50.1.tar.gz && \
    cd git-2.50.1 && \
    make configure && \
    ./configure --prefix=/usr/local && \
    make all && \
    make install && \
    /usr/local/bin/git --version && \
    cd / && rm -rf /tmp/git-* && \
    apk del wget tar make autoconf

# Make sure the new Git is in PATH  
ENV PATH="/usr/local/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import mcp; print(dir(mcp))"

# Copy the rest of the application
COPY . .

# Default environment variables (will be overridden at runtime)
ENV APP_VERSION="1.4.0"
ENV MCP_SERVER_NAME="youtrack-mcp"
ENV MCP_SERVER_DESCRIPTION="YouTrack MCP Server"
ENV MCP_DEBUG="false"
ENV YOUTRACK_VERIFY_SSL="true"

# Run the MCP server in stdio mode for Claude integration by default
CMD ["python", "main.py", "--transport", "stdio"]