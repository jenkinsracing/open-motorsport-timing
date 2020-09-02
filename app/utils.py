from datetime import datetime
import pytz


def user_sub_available(user):
    # check if the user has a subscription (None means no active subscription)
    if user.subscription:
        # get user subscription project limit (defined by what plan they subscribed to)
        limit = user.subscription.project_limit

        # count how many projects they own as a subscriber
        project_count = user_sub_count(user)

        # if user has reached the limit of their current subscription they don't have space for another active project
        if project_count >= limit:
            return False

        # user subscription has space for new active project
        return True

    return False


def user_sub_count(user):
    # count how many projects they own as a subscriber
    project_count = 0
    for pr in user.project_roles:
        if pr.role == 'project_subscriber':
            project_count += 1

    return project_count


def get_project_limit(plan):
    plan = int(plan)  # plan variable could be a string
    if plan == 1001:
        return 1
    elif plan == 1003:
        return 3
    elif plan == 1010:
        return 10
    else:
        # TODO throw error?
        print('Failed to get project limit' + str(plan))
        return 0


def timezone_choices():
    """Helper that generates a list of timezones sorted by ascending UTC offset. The timezones are represented as
        tuple pairs of timezone name and a string representation of the current UTC offset.
    """
    # TODO: Perfect for caching; the list is unlikely to change more than hourly.
    tzs = []
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    for tz_name in pytz.country_timezones['us']:  # was pytz.common_timezones
        local_now = now.astimezone(pytz.timezone(tz_name))
        # The real seconds help us sort the TZ list
        offset = local_now.utcoffset()
        offset_real_secs = offset.seconds + offset.days * 24 * 60 ** 2
        offset_txt = local_now.strftime(
            '(UTC %z) [%a %H:%M] {0}').format(tz_name)
        tzs.append((offset_real_secs, tz_name, offset_txt))
    tzs.sort()
    return [tz[1:] for tz in tzs]
