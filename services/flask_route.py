import os
import sys

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_smorest import Api, Blueprint
from flask_sqlalchemy import SQLAlchemy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
import sys

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from backend.services.database import server
from backend.services.models import Stop, StopSchema


class APIConfig:
    API_TITLE = "MTA_API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_UI_URL = (
        "https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"
    )


server.config.from_object(APIConfig)
api = Api(server)


stops = Blueprint("stops", "api", url_prefix="/api", description="Operations on stops")


@stops.route("/stops")
class StopsCollection(MethodView):

    @stops.response(status_code=200, schema=StopSchema(many=True))
    def get(self):

        stopSchema = StopSchema(many=True)

        stopsQuery = Stop.query.all()

        stops = stopSchema.dump(stopsQuery, many=True)

        return stops


api.register_blueprint(stops)

if __name__ == "__main__":
    server.run(port=6543, debug=True)
