from setuptools import setup, find_packages

setup(
    name='facets-module-mcp',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'mcp[cli]',
        'ftf-cli @ git+https://github.com/Facets-cloud/module-development-cli.git',
        'questionary',
        'checkov',
    ],
    entry_points={
        'console_scripts': [
            'facets-mcp=facets_server:main',  # assuming the main execution is in facets_server.py
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)