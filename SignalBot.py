import subprocess
import time
import logging

# Настраиваем логирование в файл
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_server():
    server = None
    process_tasks = None
    try:
        # Запускаем сервер Django
        logging.info("Запуск сервера Django...")
        server = subprocess.Popen(["python", "manage.py", "runserver"])

        # Ждём немного, чтобы убедиться, что сервер запущен
        time.sleep(2)

        # Запускаем процесс фоновых задач
        logging.info("Запуск фоновых задач process_tasks...")
        process_tasks = subprocess.Popen(["python", "manage.py", "process_tasks"])

        # Ожидаем завершения обоих процессов
        server.wait()
        process_tasks.wait()
    except KeyboardInterrupt:
        logging.info("Остановка серверов...")
        if server:
            server.terminate()
        if process_tasks:
            process_tasks.terminate()
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        # Завершаем процессы, если они всё ещё работают
        if server and server.poll() is None:
            server.terminate()
            logging.info("Сервер Django остановлен.")
        if process_tasks and process_tasks.poll() is None:
            process_tasks.terminate()
            logging.info("Процесс фоновых задач process_tasks остановлен.")

if __name__ == "__main__":
    run_server()
