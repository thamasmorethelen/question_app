from flask import (Flask, render_template, url_for,
                   g, request, session, redirect)
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()
    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()


def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        db.execute('SELECT id, name, password, expert, admin FROM users WHERE name = %s', (user, ))
        user_result = db.fetchone()
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    db.execute('''SELECT question.id as question_id,
                                 question.question_text, question.answer_text,
                                 question.asked_by_id, question.expert_id ,
                                 askers.name as asker_name, expert_list.name
                                 as expert_name FROM question JOIN users
                                 as askers ON question.asked_by_id = askers.id
                                 JOIN users as expert_list ON
                                 question.expert_id = expert_list.id
                                 WHERE answer_text IS NOT NULL''')
    question_answer = db.fetchall()
    return render_template('home.html', user=user, question_answer=question_answer)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        db.execute('SELECT name FROM users WHERE name = %s', (request.form['name'], ))
        existing_user = db.fetchone()
        if existing_user:
            return render_template('register.html', user=user, error='User already exists!')
        _hashed = generate_password_hash(request.form['password'], method='sha256')
        db.execute('INSERT INTO users (name, password, expert, admin) VALUES (%s, %s, %s, %s)', (request.form['name'], _hashed, '0', '0', ))
        session['user'] = request.form['name']
        return redirect(url_for('index'))
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    error = None
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']
        db.execute('SELECT id, name, password FROM users WHERE name = %s', (name, ))
        user_result = db.fetchone()
        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                error = 'Oh no incorrect password!'
        else:
            error = 'Oh no incorrect username!'
    return render_template('login.html', user=user, error=error)


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    db.execute('''SELECT question.id as question_id,
                                 question.question_text, question.answer_text,
                                 question.asked_by_id, question.expert_id ,
                                 askers.name as asker_name, expert_list.name
                                 as expert_name FROM question JOIN users
                                 as askers ON question.asked_by_id = askers.id
                                 JOIN users as expert_list ON
                                 question.expert_id = expert_list.id
                                 WHERE question_id = %s ''', (question_id, ))
    question = db.fetchone()
    return render_template('question.html', user=user, question=question)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['expert']:
        return redirect(url_for('index'))
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE question SET answer_text = %s WHERE id = %s ', (request.form['answer'], question_id, ))
        return redirect(url_for('unanswered'))
    db.execute('SELECT id, question_text FROM question WHERE id = %s', (question_id, ))
    question = db.fetchone()
    return render_template('answer.html', user=user, question=question)


@app.route('/ask/', methods=['GET', 'POST'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()

    if request.method == 'POST':
        db.execute('''INSERT INTO question (question_text, asked_by_id, expert_id)
                      VALUES (%s, %s, %s )''', (request.form['question'], user['id'], request.form['expert']))

        return redirect(url_for('index'))
    db.execute('SELECT id, name FROM users WHERE expert = True')
    expert_list = db.fetchall()
    return render_template('ask.html', user=user, experts=expert_list)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['expert']:
        return redirect(url_for('index'))
    db = get_db()
    db.execute('''SELECT question.id, question.question_text,
                                 users.name FROM question JOIN users
                                 ON users.id = question.asked_by_id
                                 WHERE question.expert_id = %s
                                 AND question.answer_text IS NULL''', (user['id'], ))
    question_list = db.fetchall()
    return render_template('unanswered.html', user=user, question_list=question_list)


@app.route('/users')
def users():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['admin']:
        return redirect(url_for('index'))
    db = get_db()
    db.execute('SELECT id, name, expert, admin FROM users')
    user_list = db.fetchall()
    return render_template('users.html', user=user, user_list=user_list)


@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['admin']:
        return redirect(url_for('index'))
    db = get_db()
    db.execute('UPDATE users SET expert = True WHERE id = %s', (user_id, ))
    return redirect(url_for('users'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
