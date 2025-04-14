#!/usr/bin/env python3
import os
from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read version from version.py if exists, otherwise use default
version = "0.1.0"
if os.path.exists("youtrack_mcp/version.py"):
    with open("youtrack_mcp/version.py", "r", encoding="utf-8") as f:
        exec(f.read())
        version = __version__  # noqa: F821

setup(
    name="youtrack-mcp",
    version=version,
    description="A Model Context Protocol server for JetBrains YouTrack",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="YouTrack MCP Team",
    author_email="info@example.com",
    url="https://github.com/youtrack-mcp/youtrack-mcp",
    packages=find_packages(exclude=["tests"]),
    py_modules=["main"],  # Include main.py as a module
    entry_points={
        "console_scripts": [
            "youtrack-mcp=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "mcp-python-sdk>=0.1.0",  # Use the PyPI package once available
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.1.0",
            "flake8>=4.0.1",
            "mypy>=0.931",
            "isort>=5.10.1",
            "pytest-cov>=3.0.0",
        ],
    },
    include_package_data=True,
    project_urls={
        "Bug Reports": "https://github.com/youtrack-mcp/youtrack-mcp/issues",
        "Source": "https://github.com/youtrack-mcp/youtrack-mcp",
        "Documentation": "https://github.com/youtrack-mcp/youtrack-mcp/blob/main/README.md",
    },
) 