#!/usr/bin/env python

import os
import sys

from datetime import datetime
import time

from flask_script import Manager, Server
from flask_script.commands import ShowUrls, Clean
from app import create_app
from app.models import db, User, Event, ProjectRole, Entrant, RunGroup, Tag
from app.importer import IOsImporter

from getpass import getpass

# default to dev config because no one should use this in
# production anyway
env = os.environ.get('app_ENV', 'dev')
app = create_app('app.settings.%sConfig' % env.capitalize())

manager = Manager(app)
manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
        in the context of the app
    """

    return dict(app=app, db=db, User=User)


@manager.command
def createdb():
    """ Creates a database with all of the tables defined in your SQLAlchemy models
    """

    db.create_all()

    # always create the admin account
    adduser(email='admin@commissioning.io', username='Administrator', password='V*FyHkF32tNERFy6')
    setadmin(email='admin@commissioning.io', is_admin=True)

    # always create some standard log tags
    db.session.add(Tag(term='Wiring'))
    db.session.add(Tag(term='Mechanical'))
    db.session.add(Tag(term='Damaged'))
    db.session.add(Tag(term='Resource'))
    db.session.add(Tag(term='Downtime'))
    db.session.add(Tag(term='Urgent'))
    db.session.add(Tag(term='Mismatch'))
    db.session.add(Tag(term='Missing'))

    db.session.commit()


@manager.command
def adduser(email=None, username=None, password=None):
    """ Creates a new user """
    if username is None:
        username = input("Username: ")
        email = input("Email: ")
        password = getpass()

    if User.query.filter_by(username=username).count():
        sys.exit("User by that name already exists")

    if User.query.filter_by(email=email).count():
        sys.exit("User with that email already exists")

    db.session.add(User(email, username, password))
    db.session.commit()


@manager.command
def setadmin(email=None, is_admin=None):
    """ Set/Reset a user as admin """
    if email is None:
        email = input("Username: ")

    if is_admin is None:
        is_admin = input("Is Admin: ")
        if is_admin == "True":
            is_admin = True
        else:
            is_admin = False

    user = User.query.filter_by(email=email).one()
    user.is_admin = is_admin
    db.session.commit()



@manager.command
def addrecords():
    """ Creates some test records """

    # create project 1
    _create_plant('Event1', 5, 5)
    # create project 2
    _create_plant('Event2', 15, 15)

    # TODO add user rights for one of these projects to a test user to test user rights and access


@manager.command
def createproject():

    name = input("Project Name: ")
    address = input("Address: ")
    city = input("City: ")
    state = input("State: ")
    zipcode = input("Zip: ")
    country = input("Country: ")
    description = input("Description: ")
    location = input("Location: ")

    e = Event(name, address, city, state, zipcode, country, description, location)
    db.session.add(e)
    db.session.commit()


@manager.command
def importprojectio(fpath=None, project_id=None, tc=None):
    """ import io from csv to the database """
    if fpath is None:
        path = input("Path: ")
        project_id = input("Project ID: ")
        tc = input("From test case template?: ")

    im = IOsImporter()
    im.read_data(path)
    if tc == 'y':
        im.convert_testcase('AJ', 'ajenkins')
    im.write_sql(db, int(project_id))


@manager.command
def quick():
    createdb()
    adduser(email='asdf@asdf.com', username='testuser', password='asdfasdf')
    #addsub('asdf@asdf.com')
    #addrecords()

    # importprojectio(path='res/io-local.csv', ioproject_id=1)


def _create_event(event_name, entrant_count, rg_count):
    name = event_name
    address = '123 Fake Street'
    city = 'Fakerton'
    state = 'Montana'
    zipcode = '55555'
    country = 'USA'
    description = 'summer autocross'
    location = 'parkinglot'
    user_id = 2

    e = Event(name, address, city, state, zipcode, country, description, location)
    e.project_roles.append(ProjectRole(role="project_subscriber", user_id=user_id))
    # TODO add default project role
    db.session.add(e)
    db.session.commit()

    event_id = e.id
    firstname = "name"
    lastname = "last"
    carnumber = "1"
    carmake = "carmake"
    carmodel = "carmodel"
    haspaid = False

    i = 0
    while i < entrant_count:
        db.session.add(Entrant(event_id=event_id, firstname=firstname + str(i), lastname=lastname + str(i), carnumber=carnumber + str(i), carmake=carmake + str(i), carmodel=carmake + str(i), haspaid=haspaid))
        i += 1

    db.session.commit()

    i = 0
    while i < rg_count:
        db.session.add(RunGroup(event_id=event_id, groupnumber=i, name=firstname + str(i)))
        i += 1

    db.session.commit()


if __name__ == "__main__":
    manager.run()
