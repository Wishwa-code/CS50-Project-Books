import os
import requests


from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/users")
def users():
    """Lists all users."""
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("users.html", users=users)

@app.route("/register")
def index():
    return render_template("register.html",users=users)

@app.route("/register", methods=["POST"])
def register():
    """register"""

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")

    db.execute("INSERT INTO users (username, password, firstname, lastname, email) VALUES (:username, :password, :firstname, :lastname, :email)",
            {"username": username, "password": password, "firstname": firstname, "lastname": lastname, "email": email})
    db.commit()
    return render_template("success.html")


    
@app.route("/logincheck", methods=["POST"])
def logincheck():
    """login"""

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")

    user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

    if user is None:
        return render_template("error.html", message="No such flight.")

    if password == user.password :
        session["user.id"] =user.id
        return render_template("logsuccess.html",sessionid=session["user.id"] ,user=user)
    else:
        return render_template("incorrectpass.html",user=user)

@app.route("/search", methods=["POST","GET"])
def search():
    """search"""
    isbn_number = ''
    title = ''
    author = ''

    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()

    if request.method != "POST":
        return render_template("search.html")
    
    # Get form information.
    isbn_number = request.form.get("isbn_number")
    title = request.form.get("title")
    author = request.form.get("author")

    if title == '' and isbn_number == '':
        books = db.execute("SELECT * FROM books WHERE author LIKE ('%' || :author || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()

    elif isbn_number =='' and author == '':
        books = db.execute("SELECT * FROM books WHERE title LIKE ('%' || :title || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()

    elif title == '' and author == '':
        books = db.execute("SELECT * FROM books WHERE isbn_no LIKE ('%' || :isbn_number || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()

    elif title == '':
        books = db.execute("SELECT * FROM books WHERE isbn_no LIKE ('%' || :isbn_number || '%' ) AND author LIKE ('%' || :author || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()

    elif author == '':
        books = db.execute("SELECT * FROM books WHERE isbn_no LIKE ('%' || :isbn_number || '%' ) AND title LIKE ('%' || :title || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()

    elif isbn_number == '':
        books = db.execute("SELECT * FROM books WHERE author LIKE ('%' || :author || '%' ) AND title LIKE ('%' || :title || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()
    elif title == '' and isbn_number == '' and author == '' :
        books = None
    else:
        books = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_number OR title LIKE ('%' || :title || '%' ) OR author LIKE ('%' || :author || '%' ) ", {"isbn_number": isbn_number, "title": title, "author": author }).fetchall()


    if books == []:
        return render_template("error.html", message="No such book record.", user=user)
    else:
        return render_template("books.html",books=books,user=user)

@app.route("/search/<isbn_no>")
def book(isbn_no):
    """Lists details about a single book."""

    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()

    key = 'x8GUqn9Zog0RFNkgQVd9sw'

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()

    reviews = db.execute("SELECT * FROM reviews WHERE isbn_no = :isbn_number ", {"isbn_number": isbn_no}).fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn_no})

    data = res.json()

    gdrate = data["books"][0]["average_rating"]
    gdratecount = data["books"][0]["work_ratings_count"]


    if book is None:
        return render_template("error.html", message="No such book.", user=user)
    else:
        return render_template("book.html", book=book, reviews=reviews, sessionid=session["user.id"], gdrate=gdrate, gdratecount=gdratecount, user=user)

@app.route("/enterrev/<isbn_no>")
def enterrev(isbn_no):
    """enterreview"""

    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()
    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()

    if book == [] :
        return render_template("error.html", message="No such book.", user=user)
    else:
        return render_template("addreview.html", user=user, book=book)

@app.route("/showrev/<isbn_no>")
def showrev(isbn_no):
    """enterreview"""
    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()
    
    reviews = db.execute("SELECT * FROM reviews WHERE isbn_no = :isbn_number ", {"isbn_number": isbn_no}).fetchall()
    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()

    return render_template("showreviews.html", user=user, book=book,reviews=reviews)

@app.route("/addreview/<isbn_no>", methods=["POST","GET"])
def addreview(isbn_no):
    """Add a Review."""

    # Get form information.
    rate = request.form.get("rate")
    review = request.form.get("review")
    user_id = session["user.id"]


    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()
    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()

    # Make sure book exists.
    if db.execute("SELECT * FROM reviews WHERE id = :id AND isbn_no = :isbn_no ", {"id": user_id, "isbn_no": isbn_no} ).rowcount == 1:
        return render_template("error.html", message="you can add only one review for one book")

    db.execute("INSERT INTO reviews (rate, review, isbn_no, id) VALUES (:rate, :review, :isbn_no, :id)",
            {"rate": rate, "review": review, "isbn_no": isbn_no, "id": user_id})
    db.commit()

    return render_template("revsuccess.html", user=user, book=book)

@app.route("/logout")
def logout():
    """logout"""
    user_id = session["user.id"]
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": user_id}).fetchone()

    session["user.id"] = ''

    if session["user.id"] == '' :
        return render_template("logout.html",user=user)

@app.route("/api/<isbn_no>")
def api(isbn_no):
    """Returning a details about a single book"""


    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()
    
    key = 'x8GUqn9Zog0RFNkgQVd9sw'

    book = db.execute("SELECT * FROM books WHERE isbn_no = :isbn_no", {"isbn_no": isbn_no}).fetchone()

    reviews = db.execute("SELECT * FROM reviews WHERE isbn_no = :isbn_number ", {"isbn_number": isbn_no}).fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn_no})

    data = res.json()

    gdrate = data["books"][0]["average_rating"]
    gdratecount = data["books"][0]["work_ratings_count"]
    
    if book is None:
        return jsonify({"error": "Invalid flight_id"}), 422   

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.pub_year,
            "isbn": book.isbn_no,
            "review_count": gdrate,
            "average_score": gdratecount
        }) 


