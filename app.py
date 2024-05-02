from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['movie_reviews']

user_id = 0
current_movie_id = 10
# Create collections
movies_collection = db['movies']
comments_collection = db['comments']
comments2_collection = db['comments2']
users_collection = db['users']
movies_comments = db['movies_comments']
users_comments = db['users_comments']

if movies_collection.count_documents({}) == 0:
    # If empty, insert the dummy movie data into the movies collection
    movies_data = [
        {"_id": 1, "title": "The Shawshank Redemption", "year": 1994},
        {"_id": 2, "title": "The Godfather", "year": 1972},
        {"_id": 3, "title": "The Dark Knight", "year": 2008}
    ]
    movies_collection.insert_many(movies_data)

if users_collection.count_documents({}) == 0:
    # If empty, insert the dummy movie data into the movies collection
    user_data = [
        # Default admin account to manage all comments
        {"_id": 1, "name": "Admin", "password": "0000"},
        {"name": "felicity", "password": "12345"}
    ]
    users_collection.insert_many(user_data)


@app.route('/')
def index():
    # Retrieve all movies from the database
    movies = list(movies_collection.find())

    return render_template('index.html', movies=movies, user_id=user_id)

@app.route('/login')
def render_login():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query MongoDB to find the user
        user = users_collection.find_one({'name': username, 'password': password})

        # Check if the user exists and the password matches
        if user:
            global user_id
            user_id = user['_id']

            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register')
def render_register():
    return render_template('register.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check duplicate user name
        existing_user = users_collection.find_one({'name': username})
        if existing_user:
            return 'Username already exists!'

        users_collection.insert_one({'name': username, 'password': password})
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile')
def profile():
    global user_id
    user = users_collection.find_one({"_id": user_id})
    if user_id == 0:
        return render_template('profile.html', user=user, comments=[], users=[], user_id=user_id)
    elif user_id == 1:
        comments1 = list(comments_collection.find())
        comments2 = list(comments2_collection.find())
        comments = comments1 + comments2
    else:
        comment_ids_cursor = users_comments.find({"user_id": user_id})

        comment_ids = [comment['comment_id'] for comment in comment_ids_cursor]
        if len(user['name']) % 2 == 1:
            comments = comments_collection.find({"_id": {"$in": comment_ids}})
        else:
            comments = comments2_collection.find({"_id": {"$in": comment_ids}})

    # To be optimized - update the value passed into template, or maybe change of data structure
    comments_movie_title = []
    for comment in comments:
        movie_id = movies_comments.find_one({"comment_id": comment['_id']})
        movie = movies_collection.find_one({"_id": movie_id['movie_id']})
        if movie:
            updated_comment = dict(comment)
            updated_comment["title"] = movie['title']
            if user_id == 1:
                comment_user_id = users_comments.find_one({"comment_id": comment['_id']})
                comment_user = users_collection.find_one({"_id": comment_user_id['user_id']})
                updated_comment["name"] = comment_user['name'] + ": "
            comments_movie_title.append(updated_comment)

    users = list(users_collection.find({"_id": {"$ne": 1}}))
    return render_template('profile.html', user=user, comments=comments_movie_title, users=users, user_id=user_id)

@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    comment_ids_cursor = movies_comments.find({"movie_id": movie_id})
    comment_ids = [comment['comment_id'] for comment in comment_ids_cursor]
    comments1 = list(comments_collection.find({"_id": {"$in": comment_ids}}))
    comments2 = list(comments2_collection.find({"_id": {"$in": comment_ids}}))
    comments = comments1 + comments2
    movie_info = movies_collection.find_one({"_id": movie_id})
    return render_template('movie.html', movie=movie_info, comments=comments)


@app.route('/movie/<int:movie_id>/comments')
def movie_comments(movie_id):
    # Retrieve comments for the specified movie
    movie_info = movies_collection.find_one({"_id": movie_id})
    #movie_comments = list(comments_collection.find({"movie_id": movie_id}))

    comment_found = movies_comments.find({"movie_id": movie_id})
    comment_ids = [comment['comment_id'] for comment in comment_found]

    comments_1 = list(comments_collection.find({"_id": {"$in": comment_ids}}))
    comments_2 = list(comments2_collection.find({"_id": {"$in": comment_ids}}))
    movie_comments = comments_1 + comments_2

    # comment_found_1 = movies_comments.find({"movie_id": movie_id})
    # comments_1 = []
    # for comment in comment_found_1:
    #     comment_id = comment['comment_id']
    #     user_comment = users_comments.find_one({"comment_id": comment_id})
    #     user_id = user_comment['user_id']
    #     comment_doc = {
    #         "comment": comment,
    #         "user_id": user_id
    #     }
    #     comments_1.append(comment_doc)
    #
    #
    # comment_found_2 = movies_comments.find({"movie_id": movie_id})
    # comments_2 = []
    # for comment in comment_found_2:
    #     comment_id = comment['comment_id']
    #     user_comment = users_comments.find_one({"comment_id": comment_id})
    #     user_id = user_comment['user_id']
    #     comment_doc = {
    #         "comment": comment,
    #         "user_id": user_id
    #     }
    #     comments_2.append(comment_doc)
    #
    #
    # movie_comments = comments_1 + comments_2

    return render_template('movie_comments.html', movie=movie_info, comments=movie_comments)


@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    if user_id != 1:
        return 'You are not authorized to delete movies.'
    movies_collection.delete_one({"_id": movie_id})

    return redirect(url_for('index'))


@app.route('/post_comment/<int:movie_id>', methods=['POST'])
def post_comment(movie_id):
    global user_id
    user = users_collection.find_one({"_id": user_id})
    comment = request.form['comment']
    if comment:
        if len(user['name']) % 2 == 1:
            result = comments_collection.insert_one({"comment": comment, "create_user_id": user_id})
        else:
            result = comments2_collection.insert_one({"comment": comment, "create_user_id": user_id})
        comment_id = result.inserted_id
        movies_comments.insert_one({"movie_id": movie_id, "comment_id": comment_id})

        users_comments.insert_one({"user_id": user_id, "comment_id": comment_id})
    return redirect(url_for('movie', movie_id=movie_id))

@app.route('/delete_comment/<string:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    global user_id
    user = users_collection.find_one({"_id": user_id})
    comment_id = ObjectId(comment_id)
    if len(user['name']) % 2 == 1:
        comments_collection.delete_one({"_id": comment_id})
    else:
        comments2_collection.delete_one({"_id": comment_id})
    users_collection.delete_one({"comment_id": comment_id})
    movies_comments.delete_one({"comment_id": comment_id})
    return redirect(url_for('profile'))

@app.route('/edit_comment/<string:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    global user_id
    user = users_collection.find_one({"_id": user_id})
    comment_id = ObjectId(comment_id)
    edited_comment = request.form['edited_comment']
    if len(user['name']) % 2 == 1:
        comments_collection.update_one({"_id": comment_id}, {"$set": {"comment": edited_comment}})
    else:
        comments2_collection.update_one({"_id": comment_id}, {"$set": {"comment": edited_comment}})
    return redirect(url_for('profile'))

# wy
@app.route('/add_movie')
def render_add_movie():
    return render_template('submit_movie.html')


@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    global current_movie_id
    if request.method == 'POST':
        movie_name = request.form['movie_name']
        movie_year = request.form['movie_year']

        # Check duplicate movie name
        existing_movie = movies_collection.find_one({'title': movie_name})
        if existing_movie:
            return 'Movie has already been added!'
        movie_id = current_movie_id + 1
        current_movie_id += 1
        movies_collection.insert_one({'_id': movie_id, 'title': movie_name, 'year': movie_year})
        return redirect(url_for('index'))

    return render_template('submit_movie.html')

@app.route('/update_profile')
def render_update_profile():
    return render_template('update_profile.html')


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users_collection.update_one({"_id": user_id}, {"$set": {"name": username, "password": password}})
        return redirect(url_for('profile'))

    return render_template('update_profile.html')

@app.route('/edit_user/<string:user_id>')
def render_edit_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    return render_template('edit_user.html', user=user)


@app.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"name": username, "password": password}})
        return redirect(url_for('profile'))

    return render_template('edit_user.html')

if __name__ == '__main__':
    app.run(debug=True)
