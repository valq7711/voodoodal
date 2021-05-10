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

    ## some useful options are supported:
    '''
     __config__ = dict(
         prefix = 'foo_',  
         auto_pk = True    
     )
    `prefix` - common rname prefix: db.define_table(tname, ..., rname = f'{prefix}{tname}')  
    `auto_pk` - add `primarykey = ['id']` if there is `id = Field('string')`, 
                 i.e. Field with name 'id', but with type != 'id'
    '''             
    
    class person(Table):
        name = Field(required = True)
        secret_name = Field()
        
        # place any options into __extra__ for postprocessing - see below
        __extra__ = dict(
            not_readable = [secret_name]
        )


    # to inject signature(s) just specify them as base class(es)
    class thing(sign_created, sign_updated):
        owner = Field('reference person', required = True)
        name = Field('string', required = True)
        
        # this will turn into `Field.Virtual`
        @property
        def owner_thing_ids(row):
            return (row.thing.owner, row.thing.id)
            
        # this will turn into `Field.Method`
        def thing_match(row, pattern):
            import re
            return re.match(pattern, row.thing.name)

        # this will turn into `db.thing.get_like`-method
        # usage example: db.thing.get_like('b%') - select all things whose names start with 'b'
        @classmethod
        def get_like(self, pattern):
            # self is db.thing
            db = self._db
            return db(self.name.like(pattern)).select()

        

    # if we want `db.some` to be autocomplete (this is optional and doesn't have any effect)
    some = some


    # postprocessing
    @model.postproc
    @classmethod
    def my_postproc(cls, db, tables_extra):
        '''
        `tables_extra` - dict in format {tname: __extra__, ...} i.e.:
            {
                'person': {
                    'not_readable': [secret_name] 
                }
            }
        '''
        for tname, extra in tables_extra.items():
            for attr, fld_list in extra.items():
                for f in fld_list:
                    _attr = attr.lstrip('not_')
                    setattr(db[tname][f.name], _attr, attr == _attr)
   

# at this moment all above tables are defined
# and now  `db` is `_db`, so you can:
db.commit()

```

## Installation using pip (optional)
```pip install https://github.com/valq7711/voodoodal/archive/main.zip```







