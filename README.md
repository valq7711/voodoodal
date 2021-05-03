# voodoodal

## How It Works

At first glance it may seem that I have created derived classes from `dal` and `dal`-objects, but in fact this is a simple python metamagic!  
You define dummy classes and pass them to decorator that converts class definitions into arguments for `db.define_table()`.  
Thus, there are no side effects!  
You end up with pure `db` with pure `tables/fields` and ... IDE-autocomplete!  


```python
from voodoodal import DB, Table, Field, model
from pydal import DAL

# create dal-object
_db = DAL(...)

# setup magic decorator
model = model(_db)

# if you need signature table(s)
# instead of:
#   sign_created =  db.Table(db, 'sign_created', ...)
# you can just:
class sign_created(Table):
    created = Field('datetime')
    created_by = Field('reference auth_user')

class sign_updated(Table):
    updated = Field('datetime')
    updated_by = Field('reference auth_user')


# define `some` table at module scope if needed
@model.db_table
class some(Table):
    name = Field()

# already here you can:
#   _db.commit()
#   some.insert(name = 'foo')


# define all tables under dummy class `db`
@model
class db(DB):

    class person(Table):
        name = Field('string', required = True)

    # to inject signature(s) just specify them as base class(es)
    class thing(sign_created, sign_updated):
        owner = Field('reference person', required = True)
        name = Field('string', required = True)

    # if we want `db.some` to be autocomplete (this is optional and doesn't have any effect)
    some = some

# at this moment all above tables are defined
# and now  `db` is `_db`, so you can:
db.commit()

```









