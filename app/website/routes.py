from flask import Blueprint, render_template, request, jsonify, make_response
from app.extensions import db
from app.website.contact import send_email
from app.models.contact import Blog_Contact
from app.models.themes import Blog_Theme
from app.models.posts import Blog_Posts
from app.models.user import Blog_User
from app.models.likes import Blog_Likes
from app.models.bookmarks import Blog_Bookmarks
from app.models.comments import Blog_Comments, Blog_Replies
from app.models.helpers import update_likes, update_bookmarks, delete_comment, delete_reply
from flask_login import current_user
from datetime import datetime
from sqlalchemy import desc

website = Blueprint('website', __name__, static_folder="../static", template_folder="../template")

@website.route("/")
def home():
    posts_themes = [(theme.theme, theme.picture, theme.id) for theme in db.session.query(Blog_Theme).all()]
    theme_ids = [theme[2] for theme in posts_themes]
    
    posts_all = []
    forth_theme_post_ids = []
    for theme_id in theme_ids:
        query = db.session.query(Blog_Posts).filter(
            Blog_Posts.admin_approved == "TRUE",
            Blog_Posts.date_to_post <= datetime.utcnow(),
            Blog_Posts.theme_id == theme_id
        ).order_by(desc(Blog_Posts.date_to_post)).limit(3)
        posts_all.append(query.all())
        if theme_id == 4:
            forth_theme_post_ids.extend([post.id for post in query])

    posts_all = sum(posts_all, [])

    return render_template('website/index.html', posts_all=posts_all, posts_themes=posts_themes,
                           logged_in=current_user.is_authenticated, forth_theme_post_ids=forth_theme_post_ids)

@website.route("/all/<int:index>")
def all(index):
    index = int(index)
    all_blog_posts = None
    chosen_theme = ""
    intros = []

    if index != 0:
        chosen_theme = db.session.query(Blog_Theme).filter_by(id=index).first().theme
        all_blog_posts = db.session.query(Blog_Posts).filter(
            Blog_Posts.theme_id == index,
            Blog_Posts.admin_approved == "TRUE",
            Blog_Posts.date_to_post <= datetime.utcnow()
        ).order_by(desc(Blog_Posts.date_to_post)).limit(25)
    else:
        all_blog_posts = db.session.query(Blog_Posts).filter(
            Blog_Posts.admin_approved == "TRUE",
            Blog_Posts.date_to_post <= datetime.utcnow()
        ).order_by(desc(Blog_Posts.date_to_post)).limit(25)

    intros = [post.intro[:300] + '...' if len(post.intro) > 300 else post.intro for post in all_blog_posts]

    return render_template('website/all_posts.html', all_blog_posts=all_blog_posts, chosen_theme=chosen_theme,
                           intros=intros, logged_in=current_user.is_authenticated)

@website.route("/about/")
def about():
    authors_all = db.session.query(Blog_User).filter(
        Blog_User.blocked == "FALSE", Blog_User.type == "author"
    ).order_by(desc(Blog_User.id)).limit(25)
    
    return render_template('website/about.html', authors_all=authors_all, logged_in=current_user.is_authenticated)

@website.route("/contact/", methods=['POST', 'GET'])
def contact():
    if request.method == "POST":
        contact_name = request.form['contact_name']
        contact_email = request.form['contact_email']
        contact_message = request.form['contact_message']
        
        new_contact = Blog_Contact(name=contact_name, email=contact_email, message=contact_message)
        
        try:
            db.session.add(new_contact)
            db.session.commit()
            
            send_email(contact_name, contact_email, contact_message)
            
            return render_template('website/contact.html', msg_sent=True, logged_in=current_user.is_authenticated)
        
        except Exception as e:
            return f"There was an error adding message to the database: {str(e)}"
    
    return render_template('website/contact.html', msg_sent=False, logged_in=current_user.is_authenticated)

@website.route("/post/<int:index>", methods=["GET", "POST"])
def blog_post(index):
    blog_post = db.session.query(Blog_Posts).filter(
        Blog_Posts.id == index,
        Blog_Posts.admin_approved == "TRUE",
        Blog_Posts.date_to_post <= datetime.utcnow()
    ).order_by(Blog_Posts.date_submitted.desc()).first()
    
    post_likes = db.session.query(Blog_Likes).filter(Blog_Likes.post_id == index).all()

    user_liked = False
    user_bookmarked = False

    if current_user.is_authenticated:
        like = db.session.query(Blog_Likes).filter(
            Blog_Likes.user_id == current_user.id,
            Blog_Likes.post_id == index
        ).first()
        
        bookmark = db.session.query(Blog_Bookmarks).filter(
            Blog_Bookmarks.user_id == current_user.id,
            Blog_Bookmarks.post_id == index
        ).first()
        
        if like:
            user_liked = True
        
        if bookmark:
            user_bookmarked = True

    comments = db.session.query(Blog_Comments).filter(
        Blog_Comments.post_id == index
    ).order_by(Blog_Comments.date_submitted.desc()).limit(25)

    replies = db.session.query(Blog_Replies).filter(
        Blog_Replies.post_id == index
    ).order_by(Blog_Replies.date_submitted.asc()).limit(100)

    return render_template('website/post.html', blog_posts=blog_post, logged_in=current_user.is_authenticated,
                           comments=comments, replies=replies, post_likes=post_likes, user_liked=user_liked,
                           user_bookmarked=user_bookmarked)

@website.route("/comment_post/<int:index>", methods=["POST"])
def post_comment(index):
    data = request.get_json()
    content_type = request.headers.get('Content-Type')
    
    if content_type == 'application/json':
        if 'comment' not in data and 'reply' not in data:
            return make_response(jsonify({"message": "Comment empty"}), 400)
        
        if 'reply' in data and 'commentId' in data:
            reply = Blog_Replies(
                text=data['reply'], post_id=index, user_id=current_user.id, comment_id=int(data['commentId']))
            db.session.add(reply)
            db.session.commit()
            
            return make_response(jsonify({"message": "Reply added"}), 200)
        
        elif 'comment' in data and 'reply' not in data:
            comment = Blog_Comments(
                text=data['comment'], post_id=index, user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            
            return make_response(jsonify({"message": "Comment added"}), 200)
        
        else:
            return make_response(jsonify({"message": "Must be either a comment or a reply"}), 400)
    
    else:
        return make_response(jsonify({"message": "Content type not supported"}), 412)

@website.route("/delete_comment_or_reply/<int:index>", methods=["POST"])
def post_delete_comment(index):
    data = request.get_json()
    content_type = request.headers.get('Content-Type')
    
    if content_type == 'application/json':
        if 'commentId' not in data and 'replyId' not in data:
            return make_response(jsonify({"message": "Nothing to delete"}), 400)
        
        if 'replyId' in data and 'commentId' not in data:
            res = delete_reply(int(data['replyId']))
            
            if res == "success":
                return make_response(jsonify({"message": "Successfully deleted"}), 200)
            else:
                return make_response(jsonify({"message": "Reply not found"}), 404)
        
        elif 'commentId' in data and 'replyId' not in data:
            res = delete_comment(int(data['commentId']))
            
            if res == "success":
                return make_response(jsonify({"message": "Successfully deleted"}), 200)
            else:
                return make_response(jsonify({"message": "Comment not found"}), 404)
        
        else:
            return make_response(jsonify({"message": "Must be either a commentId or a replyId"}), 400)
    
    else:
        return make_response(jsonify({"message": "Content type not supported"}), 412)

@website.route("/like_post/<int:index>", methods=["POST"])
def post_like(index):
    post = db.session.query(Blog_Posts).filter_by(id=index).first()

    if not post:
        return jsonify({"error": "Post does not exist"}, 400)

    post_likes = db.session.query(Blog_Likes).filter(
        Blog_Likes.post_id == index
    ).all()

    like = db.session.query(Blog_Likes).filter(
        Blog_Likes.user_id == current_user.id,
        Blog_Likes.post_id == index
    ).first()

    if like:
        db.session.delete(like)
        db.session.commit()
        update_likes(-1)
        has_liked = "false"
    else:
        like = Blog_Likes(user_id=current_user.id, post_id=index)
        db.session.add(like)
        db.session.commit()
        update_likes(1)
        has_liked = "true"

    return jsonify({"likes": len(post_likes), "user_liked": has_liked})

@website.route("/bookmark_post/<int:index>", methods=["POST"])
def post_bookmark(index):
    post = db.session.query(Blog_Posts).filter_by(id=index).first()

    if not post:
        return jsonify({"error": "Post does not exist"}, 400)

    bookmark = db.session.query(Blog_Bookmarks).filter(
        Blog_Bookmarks.user_id == current_user.id,
        Blog_Bookmarks.post_id == index
    ).first()

    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        update_bookmarks(-1)
        has_bookmarked = "false"
    else:
        bookmark = Blog_Bookmarks(user_id=current_user.id, post_id=index)
        db.session.add(bookmark)
        db.session.commit()
        update_bookmarks(1)
        has_bookmarked = "true"

    return jsonify({"user_bookmarked": has_bookmarked})

