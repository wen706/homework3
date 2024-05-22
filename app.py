import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3


app = Flask(__name__, static_folder="public", static_url_path="/")
app.config['DEBUG'] = True
app.secret_key = os.urandom(24)


# 設置日誌記錄
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# 實現登入功能用
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


def login_judge(username: str, password: str) -> bool:
    '''
    登入錯誤->false, 登入成功->true
    '''
    conn = sqlite3.connect('mydb.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"SELECT iid, idno, pwd FROM member WHERE idno = ? AND pwd = ?", (username, password))
    result = c.fetchone()
    conn.close()
    if result:
        return result["iid"]
    else:
        return False


# 登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username=="error":
                raise ValueError("=>error1")
            judge = login_judge(username, password)
            if judge:
                user = User(judge)
                login_user(user)
                return redirect(url_for('homee'))
            else:
                return render_template('login.html', error='請輸入正確的帳號密碼', username=username)
        return render_template('login.html')
    except Exception as e:
        app.logger.error(e)
        return render_template('error.html'), 500
    

@app.route('/')
@login_required
def homee():
    try:
        query = 'SELECT nm, birth, blood, phone, email, idno, pwd FROM member WHERE iid = ?'
        user_id = (current_user.get_id(),)
        conn = sqlite3.connect('mydb.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, user_id)
        data = c.fetchone()
        conn.close()
        return render_template('index.html', data=data)
    except Exception as e:
        app.logger.error(e)
        return render_template('error.html'), 500
    

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    try:
        if request.method == 'POST':
            update_sql = '''UPDATE member SET nm = ?, birth = ?, blood = ?, phone = ?, email = ?, idno = ?, pwd = ? WHERE iid = ?'''
            nm = request.form['nm']
            birth = request.form['birth']
            blood = request.form['blood']
            phone = request.form['phone']
            email = request.form['email']
            idno = request.form['idno']
            pwd = request.form['pwd']
            new_values = (nm, birth, blood, phone, email, idno, pwd, current_user.get_id())
            conn = sqlite3.connect('mydb.db')
            c = conn.cursor()
            c.execute(update_sql, new_values)
            conn.commit()
            conn.close()
            return redirect(url_for('homee'))
        
        query = 'SELECT nm, birth, blood, phone, email, idno, pwd FROM member WHERE iid = ?'
        user_id = (current_user.get_id(),)
        conn = sqlite3.connect('mydb.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, user_id)
        data = c.fetchone()
        conn.close()
        return render_template('edit.html', data=data)
    except Exception as e:
        app.logger.error(e)
        return render_template('error.html'), 500
    

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)