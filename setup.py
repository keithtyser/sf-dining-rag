from setuptools import setup, find_packages

setup(
    name="restaurant-assistant",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "openai",
        "pinecone-client",
        "python-dotenv",
        "numpy",
    ],
    python_requires=">=3.9",
) 