from flask import current_app
from flask_login import current_user


def user_context_processor():
    """Inject user context into jinja2 templates"""

    if current_user.is_authenticated:
        user = current_user._get_current_object()
    else:
        user = None
    return {
        'user': user,
    }


def stripe_pk_processor():
    """Inject proper public key into jinja2 templates"""

    stripe_pk = current_app.config.get('STRIPE_PUBLISH_KEY')

    return {
        'stripe_pk': stripe_pk,
    }


def register_processors(app):
    app.context_processor(user_context_processor)
    app.context_processor(stripe_pk_processor)

