import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sqlite3

ua = UserAgent().random
all_urls = []
strat_url = 'https://v2.vost.pw/'
# Выдача связанных аниме:
# Нужно запарсить снова сайт создав таблицу с FK anime_id/ Уникальным считать url


def find_connection_anime(url_anime):
	result_list = []
	url = strat_url+url_anime
	html = requests.get(url, headers={'user-agent':ua}).text
	soup = BeautifulSoup(html, 'lxml')
	container = soup.find('div', {'class': 'text_spoiler'}).find_all('a')
	for el in container:
		result_list.append(el['href'])
	return result_list


def recording_connection_anime_in_db():
	group_id = 1
	with sqlite3.connect('anime.db') as db:
		cursor = db.cursor()
		cursor.execute(f'''
			select anime_id, anime_url
			from anime
			where connection_anime != 'None' and connection_anime != ''
			''')
		all_url = cursor.fetchall()

		for anime in all_url:
			cursor.execute(f'''
				SELECT COUNT(*)
				FROM anime_groups
				WHERE anime_id = {anime[0]}
				''')
			if int(cursor.fetchone()[0]) == 0:
				connect = find_connection_anime(anime[1])
				if connect:
					number_anime = 1
					for url_con in connect:
						cursor.execute(f'''
							SELECT anime_id
							FROM anime
							WHERE anime_url LIKE '%{url_con.split('/')[-1][:-5]}%'
							''')	
						a_id = cursor.fetchone()						
						if a_id:
							try:
								cursor.execute(f'INSERT INTO anime_groups VALUES ({group_id}, {number_anime}, {a_id[0]})')
								number_anime += 1
							except Exception as ex:
								print('Попытка добавить 2-й раз аниме\n', ex)
						else: print('Нету в базе АНИМЕ: ', url_con)
					print('Добавил группу:', group_id)
					group_id += 1					
					db.commit()

		print('Работа завершил')
		cursor.close()

recording_connection_anime_in_db()
