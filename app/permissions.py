from collections import namedtuple
from functools import partial

from flask_principal import Permission

# FIXME at the moment "get" permissions are not used for protecting getting lists; for now it's available to viewers

ProjectNeed = namedtuple('project', ['method', 'value'])
ProjectSubscriberNeed = partial(ProjectNeed, 'subscriber')  # partial func where "method" property is preset to 'subscriber'
ProjectOwnerNeed = partial(ProjectNeed, 'owner')  # partial func where "method" property is preset to 'owner'
ProjectContributorNeed = partial(ProjectNeed, 'contributor')  # partial func where "method" property is preset to 'contributor'
ProjectViewerNeed = partial(ProjectNeed, 'viewer')  # partial func where "method" property is preset to 'viewer'

DeviceNeed = namedtuple('device', ['method', 'value'])
DeviceGetNeed = partial(DeviceNeed, 'get')  # partial func where "method" property is preset to 'get'
DeviceUpdateNeed = partial(DeviceNeed, 'update')  # partial func where "method" property is preset to 'update'

IONeed = namedtuple('device', ['method', 'value'])
IOGetNeed = partial(IONeed, 'get')  # partial func where "method" property is preset to 'get'
IOUpdateNeed = partial(IONeed, 'update')  # partial func where "method" property is preset to 'update'


class ProjectSubscriberPermission(Permission):
    """ The subscriber is the user which has the paid subscription that makes the project active; there is only one"""
    def __init__(self, pid):
        need = ProjectSubscriberNeed(str(pid))
        super(ProjectSubscriberPermission, self).__init__(need)


class ProjectOwnerPermission(Permission):
    def __init__(self, pid):
        need = ProjectOwnerNeed(str(pid))
        super(ProjectOwnerPermission, self).__init__(need)


class ProjectContributorPermission(Permission):
    def __init__(self, pid):
        need = ProjectContributorNeed(str(pid))
        super(ProjectContributorPermission, self).__init__(need)


class ProjectViewerPermission(Permission):
    def __init__(self, pid):
        need = ProjectViewerNeed(str(pid))
        super(ProjectViewerPermission, self).__init__(need)


# TODO revamp this somehow; at the moment these are not used so access is not very granular
class DeviceGetPermission(Permission):
    def __init__(self, pid):
        need = DeviceGetNeed(str(pid))
        super(DeviceGetPermission, self).__init__(need)


class DeviceUpdatePermission(Permission):
    def __init__(self, pid):
        need = DeviceUpdateNeed(str(pid))
        super(DeviceUpdatePermission, self).__init__(need)


class IOGetPermission(Permission):
    def __init__(self, pid):
        need = IOGetNeed(str(pid))
        super(IOGetPermission, self).__init__(need)


class IOUpdatePermission(Permission):
    def __init__(self, pid):
        need = IOUpdateNeed(str(pid))
        super(IOUpdatePermission, self).__init__(need)
