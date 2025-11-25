from datetime import datetime, date
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import os # NEW: Import os for environment variables

app = Flask(__name__)
# CRITICAL FIX: Load SECRET_KEY from environment for production safety
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_dev_key_5791628bb0b13ce0c676dfde280ba245')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillswap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- MODELS ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('MessComment', backref='comment_author', lazy=True) 
    post_comments = db.relationship('PostComment', backref='comment_author', lazy=True) 

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False, default='forum')
    price = db.Column(db.String(20), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class MessMenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    items = db.Column(db.String(200), nullable=False)
    
class MessVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('mess_menu.id'), nullable=False)
    vote = db.Column(db.Integer, nullable=False)

class MessComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('mess_comment.id'), nullable=True) 
    replies = db.relationship('MessComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')


class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) 
    
    parent_id = db.Column(db.Integer, db.ForeignKey('post_comment.id'), nullable=True) 
    
    replies = db.relationship('PostComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')


# --- AUTH ROUTES ---

@app.route("/")
@app.route("/home")
def home():
    if not current_user.is_authenticated:
        return render_template('landing.html', title='Welcome to SRU Forum')

    posts = Post.query.order_by(Post.date_posted.desc()).limit(6).all()
    return render_template('index.html', posts=posts, title='Latest Activity')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Registration failed. That username is already taken.', 'danger')
            return redirect(url_for('register')) 

        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Registration failed. That email address is already in use.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Check email and password', 'danger')
    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# Create DB
with app.app_context():
    db.create_all()

# --- POST ROUTES ---

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        price = request.form.get('price')
        post = Post(title=title, content=content, category=category, price=price, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        
        if category in ['market', 'lost']: return redirect(url_for('market'))
        elif category == 'skill': return redirect(url_for('skills'))
        else: return redirect(url_for('forum'))
        
    return render_template('create_post.html', title='New Post')

@app.route("/post/<int:post_id>")
@login_required
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    
    comments = PostComment.query.filter_by(post_id=post.id, parent_id=None).order_by(PostComment.date_posted.asc()).all()
    
    return render_template('post_detail.html', 
                           title=post.title, 
                           post=post, 
                           comments=comments,
                           PostComment=PostComment)


@app.route("/post/comment/<int:post_id>", methods=['POST'])
@login_required
def post_comment(post_id):
    body = request.form.get('comment')
    parent_id = request.form.get('parent_id', None) 
    
    if body:
        if parent_id and parent_id.isdigit():
            parent_id = int(parent_id)
        else:
            parent_id = None
            
        comment = PostComment(
            body=body, 
            user_id=current_user.id, 
            post_id=post_id,
            parent_id=parent_id
        ) 
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted!', 'success')
        
    return redirect(url_for('post_detail', post_id=post_id))

# --- FEED ROUTES ---

@app.route("/skills")
@login_required
def skills():
    posts = Post.query.filter_by(category='skill').order_by(Post.date_posted.desc()).all()
    return render_template('feed.html', posts=posts, title="SkillSwap 🤝", page_type="skill")

@app.route("/market")
@login_required
def market():
    posts = Post.query.filter(Post.category.in_(['market', 'lost'])).order_by(Post.date_posted.desc()).all()
    return render_template('feed.html', posts=posts, title="Marketplace 🛍️", page_type="market")

@app.route("/forum")
@login_required
def forum():
    posts = Post.query.filter_by(category='forum').order_by(Post.date_posted.desc()).all()
    return render_template('feed.html', posts=posts, title="Student Forum 💬", page_type="forum")

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('Permission Denied.', 'danger')
        return redirect(url_for('home'))
        
    category_for_redirect = post.category 
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'success')
    
    if category_for_redirect in ['market', 'lost']: return redirect(url_for('market'))
    elif category_for_redirect == 'skill': return redirect(url_for('skills'))
    else: return redirect(url_for('forum'))

@app.route("/profile")
@login_required
def profile():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', posts=posts)

# --- MESS ROUTES (Unchanged) ---

@app.route("/mess")
@login_required
def mess():
    today = date.today()
    meal_types = ["Breakfast", "Lunch", "Snack", "Dinner"]
    menu_data = {}
    
    defaults = {
        "Breakfast": "Idli, Sambar, Chutney, Coffee",
        "Lunch": "Rice, Dal, Aloo Fry, Curd",
        "Snack": "Samosa, Tea",
        "Dinner": "Chapati, Veg Curry, Milk"
    }

    needs_commit = False
    
    for m_type in meal_types:
        menu = MessMenu.query.filter_by(date=today, meal_type=m_type).first()
        if not menu:
            menu = MessMenu(date=today, meal_type=m_type, items=defaults[m_type])
            db.session.add(menu)
            needs_commit = True
        
        up = MessVote.query.filter_by(menu_id=menu.id, vote=1).count()
        down = MessVote.query.filter_by(menu_id=menu.id, vote=-1).count()
        user_voted = MessVote.query.filter_by(user_id=current_user.id, menu_id=menu.id).first()
        
        food_list = [item.strip() for item in menu.items.split(',') if item.strip()]

        menu_data[m_type] = {
            "id": menu.id,
            "food_list": food_list,
            "upvotes": up,
            "downvotes": down,
            "has_voted": True if user_voted else False
        }

    if needs_commit:
        db.session.commit() 

    comments = MessComment.query.filter_by(parent_id=None).order_by(MessComment.date_posted.desc()).all()
    
    return render_template('mess.html', 
        menu_data=menu_data, 
        comments=comments, 
        today=today, 
        User=User,
        MessComment=MessComment
    )

@app.route("/mess/vote/<int:menu_id>/<int:vote_type>")
@login_required
def vote_mess(menu_id, vote_type):
    existing_vote = MessVote.query.filter_by(user_id=current_user.id, menu_id=menu_id).first()
    if existing_vote:
        flash('You already voted for this meal!', 'danger')
    else:
        if vote_type not in [1, -1]:
            flash('Invalid vote type.', 'danger')
            return redirect(url_for('mess'))
            
        new_vote = MessVote(user_id=current_user.id, menu_id=menu_id, vote=vote_type)
        db.session.add(new_vote)
        db.session.commit()
        flash('Vote recorded!', 'success')
    return redirect(url_for('mess'))

@app.route("/mess/comment", methods=['POST'])
@login_required
def mess_comment():
    body = request.form.get('comment')
    parent_id = request.form.get('parent_id', None) 
    
    if body:
        if parent_id and parent_id.isdigit():
            parent_id = int(parent_id)
        else:
            parent_id = None
            
        comment = MessComment(body=body, user_id=current_user.id, parent_id=parent_id) 
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted!', 'success')
        
    return redirect(url_for('mess'))

# --- ADMIN ROUTES ---

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('update_menu'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_admin:
                login_user(user)
                flash('Welcome back, Admin.', 'success')
                return redirect(url_for('update_menu'))
            else:
                flash('Access Denied. Admins Only.', 'danger')
        else:
            flash('Login Failed.', 'danger')
    return render_template('admin_login.html')

@app.route("/mess/update", methods=['GET', 'POST'])
@login_required
def update_menu():
    if not current_user.is_admin:
        flash('Access Denied.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            menu_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('update_menu'))
            
        meal_types = ["Breakfast", "Lunch", "Snack", "Dinner"]
        
        for m_type in meal_types:
            items = request.form.get(m_type)
            menu = MessMenu.query.filter_by(date=menu_date, meal_type=m_type).first()
            if menu:
                menu.items = items
            else:
                new_menu = MessMenu(date=menu_date, meal_type=m_type, items=items)
                db.session.add(new_menu)
        
        db.session.commit()
        flash(f'Menu updated for {menu_date.strftime("%d %b")}!', 'success')
        return redirect(url_for('mess'))

    return render_template('update_menu.html', today=date.today())

if __name__ == '__main__':
    # When deploying, do NOT run app.run(). WSGI (Gunicorn) takes over.
    if os.environ.get('FLASK_ENV') == 'production':
        print("SRU FORUM PRODUCTION MODE")
    else:
        print("✅ SRU FORUM SERVER STARTED (Development)")
        app.run(debug=True)