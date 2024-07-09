from app.general_helpers.helpers import check_image_filename
from werkzeug.utils import secure_filename
from flask import current_app
import os

def check_blog_picture(post_id, filename, db_column):
    """
    Verify if the uploaded blog post picture has a valid file extension and generate a new filename.
    
    Args:
        post_id (int): The ID of the blog post.
        filename (str): The original filename of the picture.
        db_column (str): The database column where the picture should be added ("v", "h", or "s").
        
    Returns:
        str or False: The new filename if valid, False otherwise.
    """
    if db_column == "v" or db_column == "h" or db_column == "s":
        if not isinstance(post_id, int):
            return False
        if not check_image_filename(filename):
            return False
        
        post_id_str = str(post_id)
        extension = filename.rsplit(".", 1)[1]
        pic_new_name = f"Picture_{db_column}_{post_id_str}.{extension}"
        return pic_new_name
    else:
        return False

def delete_blog_img(img):
    """
    Delete a blog post image from the designated folder.

    Args:
        img (str): The filename of the image to be deleted.
        
    Raises:
        NameError: If the image cannot be deleted.
    """
    if img and os.path.exists(os.path.join(current_app.config["BLOG_IMG_FOLDER"], img)):
        try:
            os.remove(os.path.join(current_app.config["BLOG_IMG_FOLDER"], img))
        except Exception as e:
            raise NameError("Blog post image could not be deleted.") from e
