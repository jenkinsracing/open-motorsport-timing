""" OMT Web App - V0.1 - © 2019 Jenkins Racing"""

from app import create_app


if __name__ == "__main__":
    app = create_app('app.settings.DevConfig')
    app.run()
else:
    app = create_app('app.settings.ProdConfig')
