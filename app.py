from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import math
from flask import request
from werkzeug.routing import BuildError


app = Flask(__name__)

# Route for the admin dashboard
@app.route('/')
def admin():
    return render_template('admin.html')

# Routes for other sub-items (example)
@app.route('/dashboard/content')
def content_dashboard():
    return render_template('content_dashboard.html')

# Similar routes for other sub-items...

def get_tasks(page, per_page=10):
    conn = sqlite3.connect('LMS.db')
    cursor = conn.cursor()
    offset = (page - 1) * per_page
    cursor.execute("SELECT * FROM tasks LIMIT ? OFFSET ?", (per_page, offset))
    tasks = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    conn.close()
    return tasks, total_tasks

@app.route('/task/view_tasks')
def view_tasks():
    page = request.args.get('page', 1, type=int)
    tasks, total_tasks = get_tasks(page)
    total_pages = math.ceil(total_tasks / 10)
    return render_template('view_tasks.html', tasks=tasks, page=page, total_pages=total_pages)

@app.route('/task/create_new_task')
def create_new_task():
    conn = sqlite3.connect('LMS.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userEmail FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('create_new_task.html', users=users)

@app.route('/task/submit_new_task', methods=['POST'])
def submit_new_task():
    task_area = request.form.get('taskArea')
    task_deadline = request.form.get('taskDeadline')
    task_title = request.form.get('taskTitle')
    task_requirement = request.form.get('taskRequirement')
    creator_email = request.form.get('creatorEmail')
    assignee_email = request.form.get('assigneeEmail') or None

    # Connect to the database and insert the new task
    conn = sqlite3.connect('LMS.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (taskArea, taskDeadline, taskTitle, taskRequirement, 
                           creatorEmail, assigneeEmail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (task_area, task_deadline, task_title, task_requirement,
          creator_email, assignee_email))
    conn.commit()
    conn.close()

    # Redirect to the view_tasks page or display a success message
    return redirect(url_for('view_tasks'))



@app.route('/task/edit/<int:task_id>')
def edit_task(task_id):
    conn = sqlite3.connect('LMS.db')
    conn.row_factory = sqlite3.Row  # to access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE taskId = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    return render_template('edit_task.html', task=task)


@app.route('/task/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    # Retrieve form data
    # task_area = request.form.get('taskArea')
    task_deadline = request.form.get('taskDeadline')
    task_title = request.form.get('taskTitle')
    task_requirement = request.form.get('taskRequirement')
    # is_deleted = True if request.form.get('isDeleted') == 'on' else False
    # creator_email = request.form.get('creatorEmail')
    # assignee_email = request.form.get('assigneeEmail') or None

    # Update the task in the database
    conn = sqlite3.connect('LMS.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks SET
        taskDeadline = ?,
        taskTitle = ?,
        taskRequirement = ?
        WHERE taskId = ?
    ''', (task_deadline, task_title, task_requirement, task_id))

    conn.commit()
    conn.close()

    # Redirect to the view_tasks page or another appropriate page
    return redirect(url_for('view_tasks'))# Retrieve form data
    # Example: task_title = request.form.get('taskTitle')
    # Update the task in the database
    # Redirect to view_tasks or display a success message
    # ...
    return 0




@app.route('/course/create_new_course', methods=['GET', 'POST'])
def create_new_course():
    if request.method == 'POST':
        title = request.form['courseTitle']
        description = request.form['courseDescription']
        category = request.form['courseCategory']
        sub_category = request.form['courseSubCategory']

        new_course = Course(title=title, description=description, category=category, sub_category=sub_category)
        db.session.add(new_course)
        db.session.commit()

        return redirect(url_for('edit_course', course_id=new_course.id))

    return render_template('create_new_course.html')





# @app.errorhandler(404)
# def page_not_found(e):
#     # note that we set the 404 status explicitly
#     return render_template('404.html'), 404


# @app.route('/<path:anything>')
# def catch_all(anything):
#     return render_template('404.html')

# @app.errorhandler(BuildError)
# def handle_build_error(error):
#     # Render a custom HTML file for the error
#     return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
