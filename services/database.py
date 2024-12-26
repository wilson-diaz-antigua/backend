import os
from pathlib import Path

from dotenv import dotenv_values
from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlmodel import SQLModel, create_engine

env_path = Path(__file__).parent.parent / ".env.postgres"


vals = dotenv_values(env_path)

vercel = vals.get("VERCEL_URL")

db = SQLAlchemy()
ma = Marshmallow()
server = Flask(__name__)
CORS(server)
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
migrate = Migrate(server, db)
server.config["SQLALCHEMY_DATABASE_URI"] = vercel
server.config["PROPAGATE_EXCEPTIONS"] = True
db.init_app(server)
ma.init_app(server)
