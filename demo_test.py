from voodoodal import ModelBuilder
from pydal import DAL
import os

from demo_model import Model


_db = DAL(
    folder=f'{os.path.dirname(__file__)}/db_test'
)


@ModelBuilder(_db)
class db(Model):
    pass


assert db is _db
db.commit()

# check signatures
assert {db.thing.created, db.thing.created_by, db.thing.updated, db.thing.updated_by}.issubset({*db.thing})

# check rname prefix
assert all(t._rname == f'test_{t._tablename}' for t in db)

# check auto_pk
assert db.color._primarykey == ['id']


john = db.person.insert(name='John')
db.thing.insert(owner=john, name='ball')
assert db.thing.get_like('ball%')[0].name == 'ball'
db.thing(1).update_record(name='big ball')
row: Model.thing = db(db.thing).select().first()

assert row.owner_thing_name == [row.owner, row.name]
assert row.owner_id == row.owner
assert row.owner_name_meth() == [row.owner, row.name]
assert db.thing.get_like('big%')[0].name == 'big ball'
