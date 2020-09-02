from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import field_for

from sqlalchemy.orm import backref
from sqlalchemy_utils import UUIDType
import uuid

from sqlalchemy.sql import func

from datetime import datetime

db = SQLAlchemy()
ma = Marshmallow()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    tstamp = db.Column(db.DateTime(), default=func.current_timestamp())
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(100))
    display_name = db.Column(db.String(60))
    active = db.Column(db.Boolean(), default=True)
    is_admin = db.Column(db.Boolean(), default=False)

    # add one-to-one relationships
    user_details = db.relationship('UserDetail', backref='user', uselist=False)

    # add one-to-many relationships
    project_roles = db.relationship('ProjectRole', backref='user')

    # special use fields
    current_role = None

    # TODO feature: add a favorites table

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, value):
        return check_password_hash(self.password, value)

    @property
    def is_authenticated(self):
        if isinstance(self, AnonymousUserMixin):
            return False
        else:
            return True

    def is_active(self):
        return True

    def is_anonymous(self):
        if isinstance(self, AnonymousUserMixin):
            return True
        else:
            return False

    def get_id(self):
        return self.id

    def get_role(self, pid):
        """ Return the role of a specific project """
        if self.project_roles:
            for project_role in self.project_roles:
                if project_role.project_id == pid:
                    return project_role
                else:
                    return None
        else:
            return None

    def set_role(self, pid, role):
        """ Set the role of a specific project """
        if self.project_roles:
            for project_role in self.project_roles:
                if project_role.project_id == pid:
                    project_role.role = role
                    return True
            return False
        else:
            return None

    def update_current_role(self, pid):
        """ Sets the current_role to a string describing the user role of a single project for JSON """
        # FIXME this is a hack to JSONify the users role for a specific project (as a user may have many project roles)
        # FIXME if an endpoint needs to send the role for a specific project this must be called first
        role = self.get_role(pid)
        if role:
            self.current_role = role.display_string
            return True
        else:
            return False

    def has_subscription(self):
        """ Only checks the local database, for true confirmation use stripe_utils """
        if self.subscription is None:
            return False
        else:
            return True

    def is_owner(self, pid):
        if self.is_subscriber(pid):
            return True
        if ProjectRole.query.filter_by(project_id=pid, user_id=self.id, role='project_owner').first():
            return True
        return False

    def is_subscriber(self, pid):
        if ProjectRole.query.filter_by(project_id=pid, user_id=self.id, role='project_subscriber').first():
            return True
        return False

    def __repr__(self):
        return '<User %r>' % self.username

    def __json__(self):
        return ['username', 'email', 'current_role']


class UserDetail(db.Model):
    __tablename__ = 'user_details'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    job_title = db.Column(db.String(30))
    company = db.Column(db.String(30))
    address = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(30))
    country = db.Column(db.String(30))
    zip_code = db.Column(db.String(12))
    timezone = db.Column(db.String(60), default='UTC')

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<User Details: {}>'.format(self.id)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    tstamp = db.Column(db.DateTime(), default=func.current_timestamp())

    role = db.Column(db.String(12))

    user = db.relationship('User', backref='roles')

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Role: {}>'.format(self.role)


class ProjectRole(db.Model):
    __tablename__ = 'project_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    tstamp = db.Column(db.DateTime(), default=func.current_timestamp())

    role = db.Column(db.String(20))  # project_subscriber, project_owner, project_contributor, project_viewer

    project_id = db.Column(db.Integer(), db.ForeignKey('projects.id'))

    # init should be handled through sql alchemy model whenever possible

    @property
    def display_string(self):
        if self.role == "project_subscriber":
            return "Subscriber"
        elif self.role == "project_owner":
            return "Owner"
        elif self.role == "project_contributor":
            return "Contributor"
        elif self.role == "project_viewer":
            return "Viewer"
        else:
            return None

    def __repr__(self):
        return '<Project Role: {}>'.format(self.role)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    uuid = db.Column(UUIDType(binary=True), default=uuid.uuid4(), unique=True, nullable=False)
    name = db.Column(db.String(60))
    address = db.Column(db.String(60))
    city = db.Column(db.String(40))
    state = db.Column(db.String(30))
    zipcode = db.Column(db.String(15))
    country = db.Column(db.String(30))
    timezone = db.Column(db.String(60), default='UTC')
    description = db.Column(db.String(120))
    location = db.Column(db.String(60))
    eventtype = db.Column(db.String(60))
    deletion = db.Column(db.Boolean(), default=False)

    # add one-to-one relationships
    eventstats = db.relationship('EventsStats', backref=backref('project', cascade="all"), uselist=False, cascade="all, delete-orphan")

    # add one-to-many relationships
    entrants = db.relationship('Entrant', backref=backref('events', cascade="all"), cascade="all, delete-orphan")
    rungroups = db.relationship('RunGroup', backref=backref('events', cascade="all"), cascade="all, delete-orphan")
    applied_tags = db.relationship('AppliedTag', backref='events', lazy='dynamic')
    project_roles = db.relationship('ProjectRole', backref='events', lazy='dynamic', cascade="all, delete")

    def __init__(self, name, address, city, state, zipcode, country, timezone, description, location, eventtype, eventssstats=None, iosstats=None, entrants=[], rungroups=[], sitereportitems=[], id=None, uuid=None):
        # FIXME correct using mutable defaults, but without them sql alchemy complains when creating instance
        self.id = id
        self.uuid = uuid
        self.name = name

        self.address = address
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.country = country
        self.timezone = timezone
        self.description = description
        self.location = location
        self.eventtype = eventtype

        self.entrants = entrants
        self.rungroups = rungroups

        # create corresponding stats objects on new event creation
        self.eventsstats = eventssstats
        if self.eventsstats is None:
            self.eventsstats = EventsStats()

        # the user that created the project defaults to the owner
        #self.project_roles.append(ProjectRole("project_owner", user_id))

    def __repr__(self):
        return '<Project: {}>'.format(self.id)

    def __json__(self):
        return ['id', 'name', 'address', 'city', 'state', 'zipcode', 'country', 'description', 'location', 'eventtype']


class Entrant(db.Model):
    __tablename__ = 'entrants'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    firstname = db.Column(db.String(60))
    lastname = db.Column(db.String(60))
    carnumber = db.Column(db.String(60))
    carmake = db.Column(db.String(60))
    carmodel = db.Column(db.String(60))
    haspaid = db.Column(db.Boolean(), default=False)
    # TODO how to connect with car class in a nice way???

    # add one-to-many relationships
    rungroups = db.relationship('RunGroup', backref=backref('entrant', cascade="all"), cascade="all, delete-orphan")
    sessions = db.relationship('Session', backref=backref('entrant', cascade="all"), cascade="all, delete-orphan")
    logs = db.relationship('Log', backref=backref('entrant', cascade="all"), cascade="all, delete-orphan")

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Entrant: {}>'.format(self.id)

    def __json__(self):
        return ['id', 'sort', 'firstname', 'lastname', 'carnumber', 'carmake', 'carmodel', 'haspaid']

    def set_value(self, field, value):
        """Helper function that will timestamp state changes"""
        chk = field
        tstamp = field + 'tstamp'
        setattr(self, chk, value)
        setattr(self, tstamp, datetime.utcnow())
        # TODO could also stamp which user changed this value


class RunGroup(db.Model):
    __tablename__ = 'run_groups'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    groupnumber = db.Column(db.Integer())
    name = db.Column(db.String(60))

    # add one-to-many relationships
    vehicleclasses = db.relationship('VehicleClass', backref=backref('rungroup', cascade="all"), cascade="all, delete-orphan")

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Entrant: {}>'.format(self.id)

    def __json__(self):
        return ['id', 'groupnumber', 'name']


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    basetime = db.Column(db.String(60))
    correctedtime = db.Column(db.String(60))
    starttimestamp = db.Column(db.String(60))
    finishtimestamp = db.Column(db.String(60))
    penaltytime = db.Column(db.String(60))

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Entrant: {}>'.format(self.id)

    def __json__(self):
        return ['id', 'groupnumber', 'name']


class EventsStats(db.Model):
    __tablename__ = 'events_stats'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    entranttotal = db.Column(db.Integer(), default=0)
    cartotal = db.Column(db.Integer(), default=0)

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<EventsStats: {}>'.format(self.id)


class VehicleClass(db.Model):
    __tablename__ = 'vehicle_classes'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(60))
    shortname = db.Column(db.String(10))
    description = db.Column(db.String(255))

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<VehicleClass: {}>'.format(self.id)

    def __json__(self):
        return ['name', 'shortname', 'description']


class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer(), primary_key=True)
    event_uuid = db.Column(UUIDType(binary=True), db.ForeignKey('events.uuid'))
    entrant_id = db.Column(db.Integer(), db.ForeignKey('entrants.id'))
    tstamp = db.Column(db.DateTime(), default=func.current_timestamp())
    user = db.Column(db.String(30))
    logmsg = db.Column(db.String(255))

    # add one-to-many relationships
    applied_tags = db.relationship('AppliedTag', backref=backref('log', cascade="all"), cascade="all, delete")

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Log: {}>'.format(self.id)

    def __json__(self):
        return ['tstamp', 'user', 'logmsg']


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer(), primary_key=True)
    # organization_id = db.Column(db.Integer(), db.ForeignKey('organizations.id'))
    term = db.Column(db.String(30))
    user = db.Column(db.String(30))
    description = db.Column(db.String(255))

    # add one-to-many relationships
    applied_tags = db.relationship('AppliedTag', backref='tag', lazy='dynamic')

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<Tag: {}>'.format(self.id)

    def __json__(self):
        return ['term']


class AppliedTag(db.Model):
    __tablename__ = 'applied_tags'
    id = db.Column(db.Integer(), primary_key=True)
    event_uuid = db.Column(UUIDType(binary=True), db.ForeignKey('events.uuid'))
    tag_id = db.Column(db.Integer(), db.ForeignKey('tags.id'))
    log_id = db.Column(db.Integer(), db.ForeignKey('logs.id'))

    # init should be handled through sql alchemy model whenever possible

    def __repr__(self):
        return '<AppliedTag: {}>'.format(self.id)


# MARSHMALLOW SERIALIZATION MODELS
# Note that many 'id' and 'project_id' fields are dump_only because these id's will get recreated on load (import) when
# the relationships are recreated; current design only uses UUID as primary key where needed to reduce overhead

class BaseSchema(ma.ModelSchema):
    class Meta:
        sqla_session = db.session


class AppliedTagSchema(ma.ModelSchema):
    class Meta(BaseSchema.Meta):
        model = AppliedTag
        include_fk = True

    id = field_for(AppliedTag, 'id', dump_only=True)
    #project_id = field_for(AppliedTag, 'id', dump_only=True)
    log_id = field_for(AppliedTag, 'id', dump_only=True)

    # backrefs
    event = field_for(AppliedTag, 'event', dump_only=True)
    log = field_for(AppliedTag, 'log', dump_only=True)
    tag = field_for(AppliedTag, 'tag', dump_only=True)


class LogSchema(ma.ModelSchema):
    class Meta(BaseSchema.Meta):
        model = Log
        include_fk = True

    id = field_for(Log, 'id', dump_only=True)
    #project_id = field_for(Log, 'project_id', dump_only=True)
    entrant_id = field_for(Log, 'entrant_id', dump_only=True)

    applied_tags = ma.Nested(AppliedTagSchema, many=True)

    # backrefs
    event = field_for(Log, 'event', dump_only=True)
    entrant = field_for(Log, 'entrant', dump_only=True)
    io_item = field_for(Log, 'io_item', dump_only=True)


class EntrantSchema(ma.ModelSchema):
    class Meta(BaseSchema.Meta):
        model = Entrant

    id = field_for(Entrant, 'id', dump_only=True)
    event_id = field_for(Entrant, 'event_id', dump_only=True)

    logs = ma.Nested(LogSchema, many=True)

    # backrefs
    event = field_for(Entrant, 'event', dump_only=True)


class EventsStatsSchema(ma.ModelSchema):
    class Meta(BaseSchema.Meta):
        model = EventsStats

    id = field_for(EventsStats, 'id', dump_only=True)
    event_id = field_for(EventsStats, 'event_id', dump_only=True)

    # backrefs
    event = field_for(EventsStats, 'event', dump_only=True)


class EventSchema(ma.ModelSchema):
    class Meta(BaseSchema.Meta):
        model = Event
        exclude = ('project_roles', 'itemlogs', 'applied_tags', 'deletion')

    id = field_for(Event, 'id', dump_only=True)
    eventsstats = ma.Nested(EventsStatsSchema)

    entrants = ma.Nested(EntrantSchema, many=True)
    logs = ma.Nested(LogSchema)
    applied_tags = ma.Nested(AppliedTagSchema)
    #project_roles = ma.Nested(ProjectRoleSchema)
