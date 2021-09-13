from flask import Flask, render_template, request, redirect, make_response, flash
from functools import wraps
from model.user import User
import app_config
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = app_config.SECRET_KEY
app.config["MONGO_URI"] = "mongodb://localhost:27017/wad"
mongo = PyMongo(app)
db = mongo.db

def check_cookie(req):
    return User.get_user(db, req.cookies.get('username')).authorize(req.cookies.get('token')) 

def login_required(func):
    @wraps(func)
    def login_func(*arg, **kwargs):
        try:
            if check_cookie(request):
                return func(*arg, **kwargs)
        except:
            pass
        flash("Login required!")
        return redirect('/login')
    return login_func

def no_login(func):
    @wraps(func)
    def no_login_func(*arg, **kwargs):
        try:
            if check_cookie(request):
                flash("You've already logged in!")
                return redirect('/')
        except:
            pass
        return func(*arg, **kwargs)
    return no_login_func

# Home route - always redirect to login
@app.route('/')
def home():
    return redirect('/index')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@no_login
def login():
    if request.method =='GET':
        return render_template('login.html')

    user = request.form.get('username')
    pwd = request.form.get('password')
    if User.find_user(db, user): 
        current_user = User.get_user(db, user)
        if current_user.authenticate(pwd):
            token = current_user.init_session()
            resp = make_response(redirect('/index'))
            resp.set_cookie('username', user)
            resp.set_cookie('token', token)
            return resp
        else:
            flash("Username or password is incorrect!")
    else:
        flash("Username or password is incorrect!")
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    username = request.cookies.get('username')
    current_user = User.get_user(db, username)
    current_user.terminate_session()
    resp = make_response(redirect('/login'))
    resp.delete_cookie('username')
    resp.delete_cookie('token')
    flash("You've logged out!")
    return resp

@app.route('/register', methods=['POST', 'GET'])
@no_login
def register():
    if request.method == "GET":
        return render_template('register.html')

    username, password, password_confirm = request.form.get('username'), request.form.get('password'), request.form.get('password_confirm')

    if not User.find_user(db, username):
        if password == password_confirm:
            new_user = User.new(db, username, password)
            token = new_user.init_session()
            resp = make_response(redirect('/index'))
            resp.set_cookie('username', username)
            resp.set_cookie('token', token) 
            return resp
        else:
            flash("Passwords don't match!")
    else:
        flash("User already exists!")

    return render_template('register.html')

@app.route('/changepwd', methods=['POST', 'GET'])
@login_required
def changepwd():
    if request.method == "GET":
        return render_template("changepwd.html")

    username = request.cookies.get("username")
    old_pwd = request.form.get('old_pwd')
    new_pwd = request.form.get('new_pwd')
    new_pwd_confirm = request.form.get('new_pwd_confirm')

    current_user = User.get_user(db, username)
    if current_user.authenticate(old_pwd):
        if new_pwd == new_pwd_confirm:
            current_user.update_password(new_pwd)
            flash("Password updated!")
            return redirect('/')
        else:
            flash("New passwords don't match")
    else:
        flash("Old password is not correct!")
    return render_template("changepwd.html")

def allowed_extension(file_name):
    EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    extension = file_name.split('.')[-1].lower()
    return extension in EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def handle_upload():
    username = request.cookies.get('username')
    current_user = User.get_user(db, username)
    if request.method == 'GET':
        user_avatar = current_user.get_avatar()
        return render_template("avatar.html", user_avatar=user_avatar)
    
    if 'avatar-image' not in request.files:
        flash("File not found!")
        return redirect('/upload')
    
    file = request.files['avatar-image']

    if file.filename == '':
        flash("No file selected!")
        return redirect('/upload')

    if not allowed_extension(file.filename):
        flash("Invalid file extension!")
        return redirect('/upload')
    
    file_name = secure_filename(file.filename)
    
    try:
        user_avatar = current_user.get_avatar()

        try:
            if user_avatar != 'default.jpg':
                id = mongo.db.fs.files.find_one({"filename": user_avatar}).get('_id')
                mongo.db.fs.chunks.remove({'files_id': id})
                mongo.db.fs.files.remove({'_id': id})
        except:
            flash("Avatar is not in database!")

        mongo.save_file(file_name, file)
        current_user.set_avatar(file_name)
    except:
        flash("Error saving file!")
        return redirect('/upload')
    
    flash("Uploaded!")
    return redirect('/upload')

@app.route('/uploads/<filename>')
@login_required
def serve_uploaded(filename):
    if filename == 'default.jpg':
        return app.send_static_file(filename)
    return mongo.send_file(filename)

if __name__ == '__main__':
    app.run(host='localhost', port='5000', debug=True)
