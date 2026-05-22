from setuptools import setup


setup(
    name="ivan-vk-api",
    version="0.1.2",
    description="Helpers for VK Ads API data loading.",
    py_modules=[
        "vk_api",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.5",
        "requests>=2.28",
    ],
)
