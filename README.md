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

This package supports Python versions 3.7--3.10 and, currently, it's only 
tested on Windows (for Excel support). Installation instructions are provided 
for use with the [Anaconda Python] distribution. A similar process will 
probably work for pip, but it's currently not tested.

1. Create a conda environment with the base dependencies:
    
    ```
    > conda create -n _taxonopy -c conda-forge python=3.10 pip anytree blessed graphviz inquirer natsort openpyxl Pillow python-graphviz pyyaml tabulate tinydb
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
    folder: `/path/to/taxonopy`.
    
    ```
    > cd /path/to/taxonopy
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

## Tutorial

A typical user of taxonopy will create a schema (a subsumptive containment 
hierarchy) for structuring their data and then populate a database with 
records based upon the schema. This section provides a tutorial to illustrate 
all of the taxonopy operations used for completing these tasks.

Taxonopy is principally operated using a command line interface (CLI) so 
all the examples below are executed in a [Windows PowerShell]. The root CLI
command is called `taxonopy` and it provides help by typing:

```
> taxonopy -h
```

If this doesn't work, make sure that your conda environment is activated, i.e.

```
> conda activate _taxonopy
```

It is also recommend to run the tutorials below in a clean directory to prevent 
any accidents):

```
> mkdir temp
> cd temp
```

Table of contents:

* [Schemas](#Schemas)
    - [Creating the root field](#creating-the-root-field)
    - [Adding a field that takes an integer](#adding-a-field-that-takes-an-integer)
    - [Adding a field that takes a date](#adding-a-field-that-takes-a-date)
    - [Fields that take a single selection from a list of choices](#fields-that-take-a-single-selection-from-a-list-of-choices)
    - [Fields that take multiple selections from a list of choices](#fields-that-take-a-multiple-selections-from-a-list-of-choices)
    - [Adding more detail to a field](#adding-more-detail-to-a-field)
    - [Deleting a field](#deleting-a-field)
* [Database](#database)
    - [Add your first toaster](#add-your-first-toaster)
    - [Searching for and editing a record](#searching-for-and-editing-a-record)
    - [Inspecting records](#inspecting-records)
    - [Exporting and importing](#exporting-and-importing)

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

#### Fields that take multiple selections from a list of choices

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

#### Changing the order of fields

Presently it's not possible to change the order of fields in a schema using the 
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

### Database

Once a schema is defined, records can be created using the schema and stored 
in a text-based database (also a json file). The main `taxonopy` CLI 
subcommand used for working with databases and records is `db`. For help on 
the available options, type:

```
> taxonopy db -h
```

Lets add some records based on the schema created in the tutorial above. If 
you didn't create the schema, you can copy a version from the 
`examples/toasters` directory to an empty folder, like so:

```
> mkdir temp
> cp /path/to/taxonopy/examples/toasters/schema.json temp
> cd temp
```

If you've already got the schema, then just ensure that your shell's working 
directory is in the same folder. Also, if you have not yet done so, remember 
to activate the conda environment:

```
> conda activate _taxonopy
(_taxonopy) >
```

#### Add your first toaster

We create a new taxonopy database by adding our first record. For this task we 
use taxonopy's `db new` subcommand. An existing schema is expected; by default 
it's assumed to be called `schema.json` and reside in the current directory. 
This can be changed with the `--schema` argument if desired. A new database 
will be created, if it doesn't already exist, called, by default, `db.json`. 
To change this use the `--db` argument. Working in our temporary directory,
we simply type:

```
> taxonopy db new
[?] Name [str] (required):

```

At this point, we are presented with the fields in our schema to be completed 
for our new record. As the current field is marked as required, some text must 
be entered to move onto the next field. Let's add a name:

```
[?] Name [str] (required): BEKO Cosmopolis TAM8402B
[?] Capacity [int] (required):

```

It accepted the name, now we must add the toaster's capacity:

```
[?] Capacity [int] (required): 4
[?] Manufacturing Date [datetime.date.fromisoformat]:

```

The next field is for the manufacturing date. This field can only accept 
data that is valid input to the `datetime.date.fromisoformat` function. Let's
try adding an incorrect format:

```
[?] Manufacturing Date [datetime.date.fromisoformat]: 2nd June 2021
Given value is not compatible with type 'datetime.date.fromisoformat'
[?] Manufacturing Date [datetime.date.fromisoformat]:

```

OK, let's try the correct format:

```
[?] Manufacturing Date [datetime.date.fromisoformat]: 2021-06-02
[?] Colour: Black
 > Black
   Brown
   Blue

```

The next field is a list type, thus, we must select one option. To move 
between options use the arrow keys and to select an option press enter. Our 
toaster is blue:

```
[?] Colour: Blue
   Black
   Brown
 > Blue

[?] Features:
 > o Browning Control
   o Defrost
   o Reheat
   o Bluetooth

```

The Features field allows selection of multiple options. The arrow keys are
used to nagivate between the options and the **space bar** is used to select
or deselect them. When finished press the enter key. Let's add features to
our toaster:

```
[?] Features:
   X Browning Control
   X Defrost
 > X Reheat
   o Bluetooth

[?] Browning Control: Analog
 > Analog
   Digital

```

The Browning Control field requires extra data about the type of browning
control. Let's choose Digital:

```
[?] Browning Control: Digital
   Analog
 > Digital

Name value=BEKO Cosmopolis TAM8402B type=str required=True
├── Capacity value=4 type=int required=True
├── Manufacturing Date value=2021-06-02 import=datetime type=datetime.date.fromisoformat
├── Colour inquire=list required=True
│   └── Blue
└── Features inquire=checkbox
    ├── Browning Control inquire=list required=True
    │   └── Digital
    ├── Defrost
    └── Reheat

[?] Store record with Name 'BEKO Cosmopolis TAM8402B'?: yes
 > yes
   retry
   quit

```

Now we have completed all of the fields, taxonopy shows us the full record
and asks us if we want to store it. If we want to edit something we can
select `retry` and we can pass through the fields again (the original input
is remembered). If we don't want the record we can select `quit` to exit. Let's
choose `yes` to store our toaster. Now, we will see that a database file
has been created in the working directory and it contains some data.

```
> ls


    Directory: E:\Programming\Python\git\taxonopy\temp


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        02/06/2021     11:07           2005 db.json
-a----        01/06/2021     17:34           1737 schema.json

```

#### Searching for and editing a record

It might be that something is wrong with one of the records entered into your
database. For instance, the browning control on the BEKO Cosmopolis TAM8402B
is, in fact, analog not digital, so let's fix it. The CLI command for changing
existing records is `db update`. Similarly to before, the command has default
locations for the schema and database files, which can be changed if required.
For commands like `update`, where we want to select certain records, we
must enter some search parameters. These are provided by the positional `path`
argument and the optional `--value` and `--exact` arguments.

The `path` argument refers to the field that we would like to match against 
and the `--value` argument refers to the values that the field can take. 
`--value` is optional and if it's not given, the command will return any 
records containing that field - if we used the root path "Name", in our 
example, with no `--value` argument, the command would return all records in 
the database. The `--exact` argument is used to return only exact matches to 
the given value. If not given, any partial matches will also be returned.

Finally, the `--field` argument let's us edit just one field in the returned 
records. This can be useful for precise edits or if a new field is added and 
all records need to be updated, for instance. The `--field` argument takes the 
full path to the field, in the schema. Let's use all the options to fix our 
record:

```
> taxonopy db update Name --value "BEKO Cosmopolis TAM8402B" --exact --field "Name/Features/Browning Control"
[?] Update record with Name 'BEKO Cosmopolis TAM8402B'?: yes
 > yes
   no
   quit

```

Here, we search the "Name" field for the exact value "BEKO Cosmopolis TAM8402B".
We indicate that we just want to edit the "Name/Features/Browning Control"
field in the returned records. As the `update` command can return more than
one record for updating, taxonopy asks us if we want to edit this record,
or quit the update process at this point. We select `yes`, and then change
the browning control type:

```
[?] Update record with Name 'BEKO Cosmopolis TAM8402B'?: yes
 > yes
   no
   quit

[?] Browning Control: Analog
 > Analog
   Digital

Name required=True value=BEKO Cosmopolis TAM8402B type=str
├── Capacity required=True value=4 type=int
├── Manufacturing Date value=2021-06-02 type=datetime.date.fromisoformat import=datetime
├── Colour inquire=list required=True
│   └── Blue
└── Features inquire=checkbox
    ├── Defrost
    ├── Reheat
    └── Browning Control inquire=list required=True
        └── Analog

[?] Store updated record?: yes
 > yes
   no
   retry
   quit

```

As when we added a new record, taxonopy shows the updated record and asks
if we want to store it, retry or quit. After choosing `yes`, we can see that
the database file has been modified:

```
> ls


    Directory: E:\Programming\Python\git\taxonopy\temp


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        02/06/2021     11:34           2004 db.json
-a----        01/06/2021     17:34           1737 schema.json

```

#### Inspecting records

At this point in the tutorial, it's useful to have more records in our toaster 
database. Feel free to add more yourself, but if you want a shortcut then a
database file populated with 8 records is available in the 
`/path/to/taxonopy/examples/toasters` directory called `db.json`.  The 
taxonopy CLI current offers 3 commands for inspecting the records in the 
database: `count`, `show` and `list`.

The `count` subcommand allows users to count how many records contain a
particular field with, optionally, a particular value. For instance, let's
see how many records have "Name" fields containing "Toaster":

```
> taxonopy db count Name --value Toaster
Name: 2

```

By adding the `--exact` argument, we can see how many records are precisely
named "Toaster":

```
> taxonopy db count Name --value Toaster --exact
Name: 0

```

The `show` command works similarly to the `count` command, except that the
output contains the full records. For our toasters with names containing 
"Toaster" we get:

```
> taxonopy db show Name --value Toaster
Name type=str value=Dualit Bun Toaster required=True
├── Capacity type=int value=6 required=True
├── Colour inquire=list required=True
│   └── Black
└── Features inquire=checkbox
    └── Browning Control inquire=list required=True
        └── Analog

Name type=str value=Griffin Smart Connected Toaster required=True
├── Capacity type=int value=2 required=True
├── Manufacturing Date type=datetime.date.fromisoformat value=2017-01-04 import=datetime
├── Colour inquire=list required=True
│   └── Blue
└── Features inquire=checkbox
    ├── Browning Control inquire=list required=True
    │   └── Digital
    ├── Defrost
    └── Bluetooth

```

The `list` command filters the output of all records in the database. It's 
most basic usage will display the value of the root field for all the records:

```
> taxonopy db list
Name: BEKO Cosmopolis TAM8402B
Name: Bosch TAT4P429DE
Name: Dualit Bun Toaster
Name: Griffin Smart Connected Toaster
Name: Kenwood Elegancy
Name: MORPHY RICHARDS Evoke One
Name: Sunbeam Model T-20
Name: TEFAL Tefal Smartn Light TT640840

```

To display more fields at once, multiple `--path` arguments can be given to
the command. So, for instance, to see the Name, Capacity and Browning Control
fields of all the records, the follow command is given:

```
> taxonopy db list --path Name --path Name/Capacity --path "Name/Features/Browning Control"
Name: BEKO Cosmopolis TAM8402B          | Capacity: 4 | Browning Control: Analog
Name: Bosch TAT4P429DE                  | Capacity: 2 | Browning Control: Analog
Name: Dualit Bun Toaster                | Capacity: 6 | Browning Control: Analog
Name: Griffin Smart Connected Toaster   | Capacity: 2 | Browning Control: Digital
Name: Kenwood Elegancy                  | Capacity: 4 | Browning Control: Analog
Name: MORPHY RICHARDS Evoke One         | Capacity: 4 | Browning Control: Analog
Name: Sunbeam Model T-20                | Capacity: 2 | Browning Control: Analog
Name: TEFAL Tefal Smartn Light TT640840 | Capacity: 2 | Browning Control: Digital

```

When using `list` with optional fields, if one or two paths are given then
only records containing all the fields are returned:

```
> taxonopy db list --path Name --path "Name/Manufacturing Date"
Name: BEKO Cosmopolis TAM8402B        | Manufacturing Date: 2021-06-02
Name: Griffin Smart Connected Toaster | Manufacturing Date: 2017-01-04
Name: Sunbeam Model T-20              | Manufacturing Date: 1949-01-01

```

If an optional field is included where three or more paths are used, then at
least two of the fields must be contained by the record for it to be displayed:

```
> taxonopy db list --path Name --path "Name/Manufacturing Date" --path "Name/Features/Browning Control"
Name: BEKO Cosmopolis TAM8402B          | Manufacturing Date: 2021-06-02 | Browning Control: Analog
Name: Bosch TAT4P429DE                  |                                | Browning Control: Analog
Name: Dualit Bun Toaster                |                                | Browning Control: Analog
Name: Griffin Smart Connected Toaster   | Manufacturing Date: 2017-01-04 | Browning Control: Digital
Name: Kenwood Elegancy                  |                                | Browning Control: Analog
Name: MORPHY RICHARDS Evoke One         |                                | Browning Control: Analog
Name: Sunbeam Model T-20                | Manufacturing Date: 1949-01-01 | Browning Control: Analog
Name: TEFAL Tefal Smartn Light TT640840 |                                | Browning Control: Digital

```

#### Exporting and importing

It can be useful to view the entire database using a spreadsheet. For this
purpose, taxonopy can flatten the field hierarchy and export the resulting
table to an Excel file. For the database in the example above, the command
to export to Excel is:

```
> taxonopy db dump toasters
> ls


    Directory: E:\Programming\Python\git\taxonopy\temp


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        02/06/2021     11:56          13825 db.json
-a----        01/06/2021     17:34           1737 schema.json
-a----        02/06/2021     13:21          70448 toasters.xlsx

```

As can be seen, a new Excel file called "toasters.xlsx" has been created. 
Within the Excel file, the headers are separated with a colon to show 
relationships for fields below the second level, i.e. for the 
"Name/Features/Browning Control" field, the header shows "Features:Browning 
Control".

Correctly formatted Excel files can also be imported to create a new database
json file using the `db load` command. For the "toasters.xslx" file we just
created, let's make a new taxonpy database like so:

```
> taxonopy db load db_new.json .\toasters.xlsx
> ls


    Directory: E:\Programming\Python\git\taxonopy\temp


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        02/06/2021     11:56          13825 db.json
-a----        02/06/2021     13:30          13825 db_new.json
-a----        01/06/2021     17:34           1737 schema.json
-a----        02/06/2021     13:21          70448 toasters.xlsx


> taxonopy db list --path Name --path "Name/Manufacturing Date" --path "Name/Features/Browning Control" --db .\db_new.json
Name: BEKO Cosmopolis TAM8402B          | Manufacturing Date: 2021-06-02 | Browning Control: Analog
Name: Bosch TAT4P429DE                  |                                | Browning Control: Analog
Name: Dualit Bun Toaster                |                                | Browning Control: Analog
Name: Griffin Smart Connected Toaster   | Manufacturing Date: 2017-01-04 | Browning Control: Digital
Name: Kenwood Elegancy                  |                                | Browning Control: Analog
Name: MORPHY RICHARDS Evoke One         |                                | Browning Control: Analog
Name: Sunbeam Model T-20                | Manufacturing Date: 1949-01-01 | Browning Control: Analog
Name: TEFAL Tefal Smartn Light TT640840 |                                | Browning Control: Digital

```

As we can see, a new file has been created, named `db_new.json`, with the 
exact same size as the original `db.json` and precisely the same data 
contained within.

[1]: https://towardsdatascience.com/represent-hierarchical-data-in-python-cd36ada5c71a
[taxonomy-parser]: https://github.com/madagra/taxonomy-parser
[anytree]: https://github.com/c0fec0de/anytree
[tinydb]: https://github.com/msiemens/tinydb/
[python-inquirer]: https://github.com/magmax/python-inquirer
[openpyxl]: https://foss.heptapod.net/openpyxl/openpyxl
[Anaconda Python]: https://www.anaconda.com/products/individual
[Windows PowerShell]: https://docs.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.1
