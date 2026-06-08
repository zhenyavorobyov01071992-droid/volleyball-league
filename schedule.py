import psycopg2
from datetime import datetime, timedelta

def generate_and_save_schedule():
    # 1. Настройки подключения к вашей PostgreSQL
    DB_NAME = "volleyball_db"
    DB_USER = "postgres"        
    DB_PASSWORD = "375447340720"  # Замените на свой пароль от pgAdmin!
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

        # Начальная дата для проведения лиги (например, со следующего дня)
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
