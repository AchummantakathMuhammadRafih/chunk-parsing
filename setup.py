from setuptools import setup, find_packages

setup(
    name="media-transcriber",
    version="1.0.0",
    description="Modular CLI and Python framework for transcribing audio and video files using Whisper.",
    author="Muhammad Rafih",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "openai-whisper",
        "gradio>=4.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "media-transcribe=media_transcriber.cli.app:cli",
            "media-transcriber=media_transcriber.cli.app:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
