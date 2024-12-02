from setuptools import setup, find_packages

setup(
    name="reclaim-python-sdk",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "web3>=6.0.0",
        "canonicaljson>=1.0.0",
        "eth-account>=0.8.0",
        "typing-extensions>=4.5.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
        "requests>=2.32.3",
        "httpx>=0.24.0",
        "asyncio>=3.4.3",
        "pysha3>=1.0.2",
        "json-canonical>=2.0.0",
    ],
    python_requires=">=3.7",
    author="Reclaim Protocol",
    author_email="kushal@creatoros.co",
    description="Python SDK for the Reclaim Protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/reclaimprotocol/reclaim-python-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=[
        "wheel>=0.40.0",
        "setuptools>=42",
        "pysha3>=1.0.2",
    ],
) 