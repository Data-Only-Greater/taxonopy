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

## Uninstallation

Using conda:
    
    ```
    > conda remove -n _taxonopy --all
    ```

## Usage

Taxonopy requires two parts. Firstly, a schema is defined which provides a
hierarchical structure. Secondly, records are created based upon the schema.

Taxonopy is mainly used through a command line interface (CLI), as present, so 
all the commands below are executed in a [Windows PowerShell]. The root CLI
command is called `taxonopy` and it provides help by typing:

```
> taxonopy -h
```

If this doesn't work, make sure that your conda environment is activated, i.e.

```
> conda activate _taxonopy
```

It is recommend to run the tutorials below in a clean directory to prevent any
accidents)

```
> mkdir temp
> cd temp
```

### Schemas

To demonstrate schemas and their features, let's create an example for a 
toaster. When working with schemas, the `schema` subcommand of the `taxonopy` 
CLI is used. For help on the options, type:

```
> taxonopy schema -h
```

The final version of the schema created in the tutorial below can be found
in the `examples/toasters` directory.

#### Creating the root field

Every schema needs a root field, from which all other fields can be found. 
Let's use the `schema new` subcommand to create a new schema:

```
> taxonopy schema new Name
Name type=str required=True

```

Here we see that our schema has been created with the root field named "Name", 
and the attributes `type` and `required`. Every field has an implicit `name` 
attribute (given the name "Name" for our root field). Every other field 
attribute is optional, except for the root field. The `type` attribute tells 
the field to except a value and the `schema new` subcommand sets the default 
type to `str` (this can be modified using the `--attributes` argument). 
Additionally, the `required` attribute is set to `True` to ensure that a value 
is set on this field for all records. 

Setting these attributes ensures that every record will have a value associate 
to the "Name" field, which can then be used for identifying the records. 
Taxonopy checks for uniqueness of the root field value, so if a second record 
is added with the same "Name", taxonopy will ask if the original record is to 
be replaced.

Looking at the directory structure, we note that a new file named `schema.json`
has been created:

```
> ls


    Directory: E:\Programming\Python\git\taxonopy\temp


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        01/06/2021     14:51            135 schema.json

```

By default the `taxonopy` command will assume that the schema is defined in a 
file named `schema.json` in the directory in which it is called. If so 
desired, this can be changed by passing arguments to the various subcommands 
(normally `--out` or `--schema`) to change the path to the schema file.

#### Adding a field that takes an integer

When adding new fields to the schema, all attributes (other than the name) are 
optional. Let's now add a child field that takes an integer which must be set 
for all records. For this purpose we use the `schema add` subcommand. When 
adding child fields we also need to include the "path" to the parent field. In 
this case it's simply the root field name "Name".

```
> taxonopy schema add Capacity Name --attributes type=int required=True
Name required=True type=str
└── Capacity required=True type=int

```

Here, we had to explicitly set the `type` and `required` attributes, using the 
`--attributes` argument followed by `key=value` pairs. If an unknown attribute 
is given, it will simply be ignored.

Now we know how many toasts our toasters can toast.

#### Adding a field that takes a date

The `type` attribute of a field is not limited to inbuilt Python types. By 
supplying an `import` attribute, external modules can be used to validate 
input. Let's add a new field to store the manufacturing date:

```
> taxonopy schema add "Manufacturing Date" Name --attributes import=datetime type=datetime.date.fromisoformat
Name type=str required=True
├── Capacity type=int required=True
└── Manufacturing Date type=datetime.date.fromisoformat import=datetime

```

Now when this field is added to a record (if desired, as it's not required),
the `datetime` module will be imported and the given value will be passed to
the `datetime.date.fromisoformat` to test its validity.

#### Fields that take a single selection from a list of choices

The fields we've added so far hold arbitrary (typed) values, but what if we 
wanted to restrict the values that a field in a record could take? For this 
purpose, we use the `inquire` attribute, which gives the children of the field 
special meaning. Below, we'll add a field and some children to describe the 
options that the colour of the toaster can take:

```
> taxonopy schema add Colour Name --attributes inquire=list required=True
> taxonopy schema add Black Name/Colour
> taxonopy schema add Brown Name/Colour
> taxonopy schema add Blue Name/Colour
Name type=str required=True
├── Capacity type=int required=True
├── Manufacturing Date type=datetime.date.fromisoformat import=datetime
└── Colour required=True inquire=list
    ├── Black
    ├── Brown
    └── Blue

```

For the `Colour` field we have set the attribute `inquire=list`, which means 
that only one of the field's children can be selected. We then added the 
potential values by adding children to the `Colour` field (note that the parent 
path of the latter is `Name/Colour`, as forward slashes are used to separate 
levels). Now, when a record is added, the `Colour` field must have one child 
chosen from the available options in the schema.

#### Fields that take a multiple selections from a list of choices

In some cases it can be desirable to allow multiple selection from a list of
choices. For fields of this type, we set the `inquire` attribute to the value
`checkbox`. Below, we'll add some features that the toasters  could include:

```
> taxonopy schema add Features Name --attributes inquire=checkbox
> taxonopy schema add "Browning Control" Name/Features
> taxonopy schema add Defrost Name/Features
> taxonopy schema add Reheat Name/Features
> taxonopy schema add Bluetooth Name/Features
Name required=True type=str
├── Capacity required=True type=int
├── Manufacturing Date import=datetime type=datetime.date.fromisoformat
├── Colour inquire=list required=True
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Browning Control
    ├── Defrost
    ├── Reheat
    └── Bluetooth

```

When a new record is added, any number of the children of the Features field
can be chosen (including none at all, as it's not a required field).

#### Adding more detail to a field

Multiple levels can be included in a taxonopy schema, which gives us the 
opportunity to add additional detail to fields. Let's say, for instance, we 
wanted to differentiate between different types of browning control. The field 
could be modified as follows:

```
> taxonopy schema add "Browning Control" Name/Features --attributes inquire=list required=True
> taxonopy schema add Analog "Name/Features/Browning Control"
> taxonopy schema add Digital "Name/Features/Browning Control"
Name type=str required=True
├── Capacity type=int required=True
├── Manufacturing Date import=datetime type=datetime.date.fromisoformat
├── Colour required=True inquire=list
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Defrost
    ├── Reheat
    ├── Bluetooth
    └── Browning Control required=True inquire=list
        ├── Analog
        └── Digital

```

Firstly, note here that the "Browning Control" field was rewritten in the 
schema to add the `inquire` and `required` attributes.  The effect of these 
changes is that if the Browning Control feature is added to a record then a 
selection must be also be added from the children of the field (i.e. Analog or 
Digital).

#### Deleting a field

As seen in the last example, a field can be updated if required, but it's also
possible to delete a field. In the example below we'll add an unwanted field
and then delete it:

```
> taxonopy schema add "HAL9000" Name/Features
Name type=str required=True
├── Capacity type=int required=True
├── Manufacturing Date type=datetime.date.fromisoformat import=datetime
├── Colour inquire=list required=True
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Defrost
    ├── Reheat
    ├── Bluetooth
    ├── Browning Control inquire=list required=True
    │   ├── Analog
    │   └── Digital
    └── HAL9000

> taxonopy schema delete Name/Features/HAL9000
Name type=str required=True
├── Capacity type=int required=True
├── Manufacturing Date import=datetime type=datetime.date.fromisoformat
├── Colour inquire=list required=True
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Defrost
    ├── Reheat
    ├── Bluetooth
    └── Browning Control inquire=list required=True
        ├── Analog
        └── Digital

```

In this case, we must provide the full path of the field to the `schema delete`
subcommand.

#### Viewing a schema

To view an existing schema without making any changes, the `schema show`
subcommand is used. For the toaster example this gives:

```
> taxonopy schema show
Name type=str required=True
├── Capacity type=int required=True
├── Manufacturing Date import=datetime type=datetime.date.fromisoformat
├── Colour inquire=list required=True
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Defrost
    ├── Reheat
    ├── Bluetooth
    └── Browning Control inquire=list required=True
        ├── Analog
        └── Digital

```

#### Chaning the order of fields

Presently it's not possible to change the order of in a schema using the 
taxonopy package. For simple reordering, direct manipulation of the json file 
is possible. Say, for instance, we want to move the "Browning Control" field 
back to its original position. In the json file, the field is seen at the 
bottom of the "L2" group:

```json
    "L2": [
        {
            "name": "Black",
            "parent": "Name/Colour"
        },
        {
            "name": "Brown",
            "parent": "Name/Colour"
        },
        {
            "name": "Blue",
            "parent": "Name/Colour"
        },
        {
            "name": "Defrost",
            "parent": "Name/Features"
        },
        {
            "name": "Reheat",
            "parent": "Name/Features"
        },
        {
            "name": "Bluetooth",
            "parent": "Name/Features"
        },
        {
            "name": "Browning Control",
            "parent": "Name/Features",
            "inquire": "list",
            "required": "True"
        }
```

To promote the field, we can simply move the dictionary containing it above 
the other fields with parent "Name/Features", like so:

```json
    "L2": [
        {
            "name": "Black",
            "parent": "Name/Colour"
        },
        {
            "name": "Brown",
            "parent": "Name/Colour"
        },
        {
            "name": "Blue",
            "parent": "Name/Colour"
        },
        {
            "name": "Browning Control",
            "parent": "Name/Features",
            "inquire": "list",
            "required": "True"
        },
        {
            "name": "Defrost",
            "parent": "Name/Features"
        },
        {
            "name": "Reheat",
            "parent": "Name/Features"
        },
        {
            "name": "Bluetooth",
            "parent": "Name/Features"
        }
```

Saving the modified json file and viewing the schema again, we can see that 
the order of the fields has been modified:

```
> taxonopy schema show
Name required=True type=str
├── Capacity required=True type=int
├── Manufacturing Date type=datetime.date.fromisoformat import=datetime
├── Colour inquire=list required=True
│   ├── Black
│   ├── Brown
│   └── Blue
└── Features inquire=checkbox
    ├── Browning Control inquire=list required=True
    │   ├── Analog
    │   └── Digital
    ├── Defrost
    ├── Reheat
    └── Bluetooth

```

### Database and Records

Once a schema is defined, records and be created using the schema and stored 
in a text-based database (also a json file). The main `taxonopy` CLI 
subcommand used for working with databases and records is `db`. For help on 
the available options, type:

```
> taxonopy db -h
```


[1]: https://towardsdatascience.com/represent-hierarchical-data-in-python-cd36ada5c71a
[taxonomy-parser]: https://github.com/madagra/taxonomy-parser
[anytree]: https://github.com/c0fec0de/anytree
[tinydb]: https://github.com/msiemens/tinydb/
[python-inquirer]: https://github.com/magmax/python-inquirer
[openpyxl]: https://foss.heptapod.net/openpyxl/openpyxl
[Anaconda Python]: https://www.anaconda.com/products/individual
[Windows PowerShell]: https://docs.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.1
