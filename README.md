# Flask_Connect_Blog
# Flask Blog Project

Welcome to the Flask Blog Project, a blogging platform built using Flask, SQLAlchemy, and Bootstrap. This platform allows users to create, view, and interact with blog posts. It includes features such as user authentication, posting comments, liking posts, and bookmarking favorite posts.


## Features

- **User Authentication:** Users can sign up, log in, and log out securely.
- **Create and View Posts:** Users can create new posts and view posts created by others.
- **Comments and Replies:** Users can comment on posts and reply to comments.
- **Likes and Bookmarks:** Users can like posts and bookmark their favorite posts.
- **Admin Panel:** Admins have access to manage posts, users, and site statistics.
- **Contact Form:** Users can send messages via a contact form.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/flask-blog.git
   cd flask-blog
2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
3. **Set up the database:**

   Create a PostgreSQL database (or adjust database settings in `config.py`).

   Run the following command to set up the database tables and initial data:

   ```bash
   python create_db.py

4. **Run the application:**

   ```bash
   python app.py

    
The application will be accessible at http://localhost:5000.

**Usage**
-   Navigate to http://localhost:5000 in your web browser.
-   Register a new account or log in with existing credentials.
-   Explore different blog posts, comment on them, like them, and bookmark your favorites.
-   Admins can access the admin panel at /admin to manage posts, users, and site statistics.

**Technologies Used**
**Flask:** Python web framework for building the application.
**SQLAlchemy:** Python SQL toolkit and Object-Relational Mapping (ORM) library.
**HTML/CSS:** Front-end styling and structure.
**JavaScript:** Client-side interactivity, AJAX requests.
**Bootstrap:** Front-end component library for responsive design.
