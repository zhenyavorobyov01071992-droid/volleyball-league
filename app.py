from flask import Flask, render_template, jsonify
import psycopg2

app = Flask(__name__)

# Конфигурация базы данных
DB_CONFIG = {
    "dbname": "volleyball_db",
    "user": "postgres",
    "password": "ВАШ_ПАРОЛЬ",  # Сюда впишите ваш пароль от pgAdmin!
    "host": "localhost",
    "port": "5432"
}

def get_schedule_from_db():
    """Выгрузка расписания матчей"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, t1.name, h.name, t2.name, m.match_date, d.name
            FROM matches m
            JOIN teams t1 ON m.team_home_id = t1.id
            JOIN teams t2 ON m.team_away_id = t2.id
            JOIN halls h ON m.hall_id = h.id
            LEFT JOIN divisions d ON t1.division_id = d.id
            ORDER BY m.match_date ASC;
        ''')
        return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка матчей: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

def get_halls_from_db():
    """Выгрузка залов с координатами для карты"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Вытаскиваем Название, Адрес, Широту и Долготу из таблицы halls
        cursor.execute("SELECT name, address, latitude, longitude FROM halls;")
        rows = cursor.fetchall()
        
        # Превращаем данные в удобный список словарей для JavaScript
        halls = []
        for row in rows:
            halls.append({
                "name": row[0],
                "address": row[1],
                "lat": float(row[2]),  # Переводим число из БД в дробь Python
                "lng": float(row[3])
            })
        return halls
    except Exception as e:
        print(f"Ошибка залов: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

@app.route('/')
def home_page():
    db_matches = get_schedule_from_db()
    db_halls = get_halls_from_db()  # Забираем залы из базы данных
    # Передаем в HTML-шаблон и матчи, и список залов с координатами
    return render_template('index.html', matches=db_matches, halls=db_halls)

if __name__ == "__main__":
    app.run(debug=True)
