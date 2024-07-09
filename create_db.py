from flask import current_app
from datetime import datetime
from app.extensions import db
from app.models.user import Blog_User
from app.models.posts import Blog_Posts
from app.models.themes import Blog_Theme
from app.models.stats import Blog_Stats
from app.dummy_data import authors, posts, themes, comments
from app.account.helpers import hash_password
from app.models.helpers import update_stats_users_total, update_stats_users_active

# Constants for admin, default author, and default user
ADMIN_NAME = "Super Admin"
ADMIN_EMAIL = "super@admin"
ADMIN_PASSWORD = "admin123"
ADMIN_PICTURE = "Picture_default.jpg"

DEFAULT_AUTHOR_NAME = "The Travel Blog Team"
DEFAULT_AUTHOR_EMAIL = "travel@team"
DEFAULT_AUTHOR_PASSWORD = "author123"
DEFAULT_AUTHOR_ABOUT = authors.authors_about
DEFAULT_AUTHOR_PICTURE = "Picture_default_author.jpg"

DEFAULT_USER_NAME = "[Deleted]"
DEFAULT_USER_EMAIL = "deleted@users"
DEFAULT_USER_PASSWORD = "user123"
DEFAULT_USER_ABOUT = "This user's account has been deleted"
DEFAULT_USER_PICTURE = "Picture_default.jpg"

# Function to create admin account
def create_admin_account():
    if not Blog_User.query.filter_by(type="super_admin").first():
        super_admin = Blog_User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=hash_password(ADMIN_PASSWORD),
            type="super_admin",
            picture=ADMIN_PICTURE
        )
        db.session.add(super_admin)
        db.session.commit()

# Function to create default author and user accounts
def create_default_accounts():
    if not Blog_User.query.filter_by(type="author").first():
        default_author = Blog_User(
            name=DEFAULT_AUTHOR_NAME,
            email=DEFAULT_AUTHOR_EMAIL,
            password=hash_password(DEFAULT_AUTHOR_PASSWORD),
            type="author",
            about=DEFAULT_AUTHOR_ABOUT,
            picture=DEFAULT_AUTHOR_PICTURE
        )
        db.session.add(default_author)

    if not Blog_User.query.filter_by(type="user").first():
        default_user = Blog_User(
            name=DEFAULT_USER_NAME,
            email=DEFAULT_USER_EMAIL,
            password=hash_password(DEFAULT_USER_PASSWORD),
            type="user",
            about=DEFAULT_USER_ABOUT,
            picture=DEFAULT_USER_PICTURE
        )
        db.session.add(default_user)

    db.session.commit()

# Function to create blog statistics
def create_blog_stats():
    if not Blog_Stats.query.first():
        blog_stats = Blog_Stats()
        db.session.add(blog_stats)
        db.session.commit()

# Function to create themes
def create_themes():
    if not Blog_Theme.query.first():
        for theme_data in themes.themes_data:
            theme = Blog_Theme(
                theme=theme_data["theme"],
                picture=theme_data["picture"],
                picture_source=theme_data["picture_source"]
            )
            db.session.add(theme)
        db.session.commit()

# Function to create dummy user accounts
def create_dummy_accounts():
    if not Blog_User.query.filter_by(type="dummy").first():
        for idx, author_data in enumerate(authors.authors_data):
            dummy_user = Blog_User(
                name=author_data["name"],
                email=f"{idx}@example.com",
                password=hash_password("password123"),
                type="dummy",
                about=authors.authors_about,
                picture=author_data["picture"]
            )
            db.session.add(dummy_user)
        db.session.commit()

        update_stats_users_total()
        update_stats_users_active(1)

# Function to create dummy posts
def create_dummy_posts():
    if not Blog_Posts.query.first():
        for post_data in posts.post_data:
            dummy_post = Blog_Posts(
                theme_id=post_data["theme"],
                title=post_data["title"],
                intro=posts.post_intro,
                body=posts.post_body,
                author_id=post_data["author_id"],
                picture_v=post_data["picture_v"],
                picture_v_source=post_data["picture_v_source"],
                picture_h=post_data["picture_h"],
                picture_h_source=post_data["picture_h_source"],
                picture_s=post_data["picture_s"],
                picture_s_source=post_data["picture_s_source"],
                picture_alt=post_data["picture_alt"],
                admin_approved=True,
                date_submitted=datetime.strptime(post_data["date_submitted"], "%Y-%m-%d"),
                date_to_post=datetime.strptime(post_data["date_to_post"], "%Y-%m-%d")
            )
            db.session.add(dummy_post)
        db.session.commit()

# Run all functions to initialize the application
def initialize_blog_app():
    create_admin_account()
    create_default_accounts()
    create_blog_stats()
    create_themes()
    create_dummy_accounts()
    create_dummy_posts()

# Entry point when running this script
if __name__ == "__main__":
    initialize_blog_app()
