from flask import Blueprint, render_template, flash, request, redirect, url_for, current_app, session, send_from_directory
from flask_login import login_required, current_user

from flask_jsontools import jsonapi

from werkzeug.datastructures import FileStorage
import io

from app.extensions import cache
from app.forms import NewProjectForm
from app.models import db, User, ProjectRole, Project, DeviceItem, DevicesStats, IOItem, IOsStats, Log, Tag, AppliedTag, SiteReportItem, ProjectSchema

import app.permissions as permissions

from app.queries import update_device_stats, update_ios_stats, get_tstamp_counts_per_day, get_logs_by_applied_tag
from app.importer import DevicesImporter, IOsImporter

from flask_marshmallow import pprint

import os

from app.decorators import project_sub_active
from app.utils import user_sub_available


projects = Blueprint('projects', __name__)

ALLOWED_IMPORT_EXTENSIONS = {'txt', 'csv'}
ALLOWED_RESTORE_EXTENSION = 'bak'
ARCHIVE_FOLDER = '_archives'
OFFLINE = False  # FIXME get this from config file


@projects.route('/')
@login_required
#@cache.cached(timeout=10)
def index():
    # only render projects if online; admins not subject to this
    online = True
    if OFFLINE and not current_user.is_admin:
        online = False

    if online:
        # get the project ids this user has access too
        user_project_ids = []
        for project_role in current_user.project_roles:
            user_project_ids.append(project_role.project_id)

        # use the ids to get project objects
        user_projects = db.session.query(Project).filter(Project.id.in_(user_project_ids)).all()

        # format the project data for html rendering
        access = {}
        for p in user_projects:
            access[p.id] = p.name

        return render_template('projects.html', pids=access)
    else:
        return render_template('offline.html')


@projects.route('/new', methods=["GET", "POST"])
@login_required
def project_new():
    """Create new project"""

    form = NewProjectForm()

    if form.validate_on_submit() and user_sub_available(current_user):
        p = Project(form.name.data, form.company.data, form.address.data, form.city.data, form.state.data, form.zipcode.data, form.country.data, form.timezone.data, form.description.data, form.location.data)
        p.project_roles.append(ProjectRole(role="project_subscriber", user_id=current_user.id))
        db.session.add(p)
        db.session.commit()

        #flash("New projected added successfully", "success")
        return redirect(request.args.get("next") or url_for(".index"))
    # else:
    #     flash('Form error.')
    if user_sub_available(current_user):
        return render_template("projects/projectnew.html", form=form)

    return render_template("projects/projectsubscribe.html")


@projects.route('/<int:pid>/api/archive', methods=["GET"])
@login_required
def project_archive(pid):
    """Archive project"""

    permission = permissions.ProjectOwnerPermission(pid)

    if permission.can():
        p = Project.query.filter_by(id=pid).first()

        if p:
            filename = str(p.uuid) + '.bak'
            folder = current_app.config.get('ARCHIVE_PATH')
            project_schema = ProjectSchema()

            # dump project model to json
            data = project_schema.dumps(p).data
            #pprint(data)

            # save json to temporary file (should be deleted by server chron job)
            with open(folder + filename, 'w') as outfile:
                outfile.write(data)

            delete = request.args.get('delete', default=False, type=bool)

            # on delete a backup is made, but not sent to the user, then the entire project is deleted
            if delete:
                # TODO in future just mark the project for deletion by chron later so that user can undo this action
                db.session.delete(p)
                db.session.commit()

                return redirect(request.args.get("next") or url_for(".index"))

        return send_from_directory(ARCHIVE_FOLDER, filename, as_attachment=True)

    return "Access Denied", 403


@projects.route('/api/restore/', methods=["POST"])
@login_required
def project_restore():
    """Restore project"""

    if request.method == 'POST':
        # check if the user has a free project in their subscription
        if user_sub_available(current_user):
            # check if the post request has the file part
            if _check_file_exists(request):
                if _check_file_type(request, restore=True):
                    project_schema = ProjectSchema()

                    file = request.files['file']

                    if isinstance(file, FileStorage):
                        data = io.StringIO(file.stream.read().decode("UTF8", errors='ignore'), newline=None).read()

                        p = project_schema.loads(data)

                        if Project.query.filter_by(uuid=p.data.uuid).first():
                            return "Project Already Exists", 500
                        else:
                            p.data.project_roles.append(ProjectRole(role="project_subscriber", user_id=current_user.id))

                            db.session.add(p.data)
                            db.session.commit()
                            return "Success", 200

                    return "File Upload Error", 500

                return "Wrong File Type", 500

            return "No File Selected", 500

        return render_template("projects/projectsubscribe.html")

    return "Method Not Found", 404


@projects.route('/<int:pid>/dashboard/')
@login_required
@project_sub_active
def dashboard(pid):
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():

        pname = Project.query.filter_by(id=pid).one().name

        is_owner = current_user.is_owner(pid)

        has_devices = False
        sd = None
        if DeviceItem.query.filter_by(project_id=pid).first():
            has_devices = True

            # only get devices stats if the project has devices
            sd = DevicesStats.query.filter_by(project_id=pid).one()
            update_device_stats(sd)

        has_ios = False
        si = None
        if IOItem.query.filter_by(project_id=pid).first():
            has_ios = True

            # only get ios stats if the project has devices
            si = IOsStats.query.filter_by(project_id=pid).one()
            update_ios_stats(si)

        has_sitereports = False
        if SiteReportItem.query.filter_by(project_id=pid).first():
            has_sitereports = True

        tags = Tag.query.all()
        devices_t_logs = {}
        ios_t_logs = {}

        devices_t_logs['Untagged'] = get_logs_by_applied_tag(pid, type='device', limit=10)
        ios_t_logs['Untagged'] = get_logs_by_applied_tag(pid, type='io', limit=10)

        for tag in tags:
            devices_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'device', 10)
            ios_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'io', 10)

        return render_template('projects/dashboard.html', pid=pid, pname=pname, is_owner=is_owner,
                               has_devices=has_devices,
                               devices_stats=sd,
                               has_ios=has_ios,
                               ios_stats=si,
                               has_sitereports=has_sitereports,
                               tags=tags,
                               devices_t_logs=devices_t_logs,
                               ios_t_logs=ios_t_logs)

    return "Access Denied", 403


# TODO should probably move to API prefix and refactor to "import"
@projects.route('/<int:pid>/devicesupload/', methods=['POST'])
@login_required
def devices_upload(pid):
    if request.method == 'POST':
        permission = permissions.ProjectOwnerPermission(pid)

        if permission.can():
            # check if the post request has the file part
            if _check_file_exists(request):
                if _check_file_type(request):
                    im = DevicesImporter()
                    im.read_data(request.files['file'])
                    im.write_sql(db, int(pid))
                    return "Success", 200

                return "Wrong File Type", 500

    return "Access Denied", 403


@projects.route('/<int:pid>/iosupload/', methods=['POST'])
@login_required
def ios_upload(pid):
    test = request
    if request.method == 'POST':
        permission = permissions.ProjectOwnerPermission(pid)

        if permission.can():
            # check if the post request has the file part
            if _check_file_exists(request):
                if _check_file_type(request):
                    im = IOsImporter()
                    im.read_data(request.files['file'])
                    # check that the csv data has an "address" field so that device import file can't be used by mistake
                    if im.check_format():
                        im.write_sql(db, int(pid))
                        return "Success", 200
                    return "Invalid Import Format", 500

                return "Wrong File Type", 500

    return "Access Denied", 403


# SITE REPORT HANDLING
# render the main site report list table for a particular project
@projects.route('/<int:pid>/sitereports/')
@login_required
@project_sub_active
def sitereports(pid):
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        pname = Project.query.filter_by(id=pid).one().name

        tags = Tag.query.all()
        devices_t_logs = {}
        ios_t_logs = {}
        for tag in tags:
            devices_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'device', 10)
            ios_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'io', 10)

        return render_template('projects/sitereports.html', pid=pid, pname=pname)

    return "Access Denied", 403


# render the page for creating a new site report
@projects.route('/<int:pid>/sitereports/new/', methods=['GET'])
@login_required
@project_sub_active
def sitereports_new(pid):
    """Create new site report"""
    permission = permissions.ProjectContributorPermission(pid)

    if permission.can():
        # note that forms are not used here; data will come from api
        pname = Project.query.filter_by(id=pid).one().name

        # TODO get collection of log items to populate the site report BY USER AND DATE
        tags = Tag.query.all()
        devices_t_logs = {}
        ios_t_logs = {}
        for tag in tags:
            devices_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'device', 10)
            ios_t_logs[tag.term] = get_logs_by_applied_tag(pid, tag.id, 'io', 10)

        return render_template("projects/sitereportsnew.html", pid=pid, pname=pname, tags=tags, devices_t_logs=devices_t_logs,
                               ios_t_logs=ios_t_logs)

    return "Access Denied", 403


# render the page for viewing/editing a site report
@projects.route('/<int:pid>/sitereports/<int:sid>/', methods=['GET'])
@login_required
@project_sub_active
def sitereport(pid, sid):
    """View site report"""
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        pname = Project.query.filter_by(id=pid).one().name

        item = SiteReportItem.query.filter_by(id=sid).one()
        userstamp = item.userstamp
        html = item.html
        return render_template("projects/sitereportssingle.html", pid=pid, sid=sid, pname=pname, userstamp=userstamp, html=html)

    return "Access Denied", 403


# select all site report items in the database for a particular project, add a new site report
@projects.route('/<int:pid>/api/sitereports/', methods=['GET', 'POST'])
@login_required
@project_sub_active
@jsonapi
def api_sitereports(pid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            items = SiteReportItem.query.filter_by(project_id=pid).order_by(SiteReportItem.id.desc()).all()
            return items

        return "Access Denied", 403

    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            username = 'Guest'
            if hasattr(current_user, 'username'):
                username = current_user.username

            html = request.form['html']

            db.session.add(SiteReportItem(project_id=pid, html=html, userstamp=username))
            db.session.commit()

            return "Success", 200

        return "Access Denied", 403


# select or update a single site report
@projects.route('/<int:pid>/api/sitereports/<int:sid>/', methods=['GET', 'POST'])
@login_required
def api_sitereports_single(pid, sid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            item = SiteReportItem.query.filter_by(id=sid).one()
            return item.html

        return "Access Denied", 403

    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            item = SiteReportItem.query.filter_by(id=sid).one()

            # save the new html
            item.html = request.form['html']
            db.session.commit()
            return "Success", 200

        return "Access Denied", 403


# PROJECT USER HANDLING
# render the main user list table for a particular project
@projects.route('/<int:pid>/users/')
@login_required
def users(pid):
    raise NotImplementedError
    # permission = permissions.ProjectViewerPermission(pid)
    #
    # if permission.can():
    #     pname = Project.query.filter_by(id=pid).one().name
    #     return render_template('/projects/users.html', pid=pid, pname=pname)
    #
    # return "Access Denied", 403


# select all users in the database for a particular project; give a user access to the project, remove user access
@projects.route('/<int:pid>/api/users/', methods=['GET', 'POST', 'DELETE'])
@login_required
@jsonapi
def api_users(pid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            project_roles = ProjectRole.query.filter_by(project_id=pid).all()

            user_ids = []
            for project_role in project_roles:
                user_ids.append(project_role.user_id)

            # use the ids to get user objects
            project_users = db.session.query(User).filter(User.id.in_(user_ids)).all()

            for user in project_users:
                user.update_current_role(pid)

            return project_users

        return "Access Denied", 403

    # give a user permissions for this project
    if request.method == 'POST':
        permission = permissions.ProjectOwnerPermission(pid)

        if permission.can():
            if request.form['user_email'] is not None:
                user_email = request.form['user_email']

                user = User.query.filter_by(email=user_email).first()

                if user:
                    role = request.form['role']

                    # transpose form text to role name
                    if role == 'Viewer':
                        role = 'project_viewer'
                    elif role == 'Contributor':
                        role = 'project_contributor'
                    elif role == 'Owner':
                        role = 'project_owner'
                    else:
                        return "Invalid Role", 500

                    if user.get_role(pid):
                        # user already has a project role; update role
                        if user.is_subscriber(pid):
                            return "User Role Change Not Allowed", 500
                        else:
                            # ok to update
                            user.set_role(pid, role)
                            db.session.commit()
                            return "User Role Updated", 200
                    else:
                        # create new project role for user
                        db.session.add(ProjectRole(role=role, user_id=user.id, project_id=pid))
                        db.session.commit()
                        return "User Added", 200
                else:
                    return "User Email Not Found", 500
            return "User Email Required", 500
        return "Access Denied", 403

    # remove user permissions for this project
    if request.method == 'DELETE':
        permission = permissions.ProjectOwnerPermission(pid)

        if permission.can():
            if request.form['user_email'] is not None:
                user_email = request.form['user_email']

                user = User.query.filter_by(email=user_email).first()
                user_role = user.get_role(pid)

                if user:
                    if user_role:
                        if user.is_subscriber(pid):
                            return "User Role Change Not Allowed", 500
                        else:
                            # ok to delete
                            db.session.delete(user_role)
                            db.session.commit()
                            return "Success", 200
                    else:
                        return "User Role Not Found", 500
                else:
                    return "User Email Not Found", 500
            return "User Email Required", 500
        return "Access Denied", 403


# DEVICE HANDLING
# render the main device list table for a particular project
@projects.route('/<int:pid>/devices/')
@login_required
@project_sub_active
def devices(pid):
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        pname = Project.query.filter_by(id=pid).one().name
        tags = Tag.query.all()
        return render_template('/projects/devices.html', pid=pid, pname=pname, tags=tags)

    return "Access Denied", 403


# render the page for creating a new Device item
@projects.route('/<int:pid>/devices/new/', methods=['GET'])
@login_required
@project_sub_active
def devices_new(pid):
    """Create new Device item"""
    permission = permissions.ProjectContributorPermission(pid)

    if permission.can():
        # note that forms are not used here; data will come from api
        pname = Project.query.filter_by(id=pid).one().name

        return render_template("projects/devicesnew.html", pid=pid, pname=pname)

    return "Access Denied", 403


# select all device items in the database for a particular project, add a new Device item
@projects.route('/<int:pid>/api/devices/', methods=['GET', 'POST'])
@login_required
@project_sub_active
@jsonapi
def api_devices(pid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)
        if permission.can():
            items = DeviceItem.query.filter_by(project_id=pid).all()
            return items

        return "Access Denied", 403

# add a new Device item
    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            username = 'Guest'
            if hasattr(current_user, 'username'):
                username = current_user.username

            if request.form['device'] != '':
                test = request
                # TODO get sort number from database
                db.session.add(DeviceItem(project_id=pid, sort=0, **request.form.to_dict()))
                db.session.commit()
            else:
                return "Device is Required", 500

            return "Success", 200

        return "Access Denied", 403


# update the status of a device item
@projects.route('/<int:pid>/api/devices/<int:did>/', methods=['POST'])
@login_required
def api_devices_single(pid, did):
    permission = permissions.ProjectContributorPermission(pid)

    if permission.can():
        username = 'Guest'
        if hasattr(current_user, 'username'):
            username = current_user.username

        item = DeviceItem.query.filter_by(id=did).one()

        item.userstamp = username

        if hasattr(item, request.form['field']):
            v = getattr(item, request.form['field'])

            if v is True:
                item.set_value(request.form['field'], False)
                db.session.commit()
                return 'False', 200
            else:
                item.set_value(request.form['field'], True)
                db.session.commit()
                return 'True', 200

        return "Failure", 200

    return "Access Denied", 403


# IO HANDLING
# render the main io list table for a particular project
@projects.route('/<int:pid>/ios/', methods=['GET'])
@login_required
@project_sub_active
def ios(pid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            pname = Project.query.filter_by(id=pid).one().name
            tags = Tag.query.all()
            return render_template('projects/ios.html', pid=pid, pname=pname, tags=tags)

        return "Access Denied", 403


# render the page for creating a new IO item
@projects.route('/<int:pid>/ios/new/', methods=['GET'])
@login_required
@project_sub_active
def ios_new(pid):
    """Create new IO item"""
    permission = permissions.ProjectContributorPermission(pid)

    if permission.can():
        # note that forms are not used here; data will come from api
        pname = Project.query.filter_by(id=pid).one().name

        return render_template("projects/iosnew.html", pid=pid, pname=pname)

    return "Access Denied", 403


# select all IO items in the database for a particular project, add a new IO item
@projects.route('/<int:pid>/api/ios/', methods=['GET', 'POST'])
@login_required
@jsonapi
def api_ios(pid):
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            items = IOItem.query.filter_by(project_id=pid).all()
            return items

        return "Access Denied", 403

    # add a new IO item
    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            username = 'Guest'
            if hasattr(current_user, 'username'):
                username = current_user.username

            if request.form['address'] != '':
                # TODO get sort number from database
                db.session.add(IOItem(project_id=pid, sort=0, **request.form.to_dict()))
                db.session.commit()
            else:
                return "IO Address is Required", 500

            return "Success", 200

        return "Access Denied", 403


# update the status of an IO item
@projects.route('/<int:pid>/api/ios/<int:iid>/', methods=['POST'])
@login_required
def api_ios_single(pid, iid):
    permission = permissions.ProjectContributorPermission(pid)

    if permission.can():
        username = 'Guest'
        if hasattr(current_user, 'username'):
            username = current_user.username

        item = IOItem.query.filter_by(id=iid).one()

        item.userstamp = username
        if request.form['status'] == 'Done':
            item.status = 'Done'
        elif request.form['status'] == 'Repeat':
            item.status = 'Repeat'
        elif request.form['status'] == 'Reset':
            item.status = 'Untested'
        elif request.form['status'] == 'Removed':
            item.status = 'Removed'
        else:
            db.session.rollback()
            return "Failure", 500

        db.session.commit()
        return "Success", 200

    return "Access Denied", 403


# LOG HANDLING
@projects.route('/<int:pid>/api/devices/<int:did>/logs/', methods=['GET', 'POST'])
@login_required
@jsonapi
def api_devices_logs(pid, did):
    # select a list of logs for the requested Device item
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            logs = Log.query.filter_by(deviceitem_id=did).all()
            return logs

        return "Access Denied", 403

    # insert a new log message for a Device item
    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            if _create_log_and_tags(pid, None, did, request):
                item = DeviceItem.query.filter_by(id=did).one()
                item.hasdevicelog = True
                db.session.commit()
                return "Success!", 200
            else:
                return "Failure!", 500

        return "Access Denied", 403


@projects.route('/<int:pid>/api/ios/<int:iid>/logs/', methods=['GET', 'POST'])
@login_required
@jsonapi
def api_ios_logs(pid, iid):
    # select a list of logs for the requested IO item
    if request.method == 'GET':
        permission = permissions.ProjectViewerPermission(pid)

        if permission.can():
            logs = Log.query.filter_by(ioitem_id=iid).all()
            return logs

        return "Access Denied", 403

    # insert a new log message for an IO item
    if request.method == 'POST':
        permission = permissions.ProjectContributorPermission(pid)

        if permission.can():
            if _create_log_and_tags(pid, iid, None, request):
                item = IOItem.query.filter_by(id=iid).one()
                item.hasiolog = True
                db.session.commit()
                return "Success!", 200
            else:
                return "Failure!", 500

        return "Access Denied", 403


def _create_log_and_tags(pid, iid, did, request):
    username = 'Guest'
    if hasattr(current_user, 'username'):
        username = current_user.username

    project_uuid = Project.query.filter_by(id=pid).one().uuid

    if iid:
        l = Log(project_uuid=project_uuid, ioitem_id=iid, user=username, logmsg=request.form['msg'])
    elif did:
        l = Log(project_uuid=project_uuid, deviceitem_id=did, user=username, logmsg=request.form['msg'])
    else:
        return False

    # add the list of tags to the log item
    tags = request.form['tags'].split(';')

    # if there are no tags skip adding an AppliedTag
    if tags[0] != '':
        l.applied_tags.extend([AppliedTag(project_uuid=project_uuid, tag_id=t) for t in tags])

    db.session.add(l)
    db.session.commit()

    return True


# HANDLE STATISTICS
# select the IO statistics for a project
@projects.route('/<int:pid>/api/ios/stats/')
@login_required
# @jsonapi
def api_ios_stats(pid):
    # TODO need to handle query parameters here in case requester only wants specific stat fields
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        s = IOsStats.query.filter_by(project_id=pid).one()

        update_ios_stats(s)

        return '[' + '{:.1f}'.format(s.iountested) + ',' + '{:.1f}'.format(s.iodone) + ',' + '{:.1f}'.format(s.iorepeat) + ',' + '{:.1f}'.format(s.ioremoved) + ']'

    return "Access Denied", 403


# select the io activity statistics for a project
@projects.route('/<int:pid>/api/ios/stats/activity/')
@login_required
@jsonapi
def api_ios_stats_activity(pid):
    # TODO need to handle query parameters here in case requester only wants specific stat fields
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        ios_activity = [get_tstamp_counts_per_day(pid, IOItem, 7, 'status', 'Done'),
                        get_tstamp_counts_per_day(pid, IOItem, 7, 'status', 'Repeat'),
                        get_tstamp_counts_per_day(pid, IOItem, 7, 'status', 'Removed')]

        return ios_activity

    return "Access Denied", 403


# select the device statistics for a project
@projects.route('/<int:pid>/api/devices/stats/')
@login_required
# @jsonapi
def api_devices_stats(pid):
    # TODO need to handle query parameters here in case requester only wants specific stat fields
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        s = DevicesStats.query.filter_by(project_id=pid).one()

        update_device_stats(s)

        return '[' + '{:.1f}'.format(s.deviceequipmentpct) + ',' + '{:.1f}'.format(s.deviceconduitpct) + ',' + '{:.1f}'.format(s.devicewirespct) + ',' + '{:.1f}'.format(s.devicefieldpct) + ',' + '{:.1f}'.format(s.devicepanelpct) + ']'

    return "Access Denied", 403


# select the device activity statistics for a project
@projects.route('/<int:pid>/api/devices/stats/activity/')
@login_required
@jsonapi
def api_devices_stats_activity(pid):
    # TODO need to handle query parameters here in case requester only wants specific stat fields
    permission = permissions.ProjectViewerPermission(pid)

    if permission.can():
        devices_activity = [get_tstamp_counts_per_day(pid, DeviceItem, 7, 'equipmentchk', True, 'equipmentchktstamp'),
                            get_tstamp_counts_per_day(pid, DeviceItem, 7, 'conduitchk', True, 'conduitchktstamp'),
                            get_tstamp_counts_per_day(pid, DeviceItem, 7, 'wirepullchk', True, 'wirepullchktstamp'),
                            get_tstamp_counts_per_day(pid, DeviceItem, 7, 'fieldconnectchk', True, 'fieldconnectchktstamp'),
                            get_tstamp_counts_per_day(pid, DeviceItem, 7, 'panelconnectchk', True, 'panelconnectchktstamp')]

        return devices_activity

    return "Access Denied", 403


def _check_file_exists(req):
    # check if the post request has the file part
    if 'file' not in req.files:
        # flash('No file part')
        return False
    file = req.files['file']
    # if user does not select file, browser also submit a empty part without filename
    if file.filename == '':
        # flash('No selected file')
        return False

    return True


def _check_file_type(req, restore=False):
    file = req.files['file']
    if file and _allowed_file(file.filename, restore=restore):
        return True

    return False


def _allowed_file(filename, restore=False):
    if restore:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESTORE_EXTENSION
    else:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMPORT_EXTENSIONS
