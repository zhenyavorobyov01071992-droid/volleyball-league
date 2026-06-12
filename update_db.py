import psycopg2

try:
    # Чистые параметры подключения без лишних символов
    conn = psycopg2.connect(
        host="dpg-d8kiqhvavr4c739i6p60-a.frankfurt-postgres.render.com",
        database="volleyball_db_oqjm",
        user="volleyball_db_oqjm_user",
        password="PUQZnejSQDATvlFXuiD9wNZKQxWwrCJk",
        port=5432
    )
    cursor = conn.cursor()
    
    print("Подключение установлено, отправляем запрос...")
    
    cursor.execute('''
        ALTER TABLE matches 
        ADD COLUMN IF NOT EXISTS score_home INT DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS score_away INT DEFAULT NULL;
    ''')
    
    conn.commit()
    print("🚀 УСПЕШНО: Колонки счета добавлены в базу данных на Render!")
    
except Exception as e:
    print(f"❌ ОШИБКА: Не удалось обновить базу: {e}")
finally:
    if 'conn' in locals(): 
        conn.close()
