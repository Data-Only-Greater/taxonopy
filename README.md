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

[1]: https://towardsdatascience.com/represent-hierarchical-data-in-python-cd36ada5c71a
[taxonomy-parser]: https://github.com/madagra/taxonomy-parser
[anytree]: https://github.com/c0fec0de/anytree
[tinydb]: https://github.com/msiemens/tinydb/
[python-inquirer]: https://github.com/magmax/python-inquirer
[openpyxl]: https://foss.heptapod.net/openpyxl/openpyxl
