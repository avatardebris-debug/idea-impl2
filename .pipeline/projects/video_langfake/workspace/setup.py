from setuptools import setup, find_packages

setup(
    name="video_langfake",
    version="0.1.0",
    description="Deepfake subtle changes to translate video to any language",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "moviepy>=1.0.3",
        "numpy>=1.24.0",
        "openai-whisper>=20231117",
    ],
    entry_points={
        "console_scripts": [
            "video_langfake=video_langfake.cli:main",
        ],
    },
)
