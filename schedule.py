import psycopg2
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://volleyball_db_oqjm_user:PUQZnejSQDATvlFXuiD9wNZKQxWwrCJk@dpg-d8kiqhvavr4c739i6p60-a.frankfurt-postgres.render.com/volleyball_db_oqjm"

def generate_schedule():
    """Автоматическая генерация кругового расписания по дивизионам из базы данных"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # --- АВТОМАТИЧЕСКОЕ СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦ В ОБЛАКЕ (ЕСЛИ ИХ НЕТ) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS divisions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                division_id INTEGER REFERENCES divisions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS halls (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address VARCHAR(200) NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL
            );
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                match_date TIMESTAMP NOT NULL,
                team_home_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
                team_away_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
                hall_id INTEGER REFERENCES halls(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                salt VARCHAR(32) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE
            );
        ''')
        conn.commit()

        # --- СНАЧАЛА НАПОЛНЯЕМ БАЗУ СТАРТОВЫМИ ДАННЫМИ (ЕСЛИ ТАБЛИЦЫ БЫЛИ ПУСТЫМИ) ---
        cursor.execute("SELECT COUNT(*) FROM divisions;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO divisions (name) VALUES ('Высшая лига'), ('1 лига');")
            cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES ('admin', '6494921b1b86e889a7da1794bfa55bbbb18df6b4aa366a5e12ca001ba027be0b', 'a5b4c3d2e1f0a5b4');")
            cursor.execute('''
                INSERT INTO halls (name, address, latitude, longitude) VALUES 
                ('Дворец Спорта', 'Минск, пр. Победителей, 4', 53.910543, 27.547562),
                ('Чижовка-Арена', 'Минск, ул. Ташкентская, 19', 53.844322, 27.639454),
                ('Велодром Минск-Арены', 'Минск, пр. Победителей, 111', 53.935122, 27.476412);
            ''')
            cursor.execute('''
                INSERT INTO teams (name, division_id) VALUES 
                ('Зенит', 1), ('ЦСКА', 1), ('Строитель', 2), ('Шахтер', 2);
            ''')
            conn.commit()

        # 1. Теперь очищаем старое расписание матчей перед пересчетом (теперь таблица точно есть!)
        cursor.execute("TRUNCATE TABLE matches RESTART IDENTITY CASCADE;")

        # 2. Берем список всех залов для привязки игр
        cursor.execute("SELECT id FROM halls;")
        hall_ids = [row[0] for row in cursor.fetchall()]
        if not hall_ids:
            print("Ошибка: В таблице halls нет ни одного зала!")
            return

        # 3. Получаем список всех дивизионов
        cursor.execute("SELECT id FROM divisions;")
        division_ids = [row[0] for row in cursor.fetchall()]

        start_date = datetime(2026, 6, 15, 10, 0) # Начало первого тура

        # 4. Делаем перебор по каждому дивизиону отдельно
        for div_id in division_ids:
            cursor.execute("SELECT id FROM teams WHERE division_id = %s ORDER BY id;", (div_id,))
            teams = [row[0] for row in cursor.fetchall()]
            
            num_teams = len(teams)
            if num_teams < 2:
                print(f"Дивизион ID {div_id}: недостаточно команд для генерации расписания.")
                continue

            if num_teams % 2 != 0:
                teams.append(None)
                num_teams += 1

            rounds = num_teams - 1
            matches_per_round = num_teams // 2

            for round_num in range(rounds):
                round_date = start_date + timedelta(weeks=round_num)
                
                for match_num in range(matches_per_round):
                    home = teams[match_num]
                    away = teams[num_teams - 1 - match_num]

                    if home is not None and away is not None:
                        match_time = round_date + timedelta(hours=(match_num * 2))
                        assigned_hall = hall_ids[match_num % len(hall_ids)]

                        cursor.execute('''
                            INSERT INTO matches (match_date, team_home_id, team_away_id, hall_id)
                            VALUES (%s, %s, %s, %s);
                        ''', (match_time, home, away, assigned_hall))

            start_date += timedelta(hours=4)

        conn.commit()
        print("=== КАРТА РАСПИСАНИЯ ПОЛНОСТЬЮ И УСПЕШНО ОБНОВЛЕНА ===")
    except Exception as e:
        print(f"Ошибка генерации в schedule.py: {e}")
    finally:
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    generate_schedule()
