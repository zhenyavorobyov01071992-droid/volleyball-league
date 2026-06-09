from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

def get_schedule_from_db():
    """Функция подключения к PostgreSQL для выгрузки расписания матчей"""
    DB_NAME = "volleyball_db"
    DB_USER = "postgres"
    DB_PASSWORD = "375447340720"  # Сюда впишите ваш пароль от pgAdmin!
    DB_HOST = "localhost"
    DB_PORT = "5432"
    
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cursor = conn.cursor()
        
        # SQL-запрос, связывающий таблицы (JOIN), чтобы получить имена вместо ID-номеров
        cursor.execute('''
            SELECT 
                m.id,
                t1.name AS home_team,
                h.name AS hall_name,
                t2.name AS away_team,
                m.match_date
            FROM matches m
            JOIN teams t1 ON m.team_home_id = t1.id
            JOIN teams t2 ON m.team_away_id = t2.id
            JOIN halls h ON m.hall_id = h.id
            ORDER BY m.match_date ASC;
        ''')
        data = cursor.fetchall()
        return data
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        return []
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.route('/')
def home_page():
    # 1. Забираем сгенерированные матчи из базы данных
    db_matches = get_schedule_from_db()
    # 2. Рендерим (отрисовываем) файл index.html, передавая туда список матчей
    return render_template('index.html', matches=db_matches)

if __name__ == "__main__":
    app.run(debug=True)
