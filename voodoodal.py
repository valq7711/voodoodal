from pydal import DAL, Field as DalField
from pydal.objects import Table as DalTable

__author__ = "Valery Kucherov <valq7711@gmail.com>"
__copyright__ = "Copyright (C) 2021 Valery Kucherov"
__license__ = "MIT"
__version__ = "0.0.3"


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
        common_hook = getattr(cls, 'on_action', None)
        tables_extra = dict()
        for name, attr in cls.__dict__.items():
            if not isinstance(attr, type):
                continue
            new = getattr(attr, '__new__', None)
            if new and hasattr(new, '__voodoodal__'):
                # attr is voodoodal.Table class
                attr(
                    self._db,
                    'define_table',
                    prefix = prefix,
                    name = name,
                    auto_pk = auto_pk,
                    common_hook = common_hook
                )
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


HOOKS = {f"{phase}_{action}" for phase in ('before', 'after') for action in ('insert', 'update', 'delete')}


class Table(DalTable):
    def __new__(
        cls,
        db,
        action,  # 'define_table' or 'Table'
        prefix = None,
        name = None,
        auto_pk = None,
        common_hook = None,
    ):
        tname = name or cls.__name__
        fields = list()
        hooks = dict()
        table_methods = dict()  # https://github.com/web2py/pydal/blob/232e841765ee97ac6f7af45be794d46432085c4d/pydal/objects.py#L340
        kwargs = dict()
        need_pk = False
        for name, attr in cls.__dict__.items():
            if name.startswith('__'):
                continue

            # hooks
            if name in HOOKS:
                hooks[name] = attr
            # Field.Virtual
            elif isinstance(attr, property):
                fields.append(DalField.Virtual(name, attr.fget))
            # table method
            elif isinstance(attr, classmethod):
                table_methods[name] = attr.__func__
            # just Field
            elif isinstance(attr, Field):
                attr.name = name
                if not need_pk and auto_pk and name == 'id' and attr.args and attr.args[0] != 'id':
                    need_pk = True
                fields.append(DalField(name, *attr.args, **attr.kwargs))
            # Field.Method
            elif callable(attr):
                fields.append(DalField.Method(name, attr))
            else:
                kwargs[name] = attr
        for sign in cls.__bases__:
            if sign is not Table:
                fields.append(get_signature(db, sign))
        args = [tname] + fields
        if action == 'Table':
            args.insert(0, db)
        action = getattr(db, action)

        # auto_pk
        if need_pk and kwargs.get('primarykey') is None:
            kwargs['primarykey'] = ['id']
        # rname prefix
        if prefix:
            kwargs['rname'] = f"{prefix}{tname}"

        # define table
        tbl = action(*args, **kwargs) or db[tname]

        # set hooks
        for hook_name, hook in hooks.items():
            tbl[f"_{hook_name}"].append(hook)
        if common_hook:
            for hook_name in HOOKS:
                tbl[f"_{hook_name}"].append(
                    lambda *args, hook_name = hook_name, **kw: common_hook(tbl, hook_name, *args, **kw)
                )
        # set table methods
        for meth_name, meth in table_methods.items():
            tbl.add_method.register(meth_name)(meth)
        return tbl

Table.__new__.__voodoodal__ = True

class DB(DAL):
    def __new__(cls, db):
        return db
