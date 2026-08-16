from flask import Flask, render_template_string
import sqlite3
import os
import sys

# Ensure app.config works when running dashboard.py directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from app.config import DB_PATH

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YT Automation Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
        th { background-color: #eee; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .status { font-weight: bold; }
        .READY { color: green; }
        .FAILED { color: red; }
        .PUBLISHED { color: blue; }
    </style>
</head>
<body>
    <h1>YouTube Automation Dashboard</h1>
    <h2>Video Pipeline</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Created At</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row['id'] }}</td>
            <td>{{ row['title'] }}</td>
            <td class="status {{ row['status'] }}">{{ row['status'] }}</td>
            <td>{{ row['created_at'] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, rows=rows)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
