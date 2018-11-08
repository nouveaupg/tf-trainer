from flask import Flask, render_template, request, abort, Response
import user
import images
import boto3
import uuid

app = Flask(__name__)


@app.route('/')
def present_login():
    return render_template("login.html", error="")


@app.route('/login', methods=["POST"])
def do_login():
    user_obj = user.User(request.form["username"], request.form["password"])
    logged_in = user_obj.login()
    if logged_in and user_obj.username == "admin":
        session_token = logged_in[1]
        return render_template("admin.html",
                               session_id=session_token,
                               user_count=user.User.count_users(),
                               image_count=images.PostedImage.count_posted_images())
    elif logged_in:
        session_token = logged_in[1]
        return render_template("user.html",
                               session_id=session_token,
                               last_login=user_obj.last_logged_in.isoformat(),
                               username=user_obj.username,
                               uploaded_images=images.PostedImage.count_posted_images(uploader_id=logged_in[0]),
                               years=range(1990, 2019))
    return render_template("login.html", error="Invalid username/password.")


@app.route('/user/<session_token>')
def user_page(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            return render_template("user.html",
                                   session_id=session_token,
                                   last_login=user_obj.last_logged_in.isoformat(),
                                   username=user_obj.username,
                                   uploaded_images=images.PostedImage.count_posted_images(uploader_id=user_obj.user_id),
                                   years=range(1990, 2019))
    return render_template("login.html", error="Invalid session.")


@app.route('/admin/<session_token>')
def admin_page(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            if user_obj.username == "admin":
                return render_template("admin.html",
                                       session_id=session_token,
                                       user_count=user.User.count_users(),
                                       image_count=images.PostedImage.count_posted_images())
            else:
                abort(403)
    return render_template("login.html", error="Invalid session.")


@app.route('/logout/<session_token>')
def logout(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            user_obj.logout(session_token)
    return render_template("login.html", error="")


@app.route('/add-user/<session_token>', methods=["POST"])
def add_user(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            if request.form['password'] == request.form['password_repeat']:
                new_user = user.User(request.form['username'], request.form['password'])
                if new_user.create_user():
                    return list_users(session_token=session_token)
                else:
                    abort(Response("Could not create new user, perhaps the username already exists or is invalid?"))
            else:
                abort(Response("Could not create new user. Passwords did not match both times."))
    return render_template("login.html", error="Invalid session.")


@app.route('/users/last-login/<session_token>')
def list_users(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            if user_obj.username == "admin":
                all_users = user.User.get_all_users(user.User.SORT_LAST_LOGIN)
                template_data = []
                for each_user in all_users:
                    user_data = {"username": each_user.username,
                                 "user_id": each_user.user_id,
                                 "last_logged_in": each_user.last_logged_in.isoformat(),
                                 "last_image_posted": images.PostedImage.date_of_last_image_posted_by(
                                     each_user.user_id),
                                 "total_images_posted": images.PostedImage.count_posted_images(
                                     uploader_id=each_user.user_id)}
                    template_data.append(user_data)
                return render_template("list_users.html",
                                       users=template_data,
                                       session_id=session_token)
            else:
                # admin only page
                abort(403)
    return render_template("login.html", error="Invalid session.")


@app.route('/images/not-processed/<session_token>')
def list_unprocessed_images(session_token=None):
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            unprocessed_images = images.PostedImage.get_images()
            template_data = []
            for each in unprocessed_images:
                image_data = {"url": each.url,
                              "year": each.year,
                              "make": each.make,
                              "model": each.model,
                              "uploaded": each.uploaded.isoformat(),
                              "processed": each.processed}
                template_data.append(image_data)
            return render_template("user_images.html",
                                   user_images=template_data,
                                   username="Unprocessed Images",
                                   session_id=session_token,
                                   images_posted=len(template_data))
    return render_template("login.html", error="Invalid session.")


@app.route('/images/user/<user_id>/<session_token>')
def images_from_user_id(user_id=None, session_token=None):
    if user_id is None:
        abort(Response("Invalid request."))
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            if user_obj.username == "admin":
                unprocessed_images = images.PostedImage.get_images(uploader_id=user_id)
                template_data = []
                for each in unprocessed_images:
                    image_data = {"url": each.url,
                                  "year": each.year,
                                  "make": each.make,
                                  "model": each.model,
                                  "uploaded": each.uploaded.isoformat(),
                                  "processed": each.processed}
                    template_data.append(image_data)
                return render_template("user_images.html",
                                       user_images=template_data,
                                       username=user_obj.username,
                                       last_logged_in=user_obj.last_logged_in,
                                       session_id=session_token,
                                       images_posted=len(template_data))
            else:
                # forbidden to non-admin users
                abort(403)
        else:
            return render_template("login.html", error="Invalid session.")
    abort(Response("Invalid request."))


@app.route('/submit-image/', methods=["POST"])
def submit_auto_image():
    session_token = request.form["session_token"]
    if session_token:
        user_obj = user.User()
        if user_obj.validate_session(session_token):
            s3 = boto3.resource('s3')
            new_file_name = "{0}.jpg".format(uuid.uuid4())
            file = request.files["image_upload"]
            if file.mimetype == "image/jpeg":
                s3.Bucket('tf-trainer').put_object(Key=new_file_name, Body=file)
                # NOTE: CHANGE THIS TO YOUR OWN BUCKET
                obj = s3.Bucket('tf-trainer').Object(new_file_name)
                obj.Acl().put(ACL="public-read")
                new_url = "https://s3.amazonaws.com/tf-trainer/" + new_file_name
                new_posted_image = images.PostedImage(request.form['make'], request.form['model'],
                                                      request.form['year'], new_url, user_obj.user_id)
                new_posted_image.store()
                return user_page(session_token=session_token)
            else:
                abort(Response("Invalid data upload. Only image/jpeg MIME type file uploads are allowed."))
    return render_template("login.html", error="Invalid session.")
