```python
from setuptools import setup, find_packages
import os

def read_requirements(file_path="requirements.txt"):
    """Utility function to read the requirements from a file."""
    if os.path.isfile(file_path):
        with open(file_path, 'r') as req_file:
            return req_file.read().splitlines()
    return []

def read_long_description(file_path="README.md"):
    """Utility function to read the long description from a file."""
    with open(file_path, 'r', encoding='utf-8') as readme_file:
        return readme_file.read()

setup(
    name="cgai-gh-bot",
    version="0.0.1",
    description="Cowgirl AI Github GPT Bot",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Cowgirl-AI/github_gpt_bot",
    author="Tera Earlywine",
    author_email="tera@cowgirlai.tech",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=read_requirements(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cgai-gh=cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
```