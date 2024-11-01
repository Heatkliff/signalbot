import subprocess
import logging

# Настраиваем логирование в файл
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_server():
    try:
        # Запускаем сервер Django
        logging.info("Запуск сервера Django...")
        print("Запуск сервера Django...")
        server = subprocess.Popen(["python", "manage.py", "runserver"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Запускаем процесс фоновых задач
        print("Запуск фоновых задач process_tasks...")
        logging.info("Запуск фоновых задач process_tasks...")
        process_tasks = subprocess.Popen(["python", "manage.py", "process_tasks"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        print("Сервер Django и процесс process_tasks успешно запущены на фоне.")
        logging.info("Сервер Django и процесс process_tasks успешно запущены на фоне.")
    except Exception as e:
        print(f"Произошла ошибка при запуске серверов: {e}")
        logging.error(f"Произошла ошибка при запуске серверов: {e}")

if __name__ == "__main__":
    run_server()
