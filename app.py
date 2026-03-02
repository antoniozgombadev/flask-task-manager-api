from flask import Flask, render_template, request, redirect
from flask import jsonify
import sqlite3
from database import init_db
import os
app = Flask(__name__)

DB_NAME = os.path.join(os.path.dirname(__file__), "tasks.db")

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, done FROM tasks")
    tasks = cursor.fetchall()

    conn.close()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form["title"]
    if not title or title.strip() == "":
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (title, 0)
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/done/<int:task_id>")
def mark_done(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET done = 1 WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        new_title = request.form["title"]

        cursor.execute(
            "UPDATE tasks SET title = ? WHERE id = ?",
            (new_title, task_id)
        )

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute(
        "SELECT id, title FROM tasks WHERE id = ?",
        (task_id,)
    )

    task = cursor.fetchone()
    print("TASK:", task)
    conn.close()

    return render_template("edit.html", task=task)

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, done FROM tasks")
    tasks = cursor.fetchall()

    conn.close()

    tasks_list = []
    for task in tasks:
        tasks_list.append({
            "id": task[0],
            "title": task[1],
            "done": bool(task[2])
        })

    return jsonify(tasks_list)

@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (data["title"], 0)
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": new_id,
        "title": data["title"],
        "done": False
    }), 201

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Task deleted"})

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_update_task(task_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    title = data.get("title")
    done = data.get("done")

    if title is None and done is None:
        conn.close()
        return jsonify({"error": "Nothing to update"}), 400

    if title is not None:
        cursor.execute(
            "UPDATE tasks SET title = ? WHERE id = ?",
            (title, task_id)
        )

    if done is not None:
        cursor.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(done), task_id)
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Task updated"})

init_db()

if __name__ == "__main__":
    app.run()