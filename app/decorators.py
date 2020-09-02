from functools import wraps
from flask import g, render_template, request, redirect, url_for
from flask_login import current_user

from app.models import db, User, ProjectRole, Project


def project_sub_active(f):
    """ decorator to return the lock page if a view is accessed """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pid = kwargs.get('pid')

        if not _project_sub_active(pid):
            return _render_project_expired(pid)
        return f(*args, **kwargs)
    return decorated_function


def _project_sub_active(pid):
    """ check the local database to see if subscription is active; does not hit stripe """
    # get the project
    p = Project.query.filter_by(id=pid).one()
    # get the user of the project that has role of subscriber
    print('Check Subscription: getting subscriber with PID', pid)
    s = p.project_roles.filter_by(project_id=pid, role='project_subscriber').first()
    print('Check Subscription: subscriber is', s)

    # check if the subscriber user of this project has an active subscription
    if s is not None:
        # check for subscription (canceled subscription that reaches end time gets deleted from local db via web hooks)
        if s.user.subscription is not None:
            # check if the subscription is active, this could be false if there is a payment issue, but sub not canceled
            if s.user.subscription.active:
                return True
            else:
                print('Check Subscription: subscriber user subscription is not active')
                return False
        else:
            print('Check Subscription: subscriber user has no subscription')
            return False
    else:
        # FIXME a project that has no subscriber should log an error
        print('Check Subscription: project has no subscriber')
        return False


def _render_project_expired(pid):
    pname = Project.query.filter_by(id=pid).one().name

    is_subscriber = current_user.is_subscriber(pid)

    return render_template('projects/expired.html', pid=pid, pname=pname, is_subscriber=is_subscriber)
