# -*- coding: utf8 -*-
#
import configparser
import os
import pathlib


def create_config(path_file):
    """Создаёт файл конфигурации."""
    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "amount", "59000")
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
    return config.get("Settings", "amount")


def change_amount_config(path_file, value):
    """Сменяет текущий идентификатор недели."""
    if not os.path.exists(path_file):
        create_config(path_file)
    config = configparser.ConfigParser()
    config.read(path_file)
    # Меняем значения из конфиг. файла.
    config.set("Settings", "amount", value)
    # Вносим изменения в конфиг. файл.
    with open(path_file, "w") as config_file:
        config.write(config_file)
