from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='SQLPyHelper',
    version='0.1.3',
    description='A simple SQL database helper package for Python.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Adebayo Olaonipekun',
    author_email='pekunmi@live.com',
    packages=find_packages(),
    install_requires=[
        'psycopg2',
        'mysql-connector-python',
        'pyodbc',
        'cx_Oracle',
        'python-dotenv'
    ],
    extras_require={
        "mysql": ["mysql-connector-python"],
        "postgres": ["psycopg2"],
        "oracle": ["cx_Oracle"],
        "sqlserver": ["pyodbc"],
        "sqlite": []
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database :: Database Engines/Servers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
)
