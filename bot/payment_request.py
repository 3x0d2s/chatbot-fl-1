import sqlite3


class paymentDirect:
    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def get_payment_code(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT code FROM `payments` WHERE `user_id` = ?", (str(user_id),))
            return self.cursor.fetchone()

    def add_payment_to_stack(self, user_id, code):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `payments` (`user_id`, 'code') VALUES(?,?)", (user_id, code))

    def delete_payment(self, user_id):
        with self.connection:
            self.cursor.execute(
                "DELETE FROM `payments` WHERE `user_id` = ?", (user_id,))

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
