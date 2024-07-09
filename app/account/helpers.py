from flask import current_app
from werkzeug.security import generate_password_hash  # Used in signup

# Helper function to hash and salt passwords
def hash_password(password):
    """
    Hashes and salts the given password using PBKDF2 algorithm with SHA256.

    Args:
        password (str): The password to be hashed and salted.

    Returns:
        str: The hashed and salted password.
    """
    return generate_password_hash(
        password,
        method="pbkdf2:sha256",
        salt_length=8
    )
