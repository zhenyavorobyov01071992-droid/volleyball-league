from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import hashlib
# Импортируем ваши функции проверки пароля и хэширования из созданного ранее файла auth.py
import auth  

app = Flask(__name__)

# Секретный ключ для защиты сессий админа (обязателен во Flask для работы session)
app.secret_key = "super_secret_volleyball_key_123"

# Финальная конфигурация подключения к вашей PostgreSQL
DB_CONFIG = {
    "dbname": "volleyball_db",
    "user": "postgres",
    "password": "375447340720",  # Сюда впишите ваш личный пароль от pgAdmin!
    "host": "localhost",
    "port": "5432"
}

def get_schedule_from_db():
    """Выгрузка расписания матчей"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.match_date, t1.name, t2.name, h.name
            FROM matches m
            JOIN teams t1 ON m.team_home_id = t1.id
            JOIN teams t2 ON m.team_away_id = t2.id
            JOIN halls h ON m.hall_id = h.id
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
        conn = psycopg2.connect(**DB_CONFIG)
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
        conn = psycopg2.connect(**DB_CONFIG)
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
    # Защита страницы: если в сессии нет метки админа, выгоняем его на форму входа
    if not session.get('admin_logged_in'):
        return redirect(url_for('login_page'))
        
    # Секретная страница админки (Этап 6, пункт 3)
    return "<h1>Добро пожаловать в скрытую админку! Тут вы сможете редактировать игроков.</h1><a href='/logout'>Выйти из системы</a>"

@app.route('/logout')
def logout():
    # Очищаем сессию (удаляем "паспорт" админа) и выходим из системы
    session.clear()
    return redirect(url_for('home_page'))


# --- Этот маршрут должен быть ВЫШЕ, чем запуск сервера! ---
@app.route('/create_admin_fix')
def create_admin_fix():
    """Временный маршрут для создания админа с автоматическим определением колонок"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Генерируем хэш и соль для слова "admin" строго через ваш файл auth.py
        new_hash, new_salt = auth.hash_password("admin")
        
        # 2. Очищаем таблицу users
        cursor.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
        
        # 3. Пытаемся записать через колонку 'username'
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s);",
                ("admin", new_hash, new_salt)
            )
            conn.commit()
            return "<h3>Администратор успешно создан!</h3><p>Использована колонка: <b>username</b></p><a href='/login'>Перейти ко входу</a>"
        except Exception:
            conn.rollback()
            # 4. Если не вышло, записываем через альтернативную колонку 'login'
            cursor.execute(
                "INSERT INTO users (login, password_hash, salt) VALUES (%s, %s, %s);",
                ("admin", new_hash, new_salt)
            )
            conn.commit()
            return "<h3>Администратор успешно создан!</h3><p>Использована колонка: <b>login</b></p><a href='/login'>Перейти ко входу</a>"
            
    except Exception as e:
        return f"<h3>Критическая ошибка генерации:</h3><p>{e}</p>"
    finally:
        if 'conn' in locals(): conn.close()



# --- И ТОЛЬКО В САМОМ КОНЦЕ ФАЙЛА ЗАПУСКАЕТСЯ СЕРВЕР ---
if __name__ == "__main__":
    app.run(debug=True)
