from pydal import DAL, Field as DalField
from pydal.objects import Table as DalTable

__author__ = "Valery Kucherov <valq7711@gmail.com>"
__copyright__ = "Copyright (C) 2021 Valery Kucherov"
__license__ = "MIT"
__version__ = "0.0.1"

class DALClasses:
    Field = DalField

def patch(Field):
    DALClasses.Field = Field

class model:
    __current__ = None
    def __new__(cls, db):
        cls.__current__ = dict(db = db)

        def new(cls):
            self = super().__new__(cls)
            return self

        cls = type(
            f'model_{id(db)}',
            (cls,),
            dict(
                _db = db,
                __new__ = new,
                __current__ = dict()
            )
        )
        return cls()

    def __call__(self, cls):
        current = self.__current__
        model.__current__ = None
        config = getattr(cls, '__config__', {})
        prefix = config.get('prefix')
        auto_pk = config.get('auto_pk')
        tables_extra = dict()
        for name, attr in cls.__dict__.items():
            if not isinstance(attr, type):
                continue
            new = getattr(attr, '__new__', None)
            if new and hasattr(new, '__voodoodal__'):
                attr(self._db, 'define_table', prefix = prefix, name = name, auto_pk = auto_pk)
                extra = getattr(attr, '__extra__', None)
                if extra:
                    tables_extra[name] = extra
        if (postproc := current.get('postproc')):
            if isinstance(postproc, classmethod):
                postproc = postproc.__get__(cls, cls)
            postproc(self._db, tables_extra)
        return cls(self._db)

    @classmethod
    def postproc(mcls, fun):
        mcls.__current__['postproc'] = fun

    @classmethod
    def db_table(mcls, cls):
        db = getattr(mcls, '_db', mcls.__current__.get('db'))
        return cls(db, 'define_table')

    @classmethod
    def table(mcls, cls):
        db = getattr(mcls, '_db', mcls.__current__.get('db'))
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
    def __new__(cls, db, action, prefix = None, name = None, auto_pk = None):
        tname = name or cls.__name__
        fields = []
        kwargs = dict()
        need_pk = False
        for name, attr in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if isinstance(attr, Field):
                attr.name = name
                if not need_pk and auto_pk and name == 'id' and attr.args and attr.args[0] != 'id':
                    need_pk = True
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

        if need_pk and kwargs.get('primarykey') is None:
            kwargs['primarykey'] = ['id']
        if prefix:
            kwargs['rname'] = f"{prefix}{tname}"
        tbl = action(*args, **kwargs) or db[tname]
        return tbl

Table.__new__.__voodoodal__ = True

class DB(DAL):
    def __new__(cls, db):
        return db
