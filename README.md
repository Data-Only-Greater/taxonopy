# Taxonopy

## Introduction

Taxonopy is a Python package for creating subsumptive containment hierarchies
(otherwise known as taxonomic hierarchies) called schemas, and storing records
matched against a given schema in a text-based (json) database.

The schema structure is based on the design proposed by Mario Dagrada in [this 
blog post][1]. The code which works with the schemas is based on the code 
created by Mario, found in the [taxonomy-parser] repository, leveraging the 
[anytree] package.

To provide the database element of this package [tinydb] is used and a 
command line interface for working with schemas and records is included, 
utilising the fantastic [python-inquirer] package. For convenience the 
database can be round-trip dumped-to and loaded-from Excel format files, 
with the help of the [openpyxl] library.

## Installation

**Note, this package is in early-development. Use at your own risk.**

This package supports Python versions 3.6--3.8. Version 3.9 support will be
added when the upstream packages support it. Currently, it's only tested on
Windows (for Excel support).

Installation instructions are provided for use with the [Anaconda Python]
distribution. A similar process will probably work for pip, but it's currently
not tested.

1. Create a conda environment with the base dependencies:

```
> conda create -n _taxonopy -c conda-forge python=3.8 pip anytree blessed=1.17.6 graphviz inquirer openpyxl Pillow python-graphviz tinydb
```

Note that for Python<3.8 the `importlib_metadata` package should be added to
the command above.


2. Permently add conda-forge channel to the environment:

```
> conda activate _taxonopy
> conda config --env --add channels conda-forge
```

3. Install taxonopy (in development mode):

This step assumes that the source code has been downloaded to some local
folder: `/path/to/taxonopy/folder`.

```
> cd /path/to/taxonopy/folder
> pip install -e .
```

4. (Optional) Test the package

```
> conda install pytest pytest-console-scripts
> pytest
```

## Uninstall

Using conda:

```
> conda remove -n _taxonopy --all
```


[1]: https://towardsdatascience.com/represent-hierarchical-data-in-python-cd36ada5c71a
[taxonomy-parser]: https://github.com/madagra/taxonomy-parser
[anytree]: https://github.com/c0fec0de/anytree
[tinydb]: https://github.com/msiemens/tinydb/
[python-inquirer]: https://github.com/magmax/python-inquirer
[openpyxl]: https://foss.heptapod.net/openpyxl/openpyxl
[Anaconda Python]: https://www.anaconda.com/products/individual
