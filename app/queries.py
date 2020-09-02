from sqlalchemy.sql import func, and_
from datetime import datetime, timedelta

from app.models import db, User, ProjectRole, Project, DeviceItem, DevicesStats, IOItem, IOsStats, Log, AppliedTag


"""Collection of query handling functions"""


def update_device_stats(stats):
    """Update statistics stored in DB for Devices"""
    # TODO need a more intelligent way manage this, currently it can get called multiple times to render a single page
    items = DeviceItem.query.filter_by(project_id=stats.project_id).all()

    device_total = len(items)

    e, c, w, f, p, n, r = 0, 0, 0, 0, 0, 0, 0
    for i in items:
        r_t = 0
        if i.equipmentchk is True:
            e += 1
            r_t += 1
        if i.conduitchk is True:
            c += 1
            r_t += 1
        if i.wirepullchk is True:
            w += 1
            r_t += 1
        if i.fieldconnectchk is True:
            f += 1
            r_t += 1
        if i.panelconnectchk is True:
            p += 1
            r_t += 1
        if r_t == 0:
            n += 1
        if r_t == 5:
            r += 1

    stats.devicetotal = device_total
    stats.devicenone = n
    stats.deviceready = r
    stats.deviceequipment = e
    stats.deviceconduit = c
    stats.devicewires = w
    stats.devicefield = f
    stats.devicepanel = p

    if device_total > 0 or device_total is None:
        stats.devicenonepct = (n / device_total) * 100
        stats.devicereadypct = (r / device_total) * 100
        stats.deviceequipmentpct = (e / device_total) * 100
        stats.deviceconduitpct = (c / device_total) * 100
        stats.devicewirespct = (w / device_total) * 100
        stats.devicefieldpct = (f / device_total) * 100
        stats.devicepanelpct = (p / device_total) * 100

    db.session.commit()


def update_ios_stats(stats):
    """Update statistics stored in DB for IOs"""
    # TODO need a more intelligent way manage this, currently it can get called multiple times to render a single page
    items = IOItem.query.filter_by(project_id=stats.project_id).all()

    io_total = len(items)

    d, r, rm, u = 0, 0, 0, 0
    for i in items:
        if i.status == 'Done':
            d += 1
        if i.status == 'Repeat':
            r += 1
        if i.status == 'Removed':
            rm += 1
        if i.status == 'Untested':
            u += 1

    stats.iototal = io_total
    stats.iountested = u
    stats.iodone = d
    stats.iorepeat = r
    stats.ioremoved = rm

    if io_total > 0 or io_total is None:
        stats.iountestedpct = (u / io_total) * 100
        stats.iodonepct = (d / io_total) * 100
        stats.iorepeatpct = (r / io_total) * 100
        stats.ioremovedpct = (rm / io_total) * 100
    db.session.commit()


def get_tstamp_counts_per_day(project_id, model, days, field=None, value=None, tstamp='tstamp'):
    """Get the number of tstamps for a model X days into the past"""
    counts = []
    today = datetime.utcnow().date()  # work with UTC date because database has UTC timestamps

    i = 0
    while i < days:
        td = timedelta(days=i)
        d = today - td

        if field is None:
            counts.append(db.session.query(model).filter(model.project_id == project_id, func.date(getattr(model, tstamp)) == d).count())
        else:
            counts.append(db.session.query(model).filter(model.project_id == project_id, func.date(getattr(model, tstamp)) == d, getattr(model, field) == value).count())
        i += 1

    counts.reverse()

    return counts


def get_logs_by_applied_tag(project_id, tag_id=None, type=None, limit=None):
    """Get log messages (via backref) from applied tags in descending order with option to limit"""
    project_uuid = Project.query.filter_by(id=project_id).one().uuid
    logs = []

    if type == "io":
        type_column = Log.ioitem_id
    elif type == "device":
        type_column = Log.deviceitem_id
    else:
        type_column = None

    if tag_id is not None:
        # get logs by specific tag
        if type_column is not None:
            # a type of log was specified so we must join and inspect the Log foreign keys to see what type it is
            applied_tags = db.session.query(AppliedTag).join(Log, and_(AppliedTag.project_uuid == Log.project_uuid,
                                                                       AppliedTag.log_id == Log.id)).filter(
                AppliedTag.project_uuid == project_uuid, AppliedTag.tag_id == tag_id, type_column.isnot(None)).order_by(AppliedTag.id.desc()).limit(
                limit).all()
        else:
            # no type was specified so we just return all tagged logs
            applied_tags = db.session.query(AppliedTag).filter(AppliedTag.project_uuid == project_uuid,
                                                               AppliedTag.tag_id == tag_id).order_by(AppliedTag.id.desc()).limit(limit).all()

        for at in applied_tags:
            logs.append(at.log)

    else:
        # get logs that are untagged
        if type_column is not None:
            # get a specific type of log that is untagged
            logs = db.session.query(Log).filter(Log.project_uuid == project_uuid, type_column.isnot(None),
                                         Log.applied_tags == None).order_by(Log.id.desc()).limit(limit).all()
        else:
            # get all logs that are untagged
            logs = db.session.query(Log).filter(Log.project_uuid == project_uuid, Log.applied_tags == None).order_by(Log.id.desc()).limit(limit).all()

    return logs
