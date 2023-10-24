from manager import DbManager

if __name__ == '__main__':
    # Инициализация бд, обновление файлов
    db_manager = DbManager()
    print(db_manager.get_days_info('09', '2023'))
    print(db_manager.get_files_info())
