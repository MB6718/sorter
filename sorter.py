# -*- coding: utf-8 -*- 
# ##############################################################################
#  mp3Sorter v0.1                                             [Author: Max Bee]
# ##############################################################################
#  mp3Sorter - консольное (CLI) приложение для сортировки музыкальных файлов
#  по исполнителям и альбомам:
#  * Программа анализирует файлы в исходной директории, считывает ID3-теги,
#    извлекает из них информацию о названии трека, исполнителе и альбоме.
#  * Группирует файлы (перемещает, не копирует) по исполнителям и альбомам,
#     так, чтобы получить структуру директорий:
#      <директория назначения>/<исполнитель>/<альбом>/<имя файла>.mp3
#  * Переименовывает файлы по схеме:
#     <название трека> - <исполнитель> - <альбом>.mp3
#  * Если в тегах нет информации о названии трека, использует
#    оригинальное имя файла.
#  * Если в тегах нет информации об исполнителе или альбоме, пропускает файл,
#    оставляя его без изменений в исходной директории.
#  * Если в целевой директории файл с таким названием уже существует,
#    заменяет его.
#  * Файлы ищет только в исходной директории (поддиректории не анализирует).
#  * Программа поддерживает только ID3v2 теги (ID3v1 - устаревший формат).
#  * Программа принимает 3 ключа командной строки:
#    --help - вывести справочное сообщение;
#    -s | --src-dir - исходная директория, по умолчанию директория в которой
#                     запущен скрипт;
#    -d | --dst-dir - целевая директория, по умолчанию директория в которой
#                     запущен скрипт;
#  * В ходе работы программа выводит в консоль лог действий в виде:
#     <путь до исходного файла> -> <путь до файла результата>
#  * Кросс-платформенная работа с файловой системой
# ##############################################################################

# ##############################################################################
# Секция импорта сторонних пакетов
# ##############################################################################
import os
import click
import eyed3

# ##############################################################################
# Имя функции: main
# Описание: Главная функция программы. Обрабатываем входящие аргументы(опции)
#           командной строки с помощью пакета Click.
# Вход: Аргументы(опции) командной строки
# Выход: Результат работы программы
# ##############################################################################
@click.command()
@click.option('-s', '--src-dir',
			  type=click.Path(),
			  help='Source directory.',
			  default=os.getcwd())
@click.option('-d', '--dst-dir',
			  type=click.Path(),
			  help='Destination directory.',
			  default=os.getcwd())
def main(src_dir, dst_dir):

	"""Final task "Sorter of *.mp3 files by ID3 tags" [Author: Max Bee]"""

	# Проверяем, что путь 'src_dir' существует в ФС
	source_path_exists = os.path.exists(src_dir)
	if source_path_exists:
		# если путь True, получаем список файлов в нём
		files_list = get_files_list(src_dir)
		if files_list:
			# если файлы в списке есть, обрабатываем каждый из них
			for file_name in files_list:
				file_handler(dst_dir, src_dir, file_name)
			print('Done')
		else:
			print('ERROR: There are no *.mp3 files on the specified path')
	else:
		print('ERROR: Source directory not exist')

# ##############################################################################
# Имя функции: file_handler
# Описание: Обработчик файлов, в соответствии с условием программы
# Вход: destination_dir - путь источник (откуда)
#       source_dir - путь приёмник (куда)
#       file_name - имя файла
# Выход: Создание цепи директорий, переименование и перемещение файла
# ##############################################################################	
def file_handler(destination_dir, source_dir, file_name):
	"""
	Имя функции: file_handler
	Описание: Обработчик файлов, в соответствии с условием программы
	Вход: destination_dir - путь источник (откуда)
		  source_dir - путь приёмник (куда)
		  file_name - имя файла
	Выход: Создание цепи директорий, переименование и перемещение файла
	"""
	# соединяем пути с учетом правил ОС и получаем сведения об аудио файле
	artist, title, album = get_file_tags(os.path.join(source_dir, file_name))
	if artist == None or album == None:
		pass
	else:
		new_file_name = file_name
		if title != None:
			new_file_name = f'{title} - {artist} - {album}.mp3'
		# формируем путь с учетом правил ОС
		destination_path = os.path.join(destination_dir, artist, album)
		# Создаём цепь директорий по указанному пути
		destination_dir_maked = make_dest_dir(destination_path)
		if destination_dir_maked:
			# если цепь создана, перемещаем файл по пути
			result = move_file(source_dir, destination_path, file_name, \
							   new_file_name)
			if not result:
				print(f'ERROR: It is not possible to move the {file_name} file',
					   'it may be write-protected, check this and try again')
		else:
			print('ERROR: Unable to create path, no permissions, \
			       check this and try again')

# ##############################################################################
# Имя функции: move_file
# Описание: Переименовывает и перемещает файл из пути источника в путь приёмника
#           (!) Функция замещает файл, если он существует по пути приёмника
# Вход: source_path - путь источник (откуда)
#       destination_path - путь приёмник (куда)
#       file_name - имя файла
#       new_file_name - новое имя файла
# Выход: Результат по переименованию и перемещению файла
#        булево значение:
#        true - файл успешно переименован и перемещён,
#        false - ошибка переименования и перемещения
# ##############################################################################
def move_file(source_path, destination_path, file_name, new_file_name):
	"""
	Имя функции: move_file
	Описание: Переименовывает и перемещает файл из пути источника в путь приёмника
	          (!) Функция замещает файл, если он существует по пути приёмника
	Вход: source_path - путь источник (откуда)
	      destination_path - путь приёмник (куда)
	      file_name - имя файла
	      new_file_name - новое имя файла
	Выход: Результат по переименованию и перемещению файла
	       булево значение:
	       true - файл успешно переименован и перемещён,
	       false - ошибка переименования и перемещения
	"""
	path_from = os.path.join(source_path, file_name)
	path_to = os.path.join(destination_path, new_file_name)
	try:
		# проверяем, существует ли по пути файл с таким же именем
		if os.path.isfile(path_to):
			# удаляем его
			os.remove(path_to)
		# переименовываем и перемещаем файл
		os.rename(path_from, path_to)
	except:
		return False
	else:
		# если успешно, отображаем информацию
		show_info(path_from, path_to)
		return True

# ##############################################################################
# Имя функции: show_info
# Описание: Выводим в STDOUT информационную строку о перемещении файла из
#           директории источника в директорию приёмника
# Вход: path_from - путь источник с именем файла
#       path_to - путь приёмник с именем файла
# Выход: печать в STDOUT
# ##############################################################################
def show_info(path_from, path_to):
	"""
	Имя функции: show_info
	Описание: Выводим в STDOUT информационную строку о перемещении файла из
	          директории источника в директорию приёмника
	Вход: path_from - путь источник с именем файла
	      path_to - путь приёмник с именем файла
	Выход: печать в STDOUT
	"""
	# "сворачиваем" путь, если он ведёт к текущему(рабочему) каталогу
	path_from = path_from.replace(os.getcwd(), '')
	path_to = path_to.replace(os.getcwd(), '')
	# выводим на экран информационную строку
	print(f'{path_from} > {path_to}')

# ##############################################################################
# Имя функции: make_dest_dir
# Описание: Создаёт цепь директорий (путь)
# Вход: destination_path - желаемый путь
# Выход: Результат работы функции - созданная цепь директорий
#        булево значение:
#        true - всё создано успешно,
#        false - ошибка создания цепи директорий
# ##############################################################################	
def make_dest_dir(destination_path):
	"""
	Имя функции: make_dest_dir
	Описание: Создаёт цепь директорий (путь)
	Вход: destination_path - желаемый путь
	Выход: Результат работы функции - созданная цепь директорий
	       булево значение:
	       true - всё создано успешно,
	       false - ошибка создания цепи директорий
	"""
	# проверяем, существует ли указанный путь
	destination_path_exists = os.path.exists(destination_path)
	if destination_path_exists:
		# Проверим, что у текущего пользователя есть права на запись по пути
		write_permission = os.access(destination_path, mode=os.W_OK)
		if not write_permission:
			return False
	else:
		# Создаём каталоги по указанному пути
		try:
			os.makedirs(destination_path, mode=0o777, exist_ok=True)
		except:
			return False
	return True

# ##############################################################################
# Имя функции: get_file_tags
# Описание: Извлекает информацию из ID3-тегов аудио-файла формата *.mp3
#           с использованием пакета eyeD3
# Вход: file_name - путь с именем файла
# Выход: список tags, содержащий упакованные переменные artist, title, album
# ##############################################################################
def get_file_tags(file_name):
	"""
	Имя функции: get_file_tags
	Описание: Извлекает информацию из ID3-тегов аудио-файла формата *.mp3
	          с использованием пакета eyeD3
	Вход: file_name - путь с именем файла
	Выход: список tags, содержащий упакованные переменные artist, title, album
	"""
	# получаем из файла ID3 тэги
	mp3_file = eyed3.load(file_name)
	try:
		tags = [mp3_file.tag.artist, mp3_file.tag.title, mp3_file.tag.album]
	except AttributeError:
		tags = [None, None, None]
	for i, tag in enumerate(tags):
		if tag != None:
			tags[i] = tag.strip()
	return tags

# ##############################################################################
# Имя функции: get_files_list
# Описание: Получаем отфильтрованный по маске(расширению) список файлов,
#           находящихся в указанной директории
# Вход: directory - путь до директории источника
# Выход: список типа list() с именами файлов
# ##############################################################################
def get_files_list(directory):
	"""
	Имя функции: get_files_list
	Описание: Получаем отфильтрованный по маске(расширению) список файлов,
	          находящихся в указанной директории
	Вход: directory - путь до директории источника
	Выход: список типа list() с именами файлов
	"""
	# Получаем список файлов в переменную files
	files = os.listdir(directory)
	# Фильтруем список по маске '.mp3'
	return list(filter(lambda x: x.endswith('.mp3'), files))

# ##############################################################################
# Точка входа в программу
# ##############################################################################
if __name__ == '__main__':
	main()
