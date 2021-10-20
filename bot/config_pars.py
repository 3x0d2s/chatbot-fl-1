# -*- coding: utf8 -*-
#
import configparser
import os
import pathlib


def create_config(path_file):
    """Создаёт файл конфигурации."""
    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "amount_1", "39000")
    config.set("Settings", "amount_2", "69000")
    config.set("Settings", "amount_3", "129000")
    # Сохраняем конфиг. файл.
    with open(path_file, "w") as config_file:
        config.write(config_file)


def get_amount_config(path_file):
    """Парсит конфигурацию и получаем текущий идентификатор недели."""
    if not os.path.exists(path_file):
        create_config(path_file)
    config = configparser.ConfigParser()
    config.read(path_file)
    # Читаем значения из конфиг. файла.
    return [
        {"id": 1, "amount": config.get("Settings", "amount_1")},
        {"id": 2, "amount": config.get("Settings", "amount_2")},
        {"id": 3, "amount": config.get("Settings", "amount_3")},
    ]


def change_amount_config(path_file, product_id, value):
    """Сменяет текущий идентификатор недели."""
    if not os.path.exists(path_file):
        create_config(path_file)
    config = configparser.ConfigParser()
    config.read(path_file)
    # Меняем значения из конфиг. файла.
    config.set("Settings", f"amount_{product_id}", value)
    # Вносим изменения в конфиг. файл.
    with open(path_file, "w") as config_file:
        config.write(config_file)
