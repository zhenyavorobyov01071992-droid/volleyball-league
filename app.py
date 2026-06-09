from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

# Финальная конфигурация подключения к вашей PostgreSQL
DB_CONFIG = {
    "dbname": "volleyball_db",
    "user": "postgres",
    "password": "375447340720",  # Сюда впишите ваш личный пароль от pgAdmin!
    "host": "localhost",
    "port": "5432"
}

def get_schedule_from_db():
    """Выгрузка расписания матчей с полной распаковкой связей таблиц (5 колонок)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Этот запрос строго собирает: ID(0), Дату(1), Хозяев(2), Гостей(3) и Зал(4)
        cursor.execute('''
            SELECT 
                m.id,
                m.match_date,
                t1.name AS home_team,
                t2.name AS away_team,
                h.name AS hall_name
            FROM matches m
            JOIN teams t1 ON m.team_home_id = t1.id
            JOIN teams t2 ON m.team_away_id = t2.id
            JOIN halls h ON m.hall_id = h.id
            ORDER BY m.match_date ASC;
        ''')
        return cursor.fetchall()
    except Exception as e:
        print(f"--- КРИТИЧЕСКАЯ ОШИБКА БАЗЫ ДАННЫХ (МАТЧИ) ---: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

def get_halls_from_db():
    """Выгрузка всех спортзалов с координатами для нашей автономной карты"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT name, address, latitude, longitude FROM halls;")
        rows = cursor.fetchall()
        halls = []
        for row in rows:
            halls.append({
                "name": row[0],
                "address": row[1],
                "lat": float(row[2]),
                "lng": float(row[3])
            })
        return halls
    except Exception as e:
        print(f"--- КРИТИЧЕСКАЯ ОШИБКА БАЗЫ ДАННЫХ (ЗАЛЫ) ---: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

@app.route('/')
def home_page():
    db_matches = get_schedule_from_db()
    db_halls = get_halls_from_db()
    return render_template('index.html', matches=db_matches, halls=db_halls)

if __name__ == "__main__":
    app.run(debug=True)

