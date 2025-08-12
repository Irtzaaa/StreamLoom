# Social Video App

A Flask-based social media platform for uploading, liking, commenting, and sharing short videos, inspired by TikTok and YouTube Shorts.

## Features
- User authentication (register, login, logout)
- Video feed with "For You" and "Following" tabs
- Video upload with captions
- Like, comment, and reply functionality
- User profiles with stats (followers, following, videos, likes)
- Profile picture upload
- Follow/unfollow users
- Responsive design with TikTok-like scrolling

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure the `static/uploads` folder exists
3. Run the app: `python app.py`
4. Access at `http://localhost:5000`

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Styling: Custom CSS with modern design

## Directory Structure
- `static/css/` - Stylesheets
- `static/js/` - JavaScript files
- `static/uploads/` - User-uploaded videos and profile pictures
- `templates/` - HTML templates
- `app.py` - Main Flask application