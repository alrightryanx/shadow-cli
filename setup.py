from setuptools import setup, find_packages
import os

# Read the README for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="shadow-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "psutil",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "shadow=shadow_cli.main:main",
        ],
    },
    author="Ryan Cartwright",
    author_email="contact@ryancartwright.com",
    description="Unified CLI for the ShadowAI ecosystem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alrightryanx/shadow-cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
