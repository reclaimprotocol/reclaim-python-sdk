from setuptools import setup, find_packages

setup(
    name="reclaim_python_sdk",
    version="1.0.3",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests*"]),
    include_package_data=True,
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
        "safe-pysha3>=1.0.2",
        "json-canonical>=2.0.0",
    ],
    python_requires=">=3.7",
    author="Reclaim Protocol",
    author_email="engineering@creatoros.co",
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
        "wheel",
        "setuptools>=42",
    ],
) 