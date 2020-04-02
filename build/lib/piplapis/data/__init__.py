"""Python implementation of Pipl's data model.

The data model is basically Source/Person objects (avaialable in 
piplapis.data.containers) with their fields (available in piplapis.data.fields).

Importing can be done either with:

from piplapis.data.containers import Source, Person
from piplapis.data.fields import Name, Address

or simply with:

from piplapis.data import Record, Person, Name, Address, Source

"""
from piplapis.data.containers import Source, Person
from piplapis.data.fields import *
