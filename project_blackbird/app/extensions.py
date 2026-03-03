"""Application extension instances with offline-safe fallbacks."""

try:
    from flask_migrate import Migrate
except ImportError:
    class Migrate:  # type: ignore
        def init_app(self, app, db):  # noqa: ANN001, D401
            return None

try:
    from flask_sqlalchemy import SQLAlchemy
except ImportError:
    class _Session:
        def add(self, *_args, **_kwargs):
            return None

        def flush(self):
            return None

        def commit(self):
            return None

        def remove(self):
            return None

    class SQLAlchemy:  # type: ignore
        Model = object
        Integer = int
        String = str
        DateTime = object
        Float = float

        def __init__(self):
            self.session = _Session()

        def init_app(self, app):
            return None

        def create_all(self):
            return None

        def drop_all(self):
            return None

        def Column(self, *_args, **_kwargs):
            return None

        def ForeignKey(self, *_args, **_kwargs):
            return None

        def relationship(self, *_args, **_kwargs):
            return []


db = SQLAlchemy()
migrate = Migrate()
