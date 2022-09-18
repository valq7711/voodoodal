from typing import Callable, Union, Type, TypeVar
from pydal import DAL, Field as DalField
from pydal.objects import Table as DalTable, Row


DB = DAL

T = TypeVar('T')


class ModelBuilder:
    # special methods
    ON_ACTION = 'on_action'
    ON_DEFINE_TABLE = 'on_define_table'
    ON_DEFINE_MODEL = 'on_define_model'

    def __init__(self, db: DAL, migrate_indexes: Union[Callable, bool] = False, index_migrator: Callable = None):
        self._db = db
        self.migrate_indexes = migrate_indexes
        self.index_migrator = index_migrator

    def _migrate_indexes(self, tname: str):
        return (
            self.migrate_indexes
            if isinstance(self.migrate_indexes, bool)
            else self.migrate_indexes(tname)
        )

    def __call__(self, group_cls: Type[T]) -> T:
        for cls in group_cls.__bases__:
            assert issubclass(cls, DB)
            self.build_tables(cls)
        return self._db

    def build_tables(self, cls: Type[DB]):
        config = getattr(cls, '__config__', {})
        prefix = config.get('prefix')
        auto_pk = config.get('auto_pk')
        common_hook = getattr(cls, self.ON_ACTION, None)
        on_define_table = getattr(cls, self.ON_DEFINE_TABLE, None)
        if isinstance(on_define_table, classmethod):
            on_define_table = on_define_table.__get__(cls, cls)
        tables_extra = {}
        for name, attr in cls.__dict__.items():
            if not (isinstance(attr, type) and issubclass(attr, Table)):
                continue
            attr(
                self._db,
                'define_table',
                prefix=prefix,
                name=name,
                auto_pk=auto_pk,
                common_hook=common_hook,
                migrate_indexes=self._migrate_indexes(name),
                index_migrator=self.index_migrator,
                on_define=on_define_table,
            )
            extra = getattr(attr, '__extra__', None)
            if extra:
                tables_extra[name] = extra
        on_define_model = getattr(cls, self.ON_DEFINE_MODEL, None)
        if on_define_model:
            if isinstance(on_define_model, classmethod):
                on_define_model = on_define_model.__get__(cls, cls)
            on_define_model(self._db, tables_extra)


__signatures__ = {}


def get_signature(db, cls):
    db_signs: dict = __signatures__.setdefault(id(db), {})
    tbl = db_signs.get(id(cls))
    if not tbl:
        tbl = cls(db, 'Table')
        db_signs[id(cls)] = tbl
    return tbl


class DBValidatorWrapper:
    def __init__(self, fun):
        self.fun = fun

    def resolve(self, db):
        return self.fun(db)


class Field(DalField):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def resolve_validators(self, db):
        requires = self.kwargs.pop('requires', None)
        if requires is None:
            return
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        else:
            requires = [*requires]
        for i, r in enumerate(requires):
            if isinstance(r, DBValidatorWrapper):
                requires[i] = r.resolve(db)
        self.kwargs['requires'] = requires


class Index:
    '''
    class my_table(Table):
        ...
        foo_idx = Index('col_1', 'col_2', unique=True),
    '''

    def __init__(self, *fields, unique=True, **kwargs):
        kwargs['unique'] = unique
        self._fields = fields
        self.kwargs = kwargs

    @property
    def fields(self):
        return [
            f.name if isinstance(f, Field) else f
            for f in self._fields
        ]


HOOKS = {
    f"{phase}_{action}"
    for phase in ('before', 'after')
    for action in ('insert', 'update', 'delete')
}


class Table(DalTable, Row):
    def __new__(
            cls,
            db,
            action,  # 'define_table' or 'Table'
            prefix=None,
            name=None,
            auto_pk=None,
            common_hook=None,
            migrate_indexes=False,
            index_migrator=None,
            on_define=None,
    ):
        tname = name or cls.__name__
        fields = []
        hooks = {}
        table_methods = {}  # NOQA https://github.com/web2py/pydal/blob/232e841765ee97ac6f7af45be794d46432085c4d/pydal/objects.py#L340
        kwargs = {}
        indexes = {}
        has_field_id_name = False
        has_field_id_type = False
        _on_define = None
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
                if name == '_on_define':
                    _on_define = attr.__get__(cls, cls)
                else:
                    table_methods[name] = attr.__func__
            # just Field
            elif isinstance(attr, Field):
                attr.resolve_validators(db)
                attr.name = name
                has_field_id_name = has_field_id_name or name == 'id'
                has_field_id_type = (
                    has_field_id_type
                    or attr.args and attr.args[0] == 'id'
                )
                fields.append(DalField(name, *attr.args, **attr.kwargs))
            # Field.Method
            elif isinstance(attr, Index):
                indexes[name] = attr
            elif callable(attr):
                fields.append(DalField.Method(name, attr))
            else:
                kwargs[name] = attr
        for sign in cls.__bases__:
            if sign is not Table:
                fields.append(get_signature(db, sign))
        args = [tname, *fields]
        if action == 'Table':
            args.insert(0, db)
        action = getattr(db, action)

        # auto_pk
        if (
            auto_pk and not has_field_id_type and has_field_id_name
            and kwargs.get('primarykey') is None
        ):
            kwargs['primarykey'] = ['id']
        # rname prefix
        if prefix:
            kwargs['rname'] = f"{prefix}{tname}"

        # define table
        tbl: Table = action(*args, **kwargs) or db[tname]

        # set hooks
        for hook_name, hook in hooks.items():
            tbl[f"_{hook_name}"].append(hook)
        if common_hook:
            for hook_name in HOOKS:
                tbl[f"_{hook_name}"].append(
                    lambda *args, hook_name=hook_name, **kw: (
                        common_hook(tbl, hook_name, *args, **kw)
                    )
                )
        # set table methods
        for meth_name, meth in table_methods.items():
            tbl.add_method.register(meth_name)(meth)
        # postprocessing
        if _on_define:
            _on_define(tbl)
        if on_define:
            on_define(cls, tbl)
        if migrate_indexes:
            if not index_migrator:
                raise RuntimeError('index_migrator is required')
            index_migrator(
                tbl,
                [
                    (idx_name, idx.fields, idx.kwargs)
                    for idx_name, idx in indexes.items()
                ]
            )
        return tbl

    def __init__(
            self,
            db,
            action,  # 'define_table' or 'Table'
            prefix=None,
            name=None,
            auto_pk=None,
            common_hook=None,
            migrate_indexes=False,
            index_migrator=None,
            on_define=None,
    ):
        pass
