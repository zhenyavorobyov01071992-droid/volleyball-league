import psycopg2


DB_NAME = "volleyball_db"
DB_USER = "postgres"        
DB_PASSWORD = "375447340720"  
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()
# Даем команду базе данных создать таблицу Дивизионов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS divisions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE
    );
    ''')

    # Даем команду создать таблицу Команд (с внешним ключом)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        division_id INTEGER REFERENCES divisions(id) ON DELETE SET NULL
    );
    ''')

    # Даем команду создать таблицу Игроков (с внешним ключом)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL
    );
    ''')

    # Даем команду создать таблицу Спортивных залов (для Google Карт)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS halls (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255) NOT NULL,
        latitude NUMERIC(9, 6) NOT NULL,
        longitude NUMERIC(9, 6) NOT NULL
    );
    ''')

    # Фиксируем изменения в базе данных
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,   -- Логин (должен быть уникальным)
        password_hash VARCHAR(255) NOT NULL,    -- Зашифрованный пароль
        salt VARCHAR(255) NOT NULL,             -- Уникальная соль для этого пользователя
        role VARCHAR(20) DEFAULT 'admin'        -- Роль для проверки особых прав доступа
    );
    ''')
    # 6. Таблица 6: Расписание матчей (связывает команды, залы и даты)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY,
        team_home_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,  -- Хозяева
        team_away_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,  -- Гости
        hall_id INTEGER REFERENCES halls(id) ON DELETE SET NULL,      -- Спортзал
        match_date TIMESTAMP NOT NULL                                 -- Дата и время матча
    );
    ''')
    conn.commit()
    
    # ВОТ ЭТОТ ОТВЕТ вы должны увидеть на экране!
    print("Ура! Все 6 таблиц успешно созданы в PostgreSQL!")

except Exception as error:
    # А этот ответ появится ТОЛЬКО если вы ввели неверный пароль или забыли включить pgAdmin
    print(f"Произошла ошибка при создании таблиц: {error}")

finally:
    # Закрываем связь с базой в любом случае
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

        import psycopg2
from datetime import datetime, timedelta

def generate_and_save_schedule():
    # 1. Настройки подключения к вашей PostgreSQL
    DB_NAME = "volleyball_db"
    DB_USER = "postgres"        
    DB_PASSWORD = "375447340720"  # Замените на свой пароль!
    DB_HOST = "localhost"
    DB_PORT = "5432"

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()

        # 2. Достаем все команды из базы данных
        cursor.execute("SELECT id, name FROM teams;")
        teams = cursor.fetchall()  # Получаем список кортежей вида [(1, 'Зенит'), (2, 'Спартак')]

        # 3. Достаем все залы из базы данных
        cursor.execute("SELECT id, name FROM halls;")
        halls = cursor.fetchall()

        if len(teams) < 2:
            print("Ошибка: Для генерации расписания нужно минимум 2 команды!")
            return
        if not halls:
            print("Ошибка: В базе данных нет ни одного спортивного зала!")
            return

        # Если количество команд нечетное, добавляем виртуальную команду (пропуск тура)
        if len(teams) % 2 != 0:
            teams.append((None, "Выходной"))

        num_teams = len(teams)
        num_rounds = num_teams - 1  # Количество туров в круговой системе
        matches_per_round = num_teams // 2

        # Начальная дата для проведения лиги (например, ближайшая суббота)
        start_date = datetime.now() + timedelta(days=1)
        
        print("--- СТАРТ ГЕНЕРАЦИИ РАСПИСАНИЯ ---")

        # 4. Круговой алгоритм распределения (Round-robin)
        for round_num in range(num_rounds):
            # Игровой день для текущего тура (каждый тур — через неделю)
            round_date = start_date + timedelta(weeks=round_num)
            
            for match_num in range(matches_per_round):
                home = teams[match_num]
                away = teams[num_teams - 1 - match_num]

                # Пропускаем матчи с виртуальной командой "Выходной"
                if home[0] is not None and away[0] is not None:
                    # Назначаем зал по кругу, используя остаток от деления
                    hall = halls[(round_num + match_num) % len(halls)]

                    # Устанавливаем точное время матча (например, первый в 10:00, второй в 12:00)
                    match_time = round_date.replace(hour=10 + (match_num * 2), minute=0, second=0, microsecond=0)

                    # 5. Записываем сгенерированный матч в таблицу `matches`
                    cursor.execute('''
                        INSERT INTO matches (team_home_id, team_away_id, hall_id, match_date)
                        VALUES (%s, %s, %s, %s);
                    ''', (home[0], away[0], hall[0], match_time))

                    print(f"Тур {round_num + 1}: {home[1]} vs {away[1]} | Зал: {hall[1]} | Дата: {match_time.strftime('%Y-%m-%d %H:%M')}")

            # Сдвигаем команды по кругу для следующего тура (первая команда остается на месте)
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        # Сохраняем все добавленные матчи в PostgreSQL
        conn.commit()
        print("--- РАСПИСАНИЕ УСПЕШНО СГЕНЕРИРОВАНО И ЗАПИСАНО В БД ---")

    except Exception as error:
        print(f"Ошибка алгоритма: {error}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    generate_and_save_schedule()