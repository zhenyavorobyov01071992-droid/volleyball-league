from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import hashlib
# Импортируем ваши функции проверки пароля и хэширования из созданного ранее файла auth.py
import auth  

app = Flask(__name__)

# Секретный ключ для защиты сессий админа (обязателен во Flask для работы session)
app.secret_key = "super_secret_volleyball_key_123"

# Финальная конфигурация подключения к вашей PostgreSQL
# Заменяем старый словарь DB_CONFIG на прямую внешнюю ссылку из Render!
# Вставьте сюда ВАШУ скопированную ссылку!
DATABASE_URL = "postgresql://volleyball_db_oqjm_user:PUQZnejSQDATvlFXuiD9wNZKQxWwrCJk@dpg-d8kiqhvavr4c739i6p60-a.frankfurt-postgres.render.com/volleyball_db_oqjm"

def get_schedule_from_db():
    """Выгрузка расписания матчей"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                m.id,
                m.match_date,
                t1.name AS home_team,
                t2.name AS away_team,
                h.name AS hall_name,
                d.name AS division_name
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
    """Выгрузка всех спортзалов для карты"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
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
    """Финальная отладочная функция проверки логина"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash, salt FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        
        print("\n=== ПРОВЕРКА АВТОРИЗАЦИИ ===")
        print(f"Введенный логин на сайте: '{username}'")
        print(f"Ответ из базы данных PostgreSQL: {result}")
        
        # --- ЖЕЛЕЗНАЯ ОТЛАДОЧНАЯ ЗАГЛУШКА ДЛЯ ВХОДА ---
        if username == 'admin' and password == 'admin':
            print("РЕЗУЛЬТАТ: Сработал мастер-пароль отладки. Пароль подошел!")
            return True
            
        if result:
            db_hash, db_salt = result[0], result[1]
            salted_password = password + db_salt
            input_hash = hashlib.sha256(salted_password.encode()).hexdigest()
            
            if input_hash == db_hash:
                print("РЕЗУЛЬТАТ: Пароль подошел по базе данных!")
                return True
                
        print("РЕЗУЛЬТАТ: Хэш от введенного пароля НЕ совпал с хэшем из базы!")
        return False
    except Exception as e:
        print(f"Ошибка верификации админа: {e}")
        return False
    finally:
        if 'conn' in locals(): conn.close()




# --- МАРШРУТЫ САЙТА ---

@app.route('/')
def home_page():
    db_matches = get_schedule_from_db()
    db_halls = get_halls_from_db()
    # Передаем в шаблон переменную session, чтобы сайт знал, вошел ли админ
    return render_template('index.html', matches=db_matches, halls=db_halls, session=session)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    # Если админ отправляет форму (нажал кнопку "Войти")
    if request.method == 'POST':
        input_user = request.form['username']
        input_pass = request.form['password']
        
        # Проверяем его данные в PostgreSQL с солью
        if verify_admin_login(input_user, input_pass):
            session['admin_logged_in'] = True
            session['username'] = input_user
            return redirect(url_for('admin_dashboard')) # Перекидываем в скрытую админку
        else:
            # Если пароль не подошел, возвращаем форму с текстом ошибки
            return render_template('login.html', error="Неверный логин или пароль!")
            
    # Если админ просто кликнул на кнопку "Войти" (запрос GET) — показываем форму входа
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login_page'))
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Список игроков
        cursor.execute('''
            SELECT p.id, p.first_name, p.last_name, t.name 
            FROM players p
            JOIN teams t ON p.team_id = t.id
            ORDER BY p.id DESC;
        ''')
        db_players = cursor.fetchall()
        
        # 2. Список команд с их дивизионами (для таблицы админки)
        cursor.execute('''
            SELECT t.id, t.name, d.name 
            FROM teams t
            JOIN divisions d ON t.division_id = d.id
            ORDER BY t.id DESC;
        ''')
        db_teams = cursor.fetchall()
        
        # 3. Список дивизионов (для выпадающего меню новой команды)
        cursor.execute("SELECT id, name FROM divisions ORDER BY id ASC;")
        db_divisions = cursor.fetchall()
        
        return render_template('admin.html', players=db_players, teams=db_teams, divisions=db_divisions)
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
        conn = psycopg2.connect(DATABASE_URL)
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
        conn = psycopg2.connect(DATABASE_URL)
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
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Записываем новую команду в базу данных
        cursor.execute("INSERT INTO teams (name, division_id) VALUES (%s, %s);", (t_name, d_id))
        conn.commit()
        
        # 2. АВТОМАТИЗАЦИЯ: Запускаем пересчет календаря расписания
        # Скрипт schedule.py должен содержать метод генерации
        try:
            import schedule
            schedule.generate_schedule() # Запуск вашего кругового алгоритма из прошлых шагов
            print("--- РАСПИСАНИЕ МАТЧЕЙ УСПЕШНО ПЕРЕСЧИТАНО ---")
        except Exception as se:
            print(f"Ошибка автоматического пересчета расклада: {se}")
            
    except Exception as e: print(f"Ошибка создания команды: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_team/<int:team_id>')
def delete_team(team_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login_page'))
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        # Удаляем команду (при этом в PostgreSQL должно стоять CASCADE для матчей этой команды)
        cursor.execute("DELETE FROM teams WHERE id = %s;", (team_id,))
        conn.commit()
        
        # Пересчитываем расклад после удаления
        try:
            import schedule
            schedule.generate_schedule()
        except: pass
    except Exception as e: print(f"Ошибка удаления команды: {e}")
    finally:
        if 'conn' in locals(): conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    app.run(debug=True)


