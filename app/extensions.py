from collections import namedtuple
from functools import partial

from flask import current_app
from app.flask_sslify import SSLify
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, current_user
from flask_assets import Environment

# principal imports
from flask_principal import Principal, identity_loaded, RoleNeed, UserNeed

import app.permissions as permissions

from app.models import User

# Setup flask sslify
sslify = SSLify()

# Setup flask cache
cache = Cache()

# init flask assets
assets_env = Environment()

debug_toolbar = DebugToolbarExtension()

login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "warning"

# Setup flask principal
principal = Principal()


@login_manager.user_loader
def load_user(userid):
    # return an instance of the User model
    return User.query.get(userid)


@identity_loaded.connect  #_via(current_app)
# called every time a http request is made to check the loaded user against the action > from checking permission.can()
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.role))

    # add all project roles this user has to the identity
    if hasattr(current_user, 'project_roles'):
        for pr in current_user.project_roles:
            if pr.role == 'project_subscriber':
                identity.provides.add(permissions.ProjectSubscriberNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectOwnerNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectContributorNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectViewerNeed(str(pr.project_id)))

            if pr.role == 'project_owner':
                identity.provides.add(permissions.ProjectOwnerNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectContributorNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectViewerNeed(str(pr.project_id)))

            elif pr.role == 'project_contributor':
                identity.provides.add(permissions.ProjectContributorNeed(str(pr.project_id)))
                identity.provides.add(permissions.ProjectViewerNeed(str(pr.project_id)))
            elif pr.role == 'project_viewer':
                identity.provides.add(permissions.ProjectViewerNeed(str(pr.project_id)))
            # FIXME currently not used
            elif pr.role == 'device_get':
                identity.provides.add(permissions.DeviceGetNeed(str(pr.project_id)))
            elif pr.role == 'device_update':
                identity.provides.add(permissions.DeviceUpdateNeed(str(pr.project_id)))
            elif pr.role == 'io_get':
                identity.provides.add(permissions.IOGetNeed(str(pr.project_id)))
            elif pr.role == 'io_update':
                identity.provides.add(permissions.IOUpdateNeed(str(pr.project_id)))
