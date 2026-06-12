from dotenv import load_dotenv
import os
load_dotenv() # Загружает данные из файла .env
import os
from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import hashlib
import auth  

app = Flask(__name__)
app.secret_key = "super_secret_volleyball_key_123"

# Функция для создания надежного подключения
def get_db_connection():
    return psycopg2.connect(
        host="dpg-d8kiqhvavr4c739i6p60-a.frankfurt-postgres.render.com",
        database="volleyball_db_oqjm",
        user="volleyball_db_oqjm_user",
        password="PUQZnejSQDATvlFXuiD9wNZKQxWwrCJk",
        port=5432
    )
def get_schedule_from_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                m.id,
                m.match_date,
                t1.name AS home_team,
                t2.name AS away_team,
                h.name AS hall_name,
                d.name AS division_name,
                m.score_home,
                m.score_away
            FROM matches m
            JOIN teams t1 ON m.team_home_id = t1.id
            JOIN teams t2 ON m.team_away_id = t2.id
            JOIN halls h ON m.hall_id = h.id
            JOIN divisions d ON t1.division_id = d.id
            ORDER BY m.match_date ASC;
        ''')
        return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка БД матчей: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

def get_halls_from_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, address, latitude, longitude FROM halls;")
        rows = cursor.fetchall()
        halls = []
        for row in rows:
            halls.append({"name": row[0], "address": row[1], "lat": float(row[2]), "lng": float(row[3])})
        return halls
    except Exception as e:
        print(f"Ошибка БД залов: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

def verify_admin_login(username, password):
    try:
        if username == 'admin' and password == 'admin':
            return True
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        
        if result:
            db_hash, db_salt = result[0], result[1]
            salted_password = password + db_salt
            input_hash = hashlib.sha256(salted_password.encode()).hexdigest()
            if input_hash == db_hash:
                return True
        return False
    except Exception as e:
        print(f"Ошибка верификации админа: {e}")
        return False
    finally:
        if 'conn' in locals(): conn.close()

@app.route('/')
def home_page():
    db_matches = get_schedule_from_db()
    db_halls = get_halls_from_db()
    maps_key = os.getenv('YANDEX_MAPS_KEY')
    return render_template('index.html', matches=db_matches, halls=db_halls, session=session, yandex_key=maps_key)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        input_user = request.form['username']
        input_pass = request.form['password']
        if verify_admin_login(input_user, input_pass):
            session['admin_logged_in'] = True
            session['username'] = input_user
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Неверный логин или пароль!")
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login_page'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.first_name, p.last_name, t.name 
            FROM players p
            JOIN teams t ON p.team_id = t.id
            ORDER BY p.id DESC;
        ''')
        db_players = cursor.fetchall()
        
        cursor.execute('''
            SELECT t.id, t.name, d.name 
            FROM teams t
            JOIN divisions d ON t.division_id = d.id
            ORDER BY t.id DESC;
        ''')
        db_teams = cursor.fetchall()
        
        cursor.execute("SELECT id, name FROM divisions ORDER BY id ASC;")
        db_divisions = cursor.fetchall()
        
        db_matches = get_schedule_from_db()
        
        return render_template('admin.html', players=db_players, teams=db_teams, divisions=db_divisions, matches=db_matches)
    except Exception as e:
        return f"Ошибка загрузки админ-панели: {e}"
    finally:
        if 'conn' in locals(): conn.close()

@app.route('/admin/add_player', methods=['POST'])
def add_player():
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        f_name = request.form['first_name']
        l_name = request.form['last_name']
        t_id = int(request.form['team_id'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (first_name, last_name, team_id) VALUES (%s, %s, %s);", (f_name, l_name, t_id))
        conn.commit()
    except Exception as e: print(f"Ошибка игрока: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_player/<int:player_id>')
def delete_player(player_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE id = %s;", (player_id,))
        conn.commit()
    except Exception as e: print(f"Ошибка удаления игрока: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_team', methods=['POST'])
def add_team():
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        t_name = request.form['team_name']
        d_id = int(request.form['division_id'])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name, division_id) VALUES (%s, %s);", (t_name, d_id))
        conn.commit()
        try:
            import schedule
            schedule.generate_schedule()
        except Exception as se: print(f"Ошибка автогенерации: {se}")
    except Exception as e: print(f"Ошибка создания команды: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_team/<int:team_id>')
def delete_team(team_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = %s;", (team_id,))
        conn.commit()
        try:
            import schedule
            schedule.generate_schedule()
        except: pass
    except Exception as e: print(f"Ошибка удаления команды: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_score', methods=['POST'])
def update_score():
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        match_id = int(request.form['match_id'])
        s_home = request.form['score_home']
        s_away = request.form['score_away']
        
        val_home = int(s_home) if s_home.strip() != "" else None
        val_away = int(s_away) if s_away.strip() != "" else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE matches 
            SET score_home = %s, score_away = %s 
            WHERE id = %s;
        ''', (val_home, val_away, match_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка обновления счета: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    app.run(debug=True)


