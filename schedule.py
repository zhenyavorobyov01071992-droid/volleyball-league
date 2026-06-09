import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    "dbname": "volleyball_db",
    "user": "postgres",
    "password": "375447340720",  # Сюда впишите ваш пароль от pgAdmin!
    "host": "localhost",
    "port": "5432"
}

def generate_schedule():
    """Автоматическая генерация кругового расписания по дивизионам из базы данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. Очищаем старое расписание матчей перед пересчетом
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
                print(f"Дивизион ID {div_id}: недостаточно команд для генерации расписания (нужно минимум 2).")
                continue

            # Если количество команд нечетное, добавляем "выходной" (заглушку None)
            if num_teams % 2 != 0:
                teams.append(None)
                num_teams += 1

            rounds = num_teams - 1
            matches_per_round = num_teams // 2

            # Круговой алгоритм Бергера (Circular Method)
            for round_num in range(rounds):
                # Рассчитываем дату для каждого тура (например, каждую неделю)
                round_date = start_date + timedelta(weeks=round_num)
                
                for match_num in range(matches_per_round):
                    home = teams[match_num]
                    away = teams[num_teams - 1 - match_num]

                    # Если одна из команд None — это выходной тур для соперника, матч не создается
                    if home is not None and away is not None:
                        # Распределяем время внутри одного дня игр (10:00, 12:00 и т.д.)
                        match_time = round_date + timedelta(hours=(match_num * 2))
                        # Берем зал по очереди
                        assigned_hall = hall_ids[match_num % len(hall_ids)]

                        # Записываем сгенерированный матч в PostgreSQL
                        cursor.execute('''
                            INSERT INTO matches (match_date, team_home_id, team_away_id, hall_id)
                            VALUES (%s, %s, %s, %s);
                        ''', (match_time, home, away, assigned_hall))

            # Сдвигаем начало игр для следующего дивизиона на вечер или другой день
            start_date += timedelta(hours=4)

        conn.commit()
        print("=== КАРТА РАСПИСАНИЯ ПОЛНОСТЬЮ И УСПЕШНО ОБНОВЛЕНА ===")
    except Exception as e:
        print(f"Ошибка генерации в schedule.py: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    generate_schedule()
