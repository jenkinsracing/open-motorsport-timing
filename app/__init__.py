#! ../env/bin/python

from flask import Flask
from webassets.loaders import PythonLoader as PythonAssetsLoader

from app.processors import register_processors

from app import assets
from app.models import db, ma
from app.controllers.main import main
from app.controllers.projects import projects

from app.json_enc import AlchemyEncoder

from app.extensions import (
    sslify,
    cache,
    assets_env,
    debug_toolbar,
    login_manager,
    principal
)

import stripe


def create_app(object_name):
    """
    An flask application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/

    Arguments:
        object_name: the python path of the config object,
                     e.g. app.settings.ProdConfig
    """

    app = Flask(__name__)

    app.config.from_object(object_name)

    # FIXME stripe testing
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')

    # initialize sslify
    sslify.init_app(app)

    # initialize the cache
    cache.init_app(app)

    # initialize the debug tool bar
    #debug_toolbar.init_app(app)

    # initialize SQLAlchemy
    db.init_app(app)

    # initialize Marshmallow
    ma.init_app(app)

    # initialize principal extension
    principal.init_app(app)

    # json encoding
    app.json_encoder = AlchemyEncoder

    login_manager.init_app(app)

    # Import and register the different asset bundles
    assets_env.init_app(app)

    assets_loader = PythonAssetsLoader(assets)
    for name, bundle in assets_loader.load_bundles().items():
        assets_env.register(name, bundle)

    # register our blueprints
    app.register_blueprint(main)
    app.register_blueprint(projects, url_prefix='/projects')

    # register custom context processors
    register_processors(app)

    return app
