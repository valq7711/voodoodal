import pydal.validators as pydal_validators
from .voodoodal import DBValidatorWrapper


def is_not_in_db(*a, **kw):
    return DBValidatorWrapper(lambda db: pydal_validators.IS_NOT_IN_DB(db, *a, **kw))


def is_in_db(*a, **kw):
    return DBValidatorWrapper(lambda db: pydal_validators.IS_IN_DB(db, *a, **kw))
