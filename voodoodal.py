from pydal import DAL, Field as DalField
from pydal.objects import Table as DalTable

class DALClasses:
    Field = DalField

def patch(Field):
    DALClasses.Field = Field

def table(db, cls = None):
    if not cls:
        return lambda cls: table(db, cls)
    return cls(db, 'Table')

def def_table(db, cls = None):
    if not cls:
        return lambda cls: def_table(db, cls)
    return cls(db, 'define_table')

def make(db, cls):
    if not cls:
        return lambda cls: make(db, cls)
    return cls(db)

class model:
    __current__ = None
    def __new__(cls, db):
        cls.__current__ = db

        def new(cls):
            return super().__new__(cls)

        cls = type(
            f'model_{id(db)}',
            (cls,),
            dict(
                _db = db,
                __new__ = new,
            )
        )
        return cls()

    def __call__(self, cls):
        model.__current__ = None
        return cls(self._db)

    @classmethod
    def db_table(mcls, cls):
        db = getattr(mcls, '_db', mcls.__current__)
        return cls(db, 'define_table')

    @classmethod
    def table(mcls, cls):
        db = getattr(mcls, '_db', mcls.__current__)
        return cls(db, 'Table')


__signatures__ = dict()

def get_signature(db, cls):
    db_signs = __signatures__.setdefault(id(db), dict())
    tbl = db_signs.get(id(cls))
    if not tbl:
        tbl = cls(db, 'Table')
        db_signs[id(cls)] = tbl
    return tbl


class Field(DalField):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Table(DalTable):
    def __new__(cls, db, action):
        tname = cls.__name__
        fields = []
        kwargs = dict()
        for name, attr in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if isinstance(attr, Field):
                fields.append(DALClasses.Field(name, *attr.args, **attr.kwargs))
            else:
                kwargs[name] = attr
        for sign in cls.__bases__:
            if sign is not Table:
                fields.append(get_signature(db, sign))
        args = [tname] + fields
        if action == 'Table':
            args.insert(0, db)
        action = getattr(db, action)
        tbl = action(*args, **kwargs) or db[tname]
        return tbl


class DB(DAL):
    def __new__(cls, db):
        return db
