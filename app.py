from flask import Flask, render_template, flash, redirect, url_for, session, request, make_response
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, validators, IntegerField
from wtforms.fields.html5 import DateTimeField
from functools import wraps
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'hamzaelahisquash'

# Config MySQL
app.config['MYSQL_HOST'] = 'den1.mysql4.gear.host'
app.config['MYSQL_USER'] = 'squash1'
app.config['MYSQL_PASSWORD'] = '3-1squash'
app.config['MYSQL_DB'] = 'squash1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/about')
def about():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get win games
    cur.execute("SELECT count(*) AS count FROM squash_games WHERE score_hamza > score_opponent")

    # Get all win in dict format
    win = cur.fetchone()['count']

    # Get draw games
    cur.execute("SELECT count(*) AS count FROM squash_games WHERE score_hamza = score_opponent")

    # Get draw in dict format
    draw = cur.fetchone()['count']

    # Get lost games
    cur.execute("SELECT count(*) AS count FROM squash_games WHERE score_hamza < score_opponent")

    # Get all lost in dict format
    loss = cur.fetchone()['count']

    # Close connection
    cur.close()

    return render_template('about.html', win=win, loss=loss, draw=draw)


@app.route('/home')
def home():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get games
    result = cur.execute("SELECT * FROM squash_games")

    # Get all games in dict format
    games = cur.fetchall()

    if result > 0:
        return render_template('home.html', games=games)
    else:
        msg = "No Games Found. Add Game"
        return render_template('home.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/game/<string:id>/')
def game(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get user by username
    result = cur.execute("SELECT comment FROM squash_games WHERE idgames = %s", [id])
    if result > 0:
        data = cur.fetchone()
        return render_template('game.html', comment=data['comment'])
    else:
        return render_template('game.html', comment="No Comment found")


# Register Form Class
class RegisterForm(Form):
    opponent = StringField('Opponent Name', [validators.Length(min=1, max=45)])
    datetime = DateTimeField('Date & time',  format='%Y-%m-%d %H:%M:%S')
    comment = TextAreaField('Comment', [validators.Length(min=0, max=100)])
    score_hamza = IntegerField('Hamza Score', [validators.NumberRange(min=0, max=100)])
    score_opponent = IntegerField('Opponent Score', [validators.NumberRange(min=0, max=100)])


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/register', methods=['Get', 'POST'])
@is_logged_in
def register():

    form = RegisterForm(request.form)
    form.datetime.data = datetime.now()
    if request.method == 'POST' and form.validate():
        opponent = form.opponent.data
        date_time = form.datetime.data
        comment = form.comment.data
        score_hamza = form.score_hamza.data
        score_opponent = form.score_opponent.data

        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("""INSERT INTO squash_games (opponent, date, comment, score_hamza, score_opponent ) VALUES(%s, %s, %s, %s, %s)""", (opponent, date_time, comment ,score_hamza, score_opponent))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        message = 'Game: Hamza Vs {} Added'.format(opponent)
        flash(message, 'success')

        return redirect(url_for('home'))
    return render_template('register.html', form=form)

# Edit game
@app.route('/edit_game/<string:id>', methods=['Get', 'POST'])
@is_logged_in
def edit_game(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute query
    result = cur.execute("SELECT *  FROM squash_games WHERE idgames= %s", [id])

    game = cur.fetchone()

    # Get form
    form = RegisterForm(request.form)

    # Populate fields
    form.opponent.data = game['opponent']
    form.datetime.data = game['date']

    if request.method == 'POST' and form.validate():
        opponent = request.form['opponent']
        date_time = request.form['datetime']
        comment = request.form['comment']
        score_hamza = request.form['score_hamza']
        score_opponent = request.form['score_opponent']

        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("""UPDATE  squash_games SET opponent=%s, date=%s, comment=%s, score_hamza=%s, score_opponent=%s WHERE idgames=%s""", (opponent, date_time, comment, score_hamza, score_opponent, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        message = 'Game: Hamza Vs {} Edited'.format(opponent)
        flash(message, 'success')

        return redirect(url_for('home'))
    return render_template('edit_game.html', form=form)


# Delete Game
@app.route('/delete_game/<string:id>', methods=['POST'])
@is_logged_in
def delete_game(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM squash_games WHERE idgames = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Game Deleted', 'success')

    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if password_candidate == password:
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You are  now logged out', 'success')
    return redirect(url_for('home'))


@app.route('/download')
@is_logged_in
def download():
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    result = cur.execute("SELECT * FROM squash_games")
    if result > 0:
        # Get stored hash
        all_games = cur.fetchall()
        csv = ""
        for game in all_games:
            for key, value in game.items():
                csv += "{},".format(value)
            csv += '\n'
        flash('Downloading Started', 'success')
        response = make_response(csv)
        cd = 'attachment; filename=data.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype = 'text/csv'

        return response
    else:
        flash('Nothing to Download', 'danger')
    # Close connection
    cur.close()
    return redirect(url_for('home'))


if __name__ == '__main__':

    app.run(debug=True)