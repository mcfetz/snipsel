from __future__ import annotations

from flask_caching import Cache
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
cache = Cache()
