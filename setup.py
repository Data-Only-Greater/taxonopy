import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="taxonopy",
    version="0.0.1",
    author="Mathew Topper",
    author_email="mathew.topper@dataonlygreater.com",
    description="Taxonomic hierarchies with text-based records",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Data-Only-Greater/taxonopy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6, <3.9.0",
    install_requires=[
        'anytree',
        'blessed',
        'graphviz',
        'inquirer',
        'importlib_metadata; python_version < "3.8.0"',
        'natsort',
        'openpyxl',
        'Pillow',
        'tabulate',
        'tinydb'
    ],
    extras_require={
        'test': ['pytest', 'pytest-console-scripts']},
    entry_points = {
        'console_scripts': ['taxonopy=taxonopy._cli:main'],
    }
)
