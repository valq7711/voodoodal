# voodoodal

```python
from voodoodal import DB, Table, Field, model
from pydal import DAL

_db = DAL()

class sign_created(Table):
    created = Field(...)
    created_by = Field(...)

class sign_updated(Table):
    updated = Field(...)
    updated_by = Field(...)

@model(_db)
class db(DB):

    @model.db_table
    class person(Table):
        name = Field('string', required = True)

    @model.db_table
    class thing(sign_created, sign_updated):
        owner = Field(_db.person, required = True)
        name = Field('string', required = True)

# db is _db == True
db.commit()

```









