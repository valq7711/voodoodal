from voodoodal import Table, Field
from pydal import DAL
import datetime

now = datetime.datetime.now()


class sign_created(Table):
    created = Field('datetime', default=now)
    created_by = Field('reference person')


class sign_updated(Table):
    updated = Field('datetime', default=now)
    updated_by = Field('reference person')


class Model(DAL):

    __config__ = {
        # prefixes `rname` of all tables
        'prefix': 'test_',

        # add `primarykey = ['id']` if there is `id`-field with type != 'id'
        # see `color`-table below
        'auto_pk': True,
    }

    class person(Table):
        name = Field('string', required=True)

    class color(Table):
        id = Field('integer')
        name = Field('string', required=True)

    # to inject signature(s) just specify them as base class(es)
    class thing(sign_created, sign_updated):

        owner = Field('reference person', required=True)
        name = Field('string', required=True)

        @property
        def owner_id(row):
            """Define another virtual field."""
            return row.thing.owner

        @property
        def owner_thing_name(row):
            """Define virtual field."""
            return [row.thing.owner, row.thing.name]

        def owner_name_meth(row):
            """Define method field."""
            return [row.thing.owner, row.thing.name]

        @classmethod
        def get_like(self, patt):
            """Define table-method.

            This will turn into `db.thing.get_like(<pattern>)`-method.
            """
            db = self._db
            assert self is db.thing
            return db(self.name.like(patt)).select()

        # hooks go as is

        def before_insert(args):
            print('before_insert', args)

        def before_update(s, args):
            print('before_update', s, args)

        def after_update(s, args):
            print('after_insert', s, args)

        @classmethod
        def _on_define(cls, t: Table):
            """Postprocessing hook."""
            print(f"_on_define: table '{t}' created")

        __extra__ = ['whatever']

    # special hooks
    def on_action(tbl, hook, *args):
        """Convenient common hook for all before/after_insert/update/delete actions."""
        print('on_action', tbl, hook, args)

    @classmethod
    def on_define_table(cls, tcls, t):
        """Postprocessing hook, invoked for each table."""
        print(f"on_define_table: table '{t}' created from {tcls}")

    @classmethod
    def on_define_model(cls, db: DAL, extras: dict):
        """Postprocessing hook."""
        print('on_define_model', db, extras)
