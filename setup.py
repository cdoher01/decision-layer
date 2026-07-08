from pathlib import Path

from setuptools import find_packages, setup


setup(
    name="decision-layer",
    version="0.1.0",
    description="A governed decision layer for any AI agent or command-line harness.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["decision_layer", "decision_layer.*"]),
    python_requires=">=3.9",
    entry_points={"console_scripts": ["decision=decision_layer.cli:main"]},
    license="MIT",
)
