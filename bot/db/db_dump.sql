--
-- Файл сгенерирован с помощью SQLiteStudio v3.2.1 в Сб июн 5 18:47:45 2021
--
-- Использованная кодировка текста: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: payments
CREATE TABLE payments (user_id INTEGER PRIMARY KEY AUTOINCREMENT, code VARCHAR (255) NOT NULL UNIQUE);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
