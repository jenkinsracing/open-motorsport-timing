import tempfile
db_file = tempfile.NamedTemporaryFile()


class Config(object):
    SECRET_KEY = 'f8It0va1eRLF'


class ProdConfig(Config):
    ENV = 'prod'
    SQLALCHEMY_DATABASE_URI = 'mysql://'
    SQLALCHEMY_POOL_RECYCLE = 280

    ARCHIVE_PATH = ''

    CACHE_TYPE = 'simple'


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///db-local.db'

    ARCHIVE_PATH = 'app/_archives/'

    CACHE_TYPE = 'null'
    ASSETS_DEBUG = True


class TestConfig(Config):
    ENV = 'test'
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_file.name
    SQLALCHEMY_ECHO = True

    CACHE_TYPE = 'null'
    WTF_CSRF_ENABLED = False
