from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "library123"


def connect():

    con = sqlite3.connect("library.db")
    con.row_factory = sqlite3.Row

    return con



def create_table():

    con = connect()

    # Students table
    con.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Books table
    con.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT,
            author TEXT,
            category TEXT,
            quantity INTEGER
        )
    """)

    con.commit()
    con.close()


def add_sample_books():

    con = connect()

    books = [
        ("Python Programming", "Mark Lutz", "Computer Science", 5),
        ("Let Us C", "Yashavant Kanetkar", "Computer Science", 4),
        ("Harry Potter", "J.K. Rowling", "Fiction", 6),
        ("Wings of Fire", "A.P.J. Abdul Kalam", "Biography", 5),
        ("The Alchemist", "Paulo Coelho", "Literature", 3),
        ("A Brief History of Time", "Stephen Hawking", "Science", 4),
        ("Rich Dad Poor Dad", "Robert Kiyosaki", "Self Development", 5),
        ("The Discovery of India", "Jawaharlal Nehru", "History", 3)
    ]

    count = con.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    # Add books only if table is empty
    if count == 0:

        con.executemany("""
            INSERT INTO books
            (book_name, author, category, quantity)
            VALUES (?, ?, ?, ?)
        """, books)

    con.commit()
    con.close()


# Create tables and sample books
create_table()
add_sample_books()


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # Admin login
        if role == "admin":

            if username == "admin" and password == "admin123":

                session["role"] = "admin"
                session["name"] = "Admin"

                return redirect("/dashboard")

            return "Wrong Admin Username or Password! <a href='/'>Try Again</a>"

        # Student login
        elif role == "student":

            con = connect()

            student = con.execute(
                "SELECT * FROM students WHERE username=?",
                (username,)
            ).fetchone()

            con.close()

            if student and check_password_hash(student["password"], password):

                session["role"] = "student"
                session["name"] = student["name"]

                return redirect("/dashboard")

            return "Wrong Student Username or Password! <a href='/'>Try Again</a>"

    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")

        con = connect()

        try:

            con.execute(
                "INSERT INTO students (name, username, password) VALUES (?, ?, ?)",
                (name, username, generate_password_hash(password))
            )

            con.commit()
            con.close()

            return redirect("/")

        except sqlite3.IntegrityError:

            con.close()

            return "Username already exists! <a href='/register'>Try Again</a>"

    return render_template("register.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():

    if "role" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        name=session["name"],
        role=session["role"]
    )


@app.route("/students", methods=["GET"])
def students():

    if session.get("role") != "admin":
        return redirect("/")

    con = connect()

    data = con.execute(
        "SELECT id, name, username FROM students"
    ).fetchall()

    con.close()

    return render_template(
        "students.html",
        students=data
    )


@app.route("/book", methods=["GET"])
def book():

    if "role" not in session:
        return redirect("/")

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    con = connect()

    if search:

        data = con.execute("""
            SELECT * FROM books
            WHERE book_name LIKE ? OR author LIKE ?
        """, ('%' + search + '%', '%' + search + '%')).fetchall()

    elif category:

        data = con.execute("""
            SELECT * FROM books
            WHERE category = ?
        """, (category,)).fetchall()

    else:

        data = con.execute(
            "SELECT * FROM books"
        ).fetchall()

    con.close()

    return render_template(
        "book.html",
        books=data,
        search=search,
        selected_category=category
    )



@app.route("/add_book", methods=["POST"])
def add_book():

    if session.get("role") != "admin":
        return redirect("/")

    book_name = request.form.get("book_name", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    quantity = request.form.get("quantity", "").strip()

    if not book_name or not author or not category or not quantity:
        return "Please fill all book details! <a href='/book'>Go Back</a>"

    try:
        quantity = int(quantity)

        if quantity < 0:
            return "Quantity cannot be negative! <a href='/book'>Go Back</a>"

    except ValueError:
        return "Enter a valid quantity! <a href='/book'>Go Back</a>"

    con = connect()

    con.execute("""
        INSERT INTO books
        (book_name, author, category, quantity)
        VALUES (?, ?, ?, ?)
    """, (book_name, author, category, quantity))

    con.commit()
    con.close()

    return redirect("/book")

@app.route("/logout", methods=["GET"])
def logout():

    session.clear()

    return redirect("/")

if __name__ == "__main__":

    app.run(debug=True, port=5050)
