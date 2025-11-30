from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return "A comprehensive AI toolbox for Django"

setup(
    name="django-forge-ai",
    version="0.1.0",
    author="DjangoForgeAI Contributors",
    author_email="your-email@example.com",
    description="A comprehensive AI toolbox for Django - seamless integration of LLM functionalities, RAG systems, and AI agents",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-forge-ai",
    project_urls={
        "Homepage": "https://github.com/yourusername/django-forge-ai",
        "Documentation": "https://github.com/yourusername/django-forge-ai#readme",
        "Repository": "https://github.com/yourusername/django-forge-ai",
        "Issues": "https://github.com/yourusername/django-forge-ai/issues",
    },
    packages=find_packages(include=["django_forge_ai", "django_forge_ai.*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "django>=3.2",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "chromadb>=0.4.0",
        "qdrant-client>=1.6.0",
        "psycopg2-binary>=2.9.0",
        "celery>=5.3.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "tiktoken>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-django>=4.5.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "coverage>=7.0.0",
        ],
    },
    keywords="django ai llm rag vector-database openai anthropic machine-learning",
    zip_safe=False,
)
# Refactor
# Fix
# Fix
# Update
# Improve
# Refactor
# Fix
# Update
# Refactor
# Refactor
# Refactor
# Improve
# Refactor
# Refactor
# Fix
# Update
# Improve
# Improve
# Fix
# Refactor
# Refactor
# Improve
