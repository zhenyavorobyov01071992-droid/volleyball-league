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