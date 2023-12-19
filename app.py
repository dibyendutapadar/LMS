from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import sqlite3
import math
from flask import request
from werkzeug.routing import BuildError
from werkzeug.utils import secure_filename

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from flask_ckeditor import CKEditor, CKEditorField




from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
import pandas as pd
import os
from datetime import datetime, timedelta
import json
import matplotlib
from io import BytesIO
matplotlib.use('Agg')  # Use a non-interactive backend
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from sqlalchemy.dialects.postgresql import JSON


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///LMS.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Folder where uploaded files will be stored
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

db = SQLAlchemy(app)
ckeditor = CKEditor(app)

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

Base = sqlalchemy.orm.declarative_base()
engine = create_engine('sqlite:///LMS.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)  # Modify to handle rich text with markdown
    category = db.Column(db.String(100), nullable=False)
    sub_category = db.Column(db.String(100), nullable=False)
    blocks = db.relationship('Block', backref='course', lazy=True)
    course_short_name = db.Column(db.Text)  # Existing field
    course_code = db.Column(db.Text)  # Existing field
    course_objective_title = db.Column(db.Text)  # Existing field
    course_objective_description = db.Column(db.Text)  # Existing field
    course_display_image = db.Column(db.String(255))  # Modified to store image path
    is_shelf_one = db.Column(db.Boolean, default=False)  # New field
    is_shelf_two = db.Column(db.Boolean, default=False)  # New field
    is_shelf_three = db.Column(db.Boolean, default=False)  # New field
    is_shelf_four = db.Column(db.Boolean, default=False)  # New field
    is_shelf_five = db.Column(db.Boolean, default=False)  # New field


class Block(db.Model):
    __tablename__ = 'block'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    parent_block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=True)
    
    # Set up a self-referential relationship
    # 'remote_side' is used to indicate this column is on the remote side of the relationship
    parent_block = db.relationship('Block', remote_side=[id],backref=backref('children', cascade='all, delete-orphan'))
    contents = db.relationship('Content', backref='block', lazy=True)
    block_objective_title = db.Column(db.Text)  # Existing field
    block_objective_description = db.Column(db.Text)  # Existing field

class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)  # Storing rich text in raw format
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=False)
    type = db.Column(db.Enum('Video', 'Text', 'PDF', 'PPT', name='content_types'), nullable=False)
    file_link = db.Column(db.String(255))  # Store file path
    videoLink = db.Column(db.String(255))
    mastery_score = db.Column(db.Integer, default=100, nullable=False)  # Integer between 0 and 100
    completion_threshold = db.Column(JSON)
    is_shourt_course = db.Column(db.Boolean, default=False)  # New field  # If using a relational database other than PostgreSQL, consider using a serialized string


class Category(db.Model):
    __tablename__='category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # Relationship with SubCategory
    subcategories = db.relationship('SubCategory', backref='category', lazy=True)

class SubCategory(db.Model):
    __tablename__='subCategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usertype = db.Column(db.Enum('Admin', 'Author', 'Learner', name='usertype_enum'), nullable=False)
    userName = db.Column(db.String(100), nullable=False, unique=True)
    userPassword = db.Column(db.String(100), nullable=False)

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    content_id = db.Column(db.PickleType, nullable=False)  # Storing list of content IDs
    status = db.Column(db.Enum('enrolled', 'inprogress', 'completed', name='status_enum'), default='enrolled', nullable=False)

    learner = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')


class LearnerActivity(db.Model):
    __tablename__ = 'learner_activity'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    activity = db.Column(db.Enum('initialized', 'terminated', 'marked_completed', name='activity_types'), nullable=False)
    status = db.Column(db.Enum('enrolled', 'inprogress', 'completed', name='status_types'), nullable=False)
    percentage_complete = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


@app.route('/course/create_new_course', methods=['GET', 'POST'])
def create_new_course():
    if request.method == 'POST':
        title = request.form['courseTitle']
        description = request.form['courseDescription']
        category = request.form['courseCategory']
        sub_category = request.form['courseSubCategory']
        course_short_name = request.form['course_short_name']
        course_code = request.form['course_code']
        course_objective_title = request.form['course_objective_title']
        course_objective_description = request.form['course_objective_description']
        is_shelf_one = 'is_shelf_one' in request.form
        is_shelf_two = 'is_shelf_two' in request.form
        is_shelf_three = 'is_shelf_three' in request.form
        is_shelf_four = 'is_shelf_four' in request.form
        is_shelf_five = 'is_shelf_five' in request.form

        print(is_shelf_one)

        file = request.files['course_display_image']

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            file_path = ''   

        new_course = Course(title=title, description=description, category=category, sub_category=sub_category,course_display_image=file_path,
        course_short_name=course_short_name,course_code=course_code,course_objective_title=course_objective_title,course_objective_description=course_objective_description,
        is_shelf_one=is_shelf_one,is_shelf_two=is_shelf_two,is_shelf_three=is_shelf_three,is_shelf_four=is_shelf_four,is_shelf_five=is_shelf_five)
        db.session.add(new_course)
        db.session.commit()
        print(f"Course '{title}' added successfully.")
        new_course_id = new_course.id
        
        return redirect(url_for('edit_course', course_id=new_course_id))

    categories_df = pd.read_csv('category_sub_category.csv')
    categories = categories_df['Categories'].unique().tolist()
    subcategories = categories_df.groupby('Categories')['Sub-Categories'].apply(list).to_dict()
    return render_template('create_new_course.html', categories=categories,subcategories=subcategories)  # This should render the template to create a new course

@app.route('/course/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        if 'blockTitle' in request.form:  # Adding a block
            block_title = request.form['blockTitle']
            parent_block_id = request.form.get('parentBlockId')  # This can be None for top-level blocks
            new_block = Block(title=block_title, course_id=course_id, parent_block_id=parent_block_id)
            db.session.add(new_block)
            
        elif 'contentTitle' in request.form:  # Adding content
            content_title = request.form['contentTitle']
            content_text = request.form['contentText']
            parent_block_id = request.form['parentBlockId']
            new_content = Content(title=content_title, text=content_text, block_id=parent_block_id)
            db.session.add(new_content)
        
        db.session.commit()

        return redirect(url_for('edit_course', course_id=course_id))

    return render_template('edit_course.html', course=course)  # Pass the course object to the template

    

@app.route('/course/view_courses')
def view_courses():
    courses = Course.query.all()
    return render_template('view_courses.html', courses=courses)

@app.route('/course/edit_course/add_block', methods=['POST'])
def add_block():
    course_id = request.form.get('course_id')
    block_title = request.form.get('block_title')
    
    # Assuming you have already set up your database session as `db`
    new_block = Block(title=block_title, course_id=course_id)
    db.session.add(new_block)
    db.session.commit()

    # Respond with JSON indicating success
    return {'success': True}

from flask import request, jsonify

@app.route('/course/edit_course/add_content', methods=['POST'])
def add_content():
    block_id = request.form.get('block_id')
    content_title = request.form.get('content_title')
    type = request.form.get('type')
    content_text = request.form.get('content_text')
    mastery_score = request.form.get('mastery_score')
    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    else:
        file_path = ''   

    # Input validation, error handling, and database interaction would go here
    try:
        # Assuming you have a function to create content
        new_content = Content(title=content_title, text=content_text, block_id=block_id,type=type,file_link=file_path,mastery_score=mastery_score)
        db.session.add(new_content)
        db.session.commit()
        return jsonify({'success': True, 'content_id': new_content.id})
    except Exception as e:
        # Log the exception e and return an error message
        print(e)
        return jsonify({'success': False, 'error': 'Failed to add content'}), 500

@app.route('/course/edit_course/get_block', methods=['GET'])
def get_block(blockId):
    block = Block.query.get(blockId)
    if block:
        return jsonify({
            'id': block.id,
            'title': block.title,
            # Include any other block details you need
        }), 200
    else:
        return jsonify({'error': 'Block not found'}), 404



@app.route('/course/edit_course/get_content/<int:contentId>', methods=['GET'])
def get_content(contentId):
    content = Content.query.get(contentId)
    if content:
        return jsonify({
            'id': content.id,
            'title': content.title,
            'text': content.text,
            'block_id': content.block_id,
            'type':content.type,
            'file_link':content.file_link,
            'mastery_score':content.mastery_score
            # Include any other content details you need
        }), 200
    else:
        return jsonify({'error': 'Content not found'}), 404







@app.route('/course/edit_course/update_content/', methods=['POST'])
def update_content():
    content_id = request.form.get('content_id')
    content_title = request.form.get('content_title')
    type = request.form.get('type')
    content_text = request.form.get('content_text')
    mastery_score = request.form.get('mastery_score')
    file = request.files['file']


    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    else:
        file_path = ''   

    content = Content.query.get(content_id)
    if content:
        content.title = content_title
        content.text = content_text
        content.type = type
        content.mastery_score = mastery_score
        content.file_link = file_path
        db.session.commit()
        return jsonify({'message': 'Content updated successfully'}), 200
    else:
        return jsonify({'message': 'Content not found'}), 404


@app.route('/course/edit_course/add_child_block', methods=['POST'])
def add_child_block():
    parent_block_id = request.form.get('parent_block_id')
    block_title = request.form.get('block_title')

    # Find the parent block
    parent_block = Block.query.get(parent_block_id)
    print(parent_block)
    # Create a new child block
    child_block = Block(title=block_title, course_id=parent_block.course_id, parent_block_id=parent_block_id)
    
    # Append the new child block to the parent block's children relationship
    parent_block.children.append(child_block)
    
    # Commit the changes to the database
    db.session.add(child_block)
    db.session.commit()

    # Respond with JSON indicating success and the ID of the new child block
    return {'success': True, 'child_block_id': child_block.id}

@app.route('/course/view_contents')
def view_content():
    contents = Content.query.all()
    return render_template('view_content.html', contents=contents)


@app.route('/course/content', methods=['GET', 'POST'])
def add_new_content():
    if request.method == 'POST':
        title = request.form['contentTitle']
        description = request.form['contentDescription']
        category = request.form['courseCategory']
        sub_category = request.form['courseSubCategory']

        new_course = Course(title=title, description=description, category=category, sub_category=sub_category)
        db.session.add(new_course)
        db.session.commit()
        print(f"Course '{title}' added successfully.")
        new_course_id = new_course.id
        
        return redirect(url_for('edit_course', course_id=new_course_id))

    return render_template('create_new_course.html')  # This should render the template to create a new course

@app.route('/learners/view_learners')
def view_learners():
    users = User.query.all()
    return render_template('view_learners.html', users=users)

@app.route('/learners/view_activities')
def view_activities():
    activities = LearnerActivity.query.all()
    return render_template('view_logs.html', activities=activities)


#------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------LEARNER SIDE-------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/learner/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Extract data from form
        usertype = request.form['usertype']
        userName = request.form['userName']
        userPassword = request.form['userPassword']

        # Create new User object
        new_user = User(usertype=usertype, userName=userName, userPassword=userPassword)

        # Add to database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('learner_login'))
    return render_template('signup.html')

@app.route('/learner/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userName = request.form['userName']
        userPassword = request.form['userPassword']

        # Validate user
        user = User.query.filter_by(userName=userName, userPassword=userPassword).first()
        if user:
            session['current_learner_id'] = user.id
            return redirect(url_for('learner_home'))
        else:
            return 'Invalid username or password'

    return redirect(url_for('learner_home'))

@app.route('/learner')
def learner_login():
    return render_template('login.html')

@app.route('/learner/home')
def learner_home():
    courses = Course.query.all()
    current_user_id = session.get('current_learner_id')
    enrolled_courses = Enrollment.query.filter_by(learner_id=current_user_id).all()
    enrolled_course_ids = [enrollment.course_id for enrollment in enrolled_courses]
    return render_template('learner_home.html', courses=courses, enrolled_course_ids=enrolled_course_ids)

@app.route('/course/<int:course_id>')
def course_page(course_id):
    course = Course.query.get_or_404(course_id)
    current_user_id = session.get('current_learner_id')  # Replace with your session management logic
    user_enrolled = Enrollment.query.filter_by(learner_id=current_user_id, course_id=course_id).first() is not None
    return render_template('course_page.html', course=course, user_enrolled=user_enrolled)


@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    current_user_id = session.get('current_learner_id')
    # Check if the user is already enrolled
    existing_enrollment = Enrollment.query.filter_by(learner_id=current_user_id, course_id=course_id).first()
    if existing_enrollment:
    # User is already enrolled, redirect to course page
        return redirect(url_for('course_page', course_id=course_id))

# Get all content IDs from the course
    content_ids = [content.id for content in Content.query.filter_by(block_id=Block.query.filter_by(course_id=course_id).first().id).all()]

# Create a new enrollment
    new_enrollment = Enrollment(
        learner_id=current_user_id,
        course_id=course_id,
        content_id=content_ids,
        status='enrolled'
    )

# Add to database
    db.session.add(new_enrollment)
    db.session.commit()

    return redirect(url_for('course_page', course_id=course_id))


@app.route('/course/<int:course_id>/resume')
def learn_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('learn_course.html', course=course)



def get_learner_activity_status(learner_id, content_id):
    # Query your LearnerActivity model
    activity = LearnerActivity.query.filter_by(
        learner_id=learner_id,
        content_id=content_id,
        status='completed'
    ).first()
    return 'completed' if activity else 'Not Completed'


@app.route('/course/learn_course/get_content/<int:content_id>')
def learn_get_content(content_id):
    current_learner_id = session.get('current_learner_id')
    # Assume get_content_details and get_learner_activity_status are defined appropriately
    content = Content.query.get(content_id)
    completion_status = get_learner_activity_status(current_learner_id, content_id)
   
    data = {
        'id': content.id,
        'title': content.title,
        'text': content.text,
        'block_id': content.block_id,
        'completed': completion_status == 'completed'
    }

    return jsonify(data)

@app.route('/log_activity', methods=['POST'])
def log_activity():
    data = request.json
    new_activity = LearnerActivity(
        learner_id=data['learner_id'],
        content_id=data['content_id'],
        activity=data['activity'],
        status=data['status'],
        percentage_complete=data['percentage_complete'],
        timestamp=datetime.utcnow()
    )
    db.session.add(new_activity)
    db.session.commit()
    return jsonify({"status": "success"}), 200

@app.route('/logout')
def logout():
    # Remove current_learner_id from session
    session.pop('current_learner_id', None)
    return redirect(url_for('learner_login'))




def create_bar_chart(data, labels, title, ylabel, xlabel):
    fig, ax = plt.subplots()
    bars = ax.barh(labels, data)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    

    for bar in bars:
        width = bar.get_width()
        label_x_pos = width + 1  # adjust this value to move the text left or right
        ax.text(label_x_pos, bar.get_y() + bar.get_height() / 2, f'{width}', va='center')
    
    plt.tight_layout()
    # Save the figure to a bytes buffer
    canvas = FigureCanvas(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    plt.close(fig)
    
    return buffer

 # Read data from the CSV file into a dataframe
df = pd.read_csv('learner_list.csv')
    # Convert 'date' column to datetime for easier filtering
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

@app.route('/course-time-chart')
def course_time_chart():
    data = df.groupby('courseId')['activeSeconds'].sum().sort_values(ascending=False).head(10)
    buffer = create_bar_chart(data.values, data.index, 'Course Time', 'Course ID', 'Learning Time')
    return send_file(buffer, mimetype='image/png')

@app.route('/course-learner-count-chart')
def course_learner_count_chart():
    data = df.groupby('courseId')['learnerId'].nunique().sort_values(ascending=False).head(10)
    buffer = create_bar_chart(data.values, data.index, 'Course Learner Count', 'Course ID', 'Registered Learners')
    return send_file(buffer, mimetype='image/png')

@app.route('/learner-time-chart')
def learner_time_chart():
    data = df.groupby('learnerId')['activeSeconds'].sum().sort_values(ascending=False).head(10)
    buffer = create_bar_chart(data.values, data.index, 'Learner Time', 'Learner ID', 'Learning Time')
    return send_file(buffer, mimetype='image/png')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Set default dates
    
   

    default_from_date = datetime(2023, 12, 1)
    default_to_date = datetime.now() - timedelta(days=1)
    
    # Get filter values from the request or set to default
    from_date = request.form.get('from_date', default_from_date.strftime('%Y-%m-%d'))
    to_date = request.form.get('to_date', default_to_date.strftime('%Y-%m-%d'))
    
    # Convert string dates to datetime
    from_date = pd.to_datetime(from_date)
    to_date = pd.to_datetime(to_date)
    
    # Apply date filter
    df_filtered = df[(df['date'] >= from_date) & (df['date'] <= to_date)]
    
    # KPI 1: Total Registered Learners
    total_learners = df['learnerId'].nunique()
    
    # KPI 2: Learners active this week and percentage increase
    this_week = df[(df['date'] >= to_date - timedelta(days=to_date.weekday())) & (df['date'] <= to_date)]
    last_week = df[(df['date'] >= to_date - timedelta(days=to_date.weekday() + 7)) & (df['date'] < to_date - timedelta(days=to_date.weekday()))]
    
    active_learners_this_week = this_week['learnerId'].nunique()
    active_learners_last_week = last_week['learnerId'].nunique()
    percent_increase_learners = ((active_learners_this_week - active_learners_last_week) / active_learners_last_week) * 100 if active_learners_last_week > 0 else 0
    
    # KPI 3: Total Learning hours this week and percentage increase
    learning_seconds_this_week = this_week['activeSeconds'].sum()
    learning_seconds_last_week = last_week['activeSeconds'].sum()
    percent_increase_hours = ((learning_seconds_this_week - learning_seconds_last_week) / learning_seconds_last_week) * 100 if learning_seconds_last_week > 0 else 0
    
    # Convert total learning seconds to hours
    total_learning_hours_this_week = learning_seconds_this_week / 3600
    


    formatted_from_date = from_date.strftime('%Y-%m-%d')
    formatted_to_date = to_date.strftime('%Y-%m-%d')

    # Render the HTML page with the chart data and KPIs
    return render_template('dashboard.html',
                           total_learners=total_learners,
                           active_learners_this_week=active_learners_this_week,
                           percent_increase_learners=percent_increase_learners,
                           total_learning_hours_this_week=total_learning_hours_this_week,
                           percent_increase_hours=percent_increase_hours,
                           formatted_from_date=formatted_from_date,
                           formatted_to_date=formatted_to_date)



















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
    app.run(debug=True, threaded=False)
