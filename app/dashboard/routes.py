from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from app.extensions import db
from app.models.user import BlogUser
from app.models.posts import BlogPost
from app.dashboard.forms import PostForm
from app.dashboard.helpers import check_blog_picture, delete_blog_img
from app.models.themes import BlogTheme
from app.models.helpers import (
    update_stats_users_active,
    update_approved_post_stats,
    change_authorship_of_all_posts,
)
from app.models.likes import BlogLike
from app.models.bookmarks import BlogBookmark
from app.models.comments import BlogComment, BlogReply
from app.models.helpers import update_likes, update_bookmarks, delete_comment, delete_reply
from datetime import datetime
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

dashboard = Blueprint('dashboard', __name__)

# USER MANAGEMENT: Admin access only

@dashboard.route("/dashboard/manage_users", methods=["GET", "POST"])
@login_required
def manage_users():
    user_type = current_user.type
    if user_type in ["admin", "super_admin"]:
        all_users = BlogUser.query.order_by(BlogUser.id).all()
        return render_template("dashboard/users_table.html", logged_in=current_user.is_authenticated, all_users=all_users)
    else:
        flash("Access denied: admin access only.")
        return redirect(url_for('website.home'))

@dashboard.route("/dashboard/manage_users/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_user(id):
    account_types = ["admin", "author", "user"]
    account_blocked = ["FALSE", "TRUE"]
    user = BlogUser.query.get_or_404(id)

    if request.method == "POST":
        email_exists = BlogUser.query.filter(BlogUser.id != id, BlogUser.email == request.form.get("email_update")).first()
        username_exists = BlogUser.query.filter(BlogUser.id != id, BlogUser.name == request.form.get("username_update")).first()

        if email_exists:
            flash("This email is already registered.")
        elif username_exists:
            flash("This username is already taken.")
        else:
            if user.type == "author" and request.form.get("accttype_update") != "author":
                change_authorship_of_all_posts(user.id, 2)

            user.name = request.form.get("username_update")
            user.email = request.form.get("email_update")
            user.type = request.form.get("accttype_update")
            user.blocked = request.form.get("acctblocked_update")

            try:
                if request.form.get("acctblocked_update") == "TRUE":
                    block_comments_replies(user.id, True)
                elif request.form.get("acctblocked_update") == "FALSE":
                    block_comments_replies(user.id, False)

                db.session.commit()
                flash("User updated successfully!")
                return redirect(url_for('dashboard.manage_users'))
            except:
                db.session.rollback()
                flash("Error updating user.")
    return render_template("dashboard/users_user_update.html", logged_in=current_user.is_authenticated, user=user, account_types=account_types, account_blocked=account_blocked)

@dashboard.route("/dashboard/manage_users/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_user(id):
    user = BlogUser.query.get_or_404(id)

    if request.method == "POST":
        if id == 1:
            flash("Authorization error: cannot delete this user.")
        else:
            try:
                if user.type == "author":
                    change_authorship_of_all_posts(user.id, 2)

                if user.comments:
                    for comment in user.comments:
                        comment.user_id = 3
                        delete_comment(comment.id)

                if user.replies:
                    for reply in user.replies:
                        reply.user_id = 3
                        delete_reply(reply.id)

                if user.likes:
                    for like in user.likes:
                        db.session.delete(like)
                        update_likes(-1)

                if user.bookmarks:
                    for bookmark in user.bookmarks:
                        db.session.delete(bookmark)
                        update_bookmarks(-1)

                if user.picture and (user.picture != "" or user.picture != "Picture_default.jpg"):
                    profile_picture_path = os.path.join(current_app.config["PROFILE_IMG_FOLDER"], user.picture)
                    if os.path.exists(profile_picture_path):
                        os.remove(profile_picture_path)

                db.session.delete(user)
                db.session.commit()

                flash("User deleted successfully.")
                update_stats_users_active(-1)

                return redirect(url_for('dashboard.manage_users'))

            except:
                db.session.rollback()
                flash("Error deleting user.")
    return render_template("dashboard/users_user_delete.html", logged_in=current_user.is_authenticated, user=user)

@dashboard.route("/dashboard/manage_users/block/<int:id>", methods=["GET", "POST"])
@login_required
def block_user(id):
    user = BlogUser.query.get_or_404(id)

    if request.method == "POST":
        if id == 1:
            flash("Authorization error: cannot block this user.")
        else:
            user.blocked = "TRUE"

            if user.comments:
                block_comments_replies(user.id, True)

            try:
                db.session.commit()
                flash("User blocked successfully.")
                return redirect(url_for('dashboard.manage_users'))
            except:
                db.session.rollback()
                flash("Error blocking user.")
    return render_template("dashboard/users_user_block.html", logged_in=current_user.is_authenticated, user=user)

@dashboard.route("/dashboard/manage_users/preview/<int:id>")
@login_required
def preview_user(id):
    user = BlogUser.query.get_or_404(id)
    return render_template("dashboard/users_user_preview.html", logged_in=current_user.is_authenticated, user=user)

# POST MANAGEMENT

@dashboard.route("/dashboard/submit_new_post", methods=["GET", "POST"])
@login_required
def submit_new_post():
    form = PostForm()

    if form.validate_on_submit():
        author_id = current_user.id

        post = BlogPost(
            theme_id=form.theme.data,
            date_to_post=form.date.data,
            title=form.title.data,
            intro=form.intro.data,
            body=form.body.data,
            picture_v_source=form.picture_v_source.data,
            picture_h_source=form.picture_h_source.data,
            picture_s_source=form.picture_s_source.data,
            picture_alt=form.picture_alt.data,
            meta_tag=form.meta_tag.data,
            title_tag=form.title_tag.data,
            author_id=author_id
        )

        try:
            db.session.add(post)
            db.session.commit()
            flash("Post submitted successfully!")
        except:
            db.session.rollback()
            flash("Error submitting post.")

        return redirect(url_for('account.dashboard'))

    return render_template("dashboard/posts_submit_new.html", logged_in=current_user.is_authenticated, form=form)

@dashboard.route("/dashboard/manage_posts")
@login_required
def manage_posts():
    posts = BlogPost.query.order_by(BlogPost.id).all()
    return render_template("dashboard/posts_table.html", logged_in=current_user.is_authenticated, posts=posts)

@dashboard.route("/dashboard/manage_posts/approve_post/<int:id>", methods=["GET", "POST"])
@login_required
def approve_post(id):
    post = BlogPost.query.get_or_404(id)

    if request.method == "POST":
        post.admin_approved = True

        try:
            db.session.commit()
            flash("Post approved successfully.")
            update_approved_post_stats(1)
            return redirect(url_for('dashboard.manage_posts'))
        except:
            db.session.rollback()
            flash("Error approving post.")

    return render_template("dashboard/posts_approve_post.html", logged_in=current_user.is_authenticated, post=post)

@dashboard.route("/dashboard/manage_posts/disallow_post/<int:id>", methods=["GET", "POST"])
@login_required
def disallow_post(id):
    post = BlogPost.query.get_or_404(id)

    if request.method == "POST":
        post.admin_approved = False

        try:
            db.session.commit()
            flash("Post disallowed successfully.")
            update_approved_post_stats(-1)
            return redirect(url_for('dashboard.manage_posts'))
        except:
            db.session.rollback()
            flash("Error disallowing post.")

    return render_template("dashboard/posts_disallow_post.html", logged_in=current_user.is_authenticated, post=post)

@dashboard.route("/dashboard/manage_posts_author")
@login_required
def manage_posts_author():
    posts = BlogPost.query.filter_by(author_id=current_user.id).all()
    return render_template("dashboard/posts_table_author.html", logged_in=current_user.is_authenticated, posts=posts)

@dashboard.route("/dashboard/manage_posts_author/preview_post/<int:id>")
@login_required
def preview_post_author(id):
    post = BlogPost.query.get_or_404(id)
    return render_template("dashboard/posts_preview_post.html", logged_in=current_user.is_authenticated, post=post)

@dashboard.route("/dashboard/manage_posts_author/edit_post/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post_author(id):
    post = BlogPost.query.get_or_404(id)
    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.theme_id = form.theme.data
        post.date_to_post = form.date.data
        post.title = form.title.data
        post.intro = form.intro.data
        post.body = form.body.data
        post.picture_v_source = form.picture_v_source.data
        post.picture_h_source = form.picture_h_source.data
        post.picture_s_source = form.picture_s_source.data
        post.picture_alt = form.picture_alt.data
        post.meta_tag = form.meta_tag.data
        post.title_tag = form.title_tag.data

        try:
            db.session.commit()
            flash("Post updated successfully.")
            return redirect(url_for('dashboard.manage_posts_author'))
        except:
            db.session.rollback()
            flash("Error updating post.")

    return render_template("dashboard/posts_edit_post_author.html", logged_in=current_user.is_authenticated, form=form, post=post)

@dashboard.route("/dashboard/manage_posts_author/delete_post/<int:id>", methods=["GET", "POST"])
@login_required
def delete_post_author(id):
    post = BlogPost.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(post)
            db.session.commit()
            flash("Post deleted successfully.")
            return redirect(url_for('dashboard.manage_posts_author'))
        except:
            db.session.rollback()
            flash("Error deleting post.")

    return render_template("dashboard/posts_delete_post_author.html", logged_in=current_user.is_authenticated, post=post)

# THEME MANAGEMENT

@dashboard.route("/dashboard/manage_themes")
@login_required
def manage_themes():
    themes = BlogTheme.query.order_by(BlogTheme.id).all()
    return render_template("dashboard/themes_table.html", logged_in=current_user.is_authenticated, themes=themes)

@dashboard.route("/dashboard/manage_themes/add_theme", methods=["GET", "POST"])
@login_required
def add_theme():
    if request.method == "POST":
        theme_name = request.form.get("theme_name")

        if BlogTheme.query.filter_by(name=theme_name).first():
            flash("This theme already exists.")
        else:
            theme = BlogTheme(name=theme_name)
            try:
                db.session.add(theme)
                db.session.commit()
                flash("Theme added successfully.")
                return redirect(url_for('dashboard.manage_themes'))
            except:
                db.session.rollback()
                flash("Error adding theme.")

    return render_template("dashboard/themes_add_theme.html", logged_in=current_user.is_authenticated)

@dashboard.route("/dashboard/manage_themes/delete_theme/<int:id>", methods=["GET", "POST"])
@login_required
def delete_theme(id):
    theme = BlogTheme.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(theme)
            db.session.commit()
            flash("Theme deleted successfully.")
            return redirect(url_for('dashboard.manage_themes'))
        except:
            db.session.rollback()
            flash("Error deleting theme.")

    return render_template("dashboard/themes_delete_theme.html", logged_in=current_user.is_authenticated, theme=theme)

# LIKE AND BOOKMARK MANAGEMENT

@dashboard.route("/dashboard/manage_likes")
@login_required
def manage_likes():
    likes = BlogLike.query.order_by(BlogLike.id).all()
    return render_template("dashboard/likes_table.html", logged_in=current_user.is_authenticated, likes=likes)

@dashboard.route("/dashboard/manage_likes/delete_like/<int:id>", methods=["GET", "POST"])
@login_required
def delete_like(id):
    like = BlogLike.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(like)
            update_likes(-1)
            db.session.commit()
            flash("Like deleted successfully.")
            return redirect(url_for('dashboard.manage_likes'))
        except:
            db.session.rollback()
            flash("Error deleting like.")

    return render_template("dashboard/likes_delete_like.html", logged_in=current_user.is_authenticated, like=like)

@dashboard.route("/dashboard/manage_bookmarks")
@login_required
def manage_bookmarks():
    bookmarks = BlogBookmark.query.order_by(BlogBookmark.id).all()
    return render_template("dashboard/bookmarks_table.html", logged_in=current_user.is_authenticated, bookmarks=bookmarks)

@dashboard.route("/dashboard/manage_bookmarks/delete_bookmark/<int:id>", methods=["GET", "POST"])
@login_required
def delete_bookmark(id):
    bookmark = BlogBookmark.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(bookmark)
            update_bookmarks(-1)
            db.session.commit()
            flash("Bookmark deleted successfully.")
            return redirect(url_for('dashboard.manage_bookmarks'))
        except:
            db.session.rollback()
            flash("Error deleting bookmark.")

    return render_template("dashboard/bookmarks_delete_bookmark.html", logged_in=current_user.is_authenticated, bookmark=bookmark)

# COMMENT AND REPLY MANAGEMENT

@dashboard.route("/dashboard/manage_comments")
@login_required
def manage_comments():
    comments = BlogComment.query.order_by(BlogComment.id).all()
    return render_template("dashboard/comments_table.html", logged_in=current_user.is_authenticated, comments=comments)

@dashboard.route("/dashboard/manage_comments/delete_comment/<int:id>", methods=["GET", "POST"])
@login_required
def delete_comment(id):
    comment = BlogComment.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(comment)
            db.session.commit()
            flash("Comment deleted successfully.")
            return redirect(url_for('dashboard.manage_comments'))
        except:
            db.session.rollback()
            flash("Error deleting comment.")

    return render_template("dashboard/comments_delete_comment.html", logged_in=current_user.is_authenticated, comment=comment)

@dashboard.route("/dashboard/manage_replies")
@login_required
def manage_replies():
    replies = BlogReply.query.order_by(BlogReply.id).all()
    return render_template("dashboard/replies_table.html", logged_in=current_user.is_authenticated, replies=replies)

@dashboard.route("/dashboard/manage_replies/delete_reply/<int:id>", methods=["GET", "POST"])
@login_required
def delete_reply(id):
    reply = BlogReply.query.get_or_404(id)

    if request.method == "POST":
        try:
            db.session.delete(reply)
            db.session.commit()
            flash("Reply deleted successfully.")
            return redirect(url_for('dashboard.manage_replies'))
        except:
            db.session.rollback()
            flash("Error deleting reply.")

    return render_template("dashboard/replies_delete_reply.html", logged_in=current_user.is_authenticated, reply=reply)

# IMAGE MANAGEMENT

@dashboard.route("/dashboard/manage_images")
@login_required
def manage_images():
    pictures = os.listdir(current_app.config["PROFILE_IMG_FOLDER"])
    return render_template("dashboard/images_table.html", logged_in=current_user.is_authenticated, pictures=pictures)

@dashboard.route("/dashboard/manage_images/delete_image/<string:filename>", methods=["GET", "POST"])
@login_required
def delete_image(filename):
    if request.method == "POST":
        if filename != "Picture_default.jpg":
            try:
                delete_blog_img(filename)
                flash("Image deleted successfully.")
                return redirect(url_for('dashboard.manage_images'))
            except:
                flash("Error deleting image.")
        else:
            flash("Cannot delete default image.")

    return render_template("dashboard/images_delete_image.html", logged_in=current_user.is_authenticated, filename=filename)

# STATISTICS MANAGEMENT

@dashboard.route("/dashboard/manage_stats")
@login_required
def manage_stats():
    users_count = BlogUser.query.count()
    posts_count = BlogPost.query.count()
    likes_count = BlogLike.query.count()
    bookmarks_count = BlogBookmark.query.count()
    comments_count = BlogComment.query.count()
    replies_count = BlogReply.query.count()

    return render_template("dashboard/stats_table.html", logged_in=current_user.is_authenticated, users_count=users_count, posts_count=posts_count, likes_count=likes_count, bookmarks_count=bookmarks_count, comments_count=comments_count, replies_count=replies_count)
