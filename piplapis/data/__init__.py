"""Python implementation of Pipl's data model.

The data model is basically Record/Person objects (avaialable in 
piplapis.data.containers) with their source (available in piplapis.data.source)
and their fields (available in piplapis.data.fields).

Importing can be done either with:

from piplapis.data.containers import Record, Person
from piplapis.data.fields import Name, Address
from piplapis.data.source import Source

or simply with:

from piplapis.data import Record, Person, Name, Address, Source

"""
from piplapis.data.containers import Record, Person
from piplapis.data.source import Source
from piplapis.data.fields import *
