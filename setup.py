from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='SQLPyHelper',
    version='0.1.7',
    description='A simple SQL database helper package for Python.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Adebayo Olaonipekun',
    author_email='pekunmi@live.com',
    url='https://github.com/adebayopeter/sqlpyhelper',
    packages=find_packages(),
    package_data={
        "sqlpyhelper": ["py.typed"],
    },
    python_requires=">=3.8",
    install_requires=[
        'python-dotenv',
        'click'
    ],
    extras_require={
        "postgres": ["psycopg2"],
        "mysql": ["mysql-connector-python"],
        "sqlserver": ["pyodbc"],
        "oracle": ["oracledb"],
        "all": [
            "psycopg2",
            "mysql-connector-python",
            "pyodbc",
            "oracledb",
        ],
    },
    keywords=[
        "database", "sql", "sqlite", "postgresql", "mysql",
        "sqlserver", "oracle", "db", "query", "helper",
    ],
    project_urls={
        "Documentation": "https://sqlpyhelper.readthedocs.io/en/latest/",
        "Source": "https://github.com/adebayopeter/sqlpyhelper",
        "Bug Tracker": "https://github.com/adebayopeter/sqlpyhelper/issues",
        "Changelog": "https://github.com/adebayopeter/sqlpyhelper/blob/main/CHANGELOG.md",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database :: Database Engines/Servers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'sqlpyhelper=sqlpyhelper.cli:cli',
        ],
    },
)
