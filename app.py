from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///social.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'jpg', 'jpeg', 'png'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), default='default.jpg')
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', backref='followed', lazy='dynamic')
    following = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower', lazy='dynamic')
    videos = db.relationship('Video', backref='creator', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('Like', backref='video', lazy='dynamic')
    comments = db.relationship('Comment', backref='video', lazy='dynamic')

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        user = User(firstname=firstname, lastname=lastname, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please set your profile picture.', 'success')
        return redirect(url_for('profile', user_id=user.id))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('feed', tab='for_you'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/feed/<tab>')
@login_required
def feed(tab='for_you'):
    if tab == 'following':
        followed_ids = [f.followed_id for f in current_user.following]
        videos = Video.query.filter(Video.user_id.in_(followed_ids)).order_by(Video.created_at.desc()).all()
    else:
        videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template('feed.html', videos=videos, tab=tab, Comment=Comment)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    videos = user.videos.order_by(Video.created_at.desc()).all()
    stats = {
        'followers': user.followers.count(),
        'following': user.following.count(),
        'videos': user.videos.count(),
        'likes': sum(video.likes.count() for video in user.videos.all())
    }
    return render_template('profile.html', user=user, videos=videos, stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file', 'error')
            return redirect(request.url)
        file = request.files['video']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            caption = request.form['caption']
            video = Video(filename=filename, caption=caption, user_id=current_user.id)
            db.session.add(video)
            db.session.commit()
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('profile', user_id=current_user.id))
        flash('Invalid file format', 'error')
    return render_template('upload.html')

@app.route('/like/<int:video_id>', methods=['POST'])
@login_required
def like(video_id):
    video = Video.query.get_or_404(video_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, video_id=video_id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'status': 'unliked', 'likes': video.likes.count()})
    like = Like(user_id=current_user.id, video_id=video_id)
    db.session.add(like)
    db.session.commit()
    return jsonify({'status': 'liked', 'likes': video.likes.count()})

@app.route('/comment/<int:video_id>', methods=['POST'])
@login_required
def comment(video_id):
    video = Video.query.get_or_404(video_id)
    content = request.form['content']
    parent_id = request.form.get('parent_id')
    comment = Comment(content=content, user_id=current_user.id, video_id=video_id, parent_id=parent_id or None)
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user': {
                'firstname': comment.user.firstname,
                'lastname': comment.user.lastname
            },
            'timestamp': comment.timestamp.isoformat(),
            'replies': []
        }
    })

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        existing_follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
        if existing_follow:
            db.session.delete(existing_follow)
            db.session.commit()
            return jsonify({'status': 'unfollowed', 'followers': user.followers.count()})
        follow = Follow(follower_id=current_user.id, followed_id=user_id)
        db.session.add(follow)
        db.session.commit()
        return jsonify({'status': 'followed', 'followers': user.followers.count()})
    return jsonify({'status': 'cannot_follow_self'})

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            if current_user.profile_picture != 'default.jpg':
                old_file = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                if os.path.exists(old_file):
                    os.remove(old_file)
            current_user.profile_picture = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Invalid file format. Please upload a JPG, JPEG, or PNG image.', 'error')
    else:
        flash('No file selected.', 'error')
    return redirect(url_for('profile', user_id=current_user.id))

@app.route('/share/<int:video_id>')
@login_required
def share(video_id):
    video = Video.query.get_or_404(video_id)
    share_url = url_for('feed', tab='for_you', _external=True) + f'#video-{video_id}'
    return jsonify({'status': 'success', 'share_url': share_url})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=False)
