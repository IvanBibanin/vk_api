from setuptools import setup


setup(
    name="ivan-vk-api",
    version="0.1.1",
    description="Helpers for VK Ads API data loading and PostgreSQL export.",
    py_modules=[
        "vk_api",
        "to_postgresql",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.5",
        "requests>=2.28",
        "SQLAlchemy>=1.4",
        "psycopg2-binary>=2.9",
    ],
)
