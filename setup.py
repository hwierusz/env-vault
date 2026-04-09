from setuptools import setup, find_packages

setup(
    name="env-vault",
    version="0.1.0",
    description="CLI tool for managing environment variables with encrypted storage",
    author="env-vault contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "click>=8.0",
        "cryptography>=41.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "env-vault=env_vault.cli:cli",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities",
    ],
)
