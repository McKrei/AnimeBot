

	
sorting_list = ('Новые', 'Популярные', 'Высший рейтинг', 'Высший_рейтинг', 'Обновления')

name_torrent_list = [
	'Torrent',
	'Торрент',
	'торент'
]

help_text = f'''
Кнопка *"Похожие"* - подбирает рекомендации по конкретному аниме, 
Работает только с аниме *до 2020* года!
Поиск торрента слово {name_torrent_list} *через пробел* название аниме!
*"торрент наруто"*
'''

sorting_dict = {'Новые': 'date_update',
				'Популярные': 'popularity',
				'Высший рейтинг': 'rating',
				'Высший_рейтинг': 'rating',
				'Обновления': 'release'}

# Оригинал
start_url = 'https://animevost.org/'
srart_url_pleer = 'https://animevost.org//frame5.php?play='
domen = '.org'

# Зеркало
# start_url = 'https://v2.vost.pw/'
srart_url_pleer_mirror = 'https://v2.vost.pw///frame5.php?play='
# domen = '.pw'


ru_alphabet = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')


genre ='''Боевые искусства
Война
Драма
Детектив
История
Комедия
Меха
Мистика
Махо-сёдзё
Музыкальный
Повседневность
Приключения
Пародия
Романтика
Сёнэн
Сёдзё
Спорт
Сказка
Сёдзё-ай
Сёнэн-ай
Самураи
Триллер
Ужасы
Фантастика
Фэнтези
Школа
Этти'''

genre_dict = {el : i+1 for i, el in enumerate(genre.split('\n'))}