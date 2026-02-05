from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- DB SETUP ----------
with db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        status INTEGER DEFAULT 0
    )
    """)

# -------- TODO LIST ----------
@app.route("/todo", methods=["GET", "POST"])
def todo():
    conn = db()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO todos (task) VALUES (?)",
            (request.form["task"],)
        )
        conn.commit()

    tasks = conn.execute("SELECT * FROM todos").fetchall()
    return render_template("todo.html", tasks=tasks)


@app.route("/todo/done/<int:id>")
def todo_done(id):
    conn = db()
    conn.execute("UPDATE todos SET status=1 WHERE id=?", (id,))
    conn.commit()
    return redirect("/todo")


@app.route("/todo/delete/<int:id>")
def todo_delete(id):
    conn = db()
    conn.execute("DELETE FROM todos WHERE id=?", (id,))
    conn.commit()
    return redirect("/todo")
@app.route("/")
def index():
    conn = db()
    expenses = conn.execute("SELECT * FROM expenses").fetchall()

    total = sum(e["amount"] for e in expenses)

    summary = {}
    for e in expenses:
        summary[e["category"]] = summary.get(e["category"], 0) + e["amount"]

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        summary=summary
    )

# ---------- DASHBOARD ----------
@app.route("/")
def dashboard():
    month = request.args.get("month")
    category = request.args.get("category")

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if month:
        query += " AND strftime('%Y-%m', date)=?"
        params.append(month)

    if category:
        query += " AND category=?"
        params.append(category)

    expenses = db().execute(query, params).fetchall()
    total = sum(e["amount"] for e in expenses)

    summary = {}
    for e in expenses:
        summary[e["category"]] = summary.get(e["category"], 0) + e["amount"]

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        summary=summary
    )

# ---------- ADD ----------
@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        conn = db()
        conn.execute(
            "INSERT INTO expenses (title, amount, category, date) VALUES (?,?,?,?)",
            (
                request.form["title"],
                float(request.form["amount"]),
                request.form["category"],
                request.form["date"] or datetime.now().strftime("%Y-%m-%d")
            )
        )
        conn.commit()   
        conn.close()
        return redirect("/")

    return render_template("add_expense.html")


# ---------- EDIT ----------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    conn = db()

    if request.method == "POST":
        conn.execute("""
            UPDATE expenses
            SET title=?, amount=?, category=?, date=?
            WHERE id=?
        """, (
            request.form["title"],
            request.form["amount"],
            request.form["category"],
            request.form["date"],
            id
        ))
        conn.commit()
        return redirect("/")

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=?", (id,)
    ).fetchone()

    return render_template("edit_expense.html", expense=expense)

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete_expense(id):
    conn = db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
