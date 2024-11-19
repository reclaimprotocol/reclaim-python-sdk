from setuptools import setup, find_packages

setup(
    name="reclaim-python-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "canonicaljson>=1.0.0",
        "eth-account>=0.8.0",
        "typing-extensions>=4.5.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.0"
    ],
    python_requires=">=3.7",
    author="Reclaim Protocol",
    author_email="team@reclaimprotocol.org",
    description="Python SDK for the Reclaim Protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/reclaimprotocol/reclaim-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 