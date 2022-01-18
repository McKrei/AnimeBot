import datetime

import re
import requests

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from activate_anime_bot import db, cursor

from bank import srart_url_pleer, start_url, genre_dict


def pars_ep(list_url_ep):
	result = []
	ua = UserAgent().random

	for ep in list_url_ep:	 	
		url = srart_url_pleer + str(ep)
		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		url_list = [None, None, url]
		container = soup.find_all('a', target="_blank")

		for el in container:
			if el.text == '480p (SD)': url_list[1] = el['href']                
			elif el.text == '720p (HD)': url_list[0] = el['href']
		result.append(url_list)
	if len(result) == 1: result = result[0]

	return result


def new_anime_db(url):
	'''
	ЗАПИСЫВАЕМ НОВЫЕ АНИМЕ В ДБ, получаем ссылку на аниме
	'''
	try:
		ua = UserAgent().random
		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')

		# Создаем element из которого будем извлекать name_ru, name_en, episodes_came_out
		element = soup.select_one('h1').text.strip().lower().translate(str.maketrans("'",' ','"')).split(' / ')   
		name_ru = element[0]
		element = element[1].split(' [')        
		name_en = element[0]
		element = element[1][:-1]
		try:
			if element == 'анонс':
				episodes_came_out = 0
			else:
				test = element.split()[0]
				if test[:2] == "1-":
					episodes_came_out = int(test[2:]) if test[-1] != '+' else int(test[2:-1])
				else:
					episodes_came_out = 1
		except Exception as ex:
			episodes_came_out = 0
			print(ex,'\nОшибка в episodes_came_outn\n',url)

		# Создаем element из которого будем извлекать: release episodes_all genre description
		element = soup.find('div', {'class': 'shortstoryContent'}).find_all('p')

		# Находим популярность и рейтинг
		try:
			popularity = int(soup.find('span', {'style': 'font-size:11px; color:#000;'}).text.split(': ')[1][:-1])
			rating = int(soup.find('li', {'class': 'current-rating'}).text) // 2
		except Exception as ex:
			popularity = rating = 0
			print('Ошибка в popularity и rating: ',url)

		# Находим тип
		anime_type = element[2].text.split('Тип: ')[1]

		# Находим дату релиза, проверка на INT
		try: 
			release = int(element[0].text.split()[2])
		except Exception as ex:
			release = 2000
			print('\nОшибка в release: ',url) 

		# Находим жанры
		genre = element[1].text[6:]

		# Находим кол-во эпизодов
		test = element[3].text.split()[2] 
		episodes_all = int(test) if test[-1] != '+' else int(test[:-1])

		# Находим Описание  
		for el in element:
			el = el.text
			if el.split()[0] == 'Описание:':
				description = el[10:].translate(str.maketrans("'",' ','"'))    
				break

		# Находим пересечения по Аниме            
		try:
			connection_anime = ' | '.join([el.text.split(' - ')[0] for el in\
			soup.find('div', {'class': 'text_spoiler'}).find_all('li')])
		except Exception:
			connection_anime = connect = None

		# Находим url на картинку и аниме без домена 
		img_url = soup.find('img', class_='imgRadius')['src']
		anime_url = url.split('.pw')[1]


		data_update = datetime.datetime.now()

		list_ep = re.findall(r'\d{9,}', str(soup.find_all('script')))
		if list_ep: 
			if episodes_came_out != len(list_ep):
				episodes_came_out = len(list_ep)
				if episodes_came_out > episodes_all:
					episodes_all = episodes_came_out

		cursor.execute(f'''
		SELECT count(anime_id)
		FROM anime 
		''')
		anime_id = int(cursor.fetchone()[0]) +1


		# Записываем в табличку anime
		cursor.execute(f'''
			INSERT INTO anime VALUES (
			{anime_id}, '{name_ru}', '{name_en}', {episodes_came_out}, '{genre}', {rating},  
			{popularity}, '{description}', '{connection_anime}', '{anime_url}', 
			'{img_url}', {release}, {episodes_all}, datetime('now'), '{anime_type}');
			''')

		# Записываем в табличку genre
		for el in genre.split(', '):
			genre_id = genre_dict.get(el)
			if genre_id:
				cursor.execute(f'''
				INSERT INTO anime_genre VALUES
				({anime_id}, {genre_id});
				''')

		# Записываем в табличку episode_url
		number_ep = 0
		for ep in list_ep:
			number_ep += 1
			if ep:
				cursor.execute(f'''
				INSERT INTO episode_url VALUES
				({ep}, {anime_id}, {number_ep});
				''')
		
		print(f'Добавил аниме {anime_id=}: {name_ru=}')
		db.commit()

		# Записываем группы :-) 
		if connection_anime:
			checking_connect_anime(url, anime_id)
		db.commit()


	except (Exception) as ex:
		print(f'new_anime_db = {url}\n{ex}')


def count_ep(a_url):
	'''
	Проверяем, наличие аниме в БД, возвращаем его ID, серии которые вышли, серии факт. либо None
	'''
	cursor.execute(f'''
		SELECT anime_id, episodes_came_out
		FROM anime 
		WHERE anime_url = '{a_url}'
		''')
	result = cursor.fetchone()
	if not result: return None
	cursor.execute(f'''
		SELECT count(number_ep)
		FROM episode_url 
		WHERE anime_id = {result[0]}
		''')
	n_coun = cursor.fetchone()[0]
	return *result, n_coun


def checking_connect_anime(url_anime, anime_id):
	# Собираем связанные аниме 
	result_list = []
	ua = UserAgent().random
	html = requests.get(url_anime, headers={'user-agent':ua}).text
	soup = BeautifulSoup(html, 'lxml')
	container = soup.find('div', {'class': 'text_spoiler'}).find_all('a')
	for el in container:
		result_list.append(el['href'])

	for u in result_list:
		cursor.execute(f'''
			SELECT group_id
			FROM anime
			JOIN anime_groups USING (anime_id)
			WHERE anime_url LIKE '%{u.split('/')[-1][:-5]}%'
			''')
		group_id = cursor.fetchone()
		if group_id:
			cursor.execute(f'''
				SELECT max(number_anime)
				FROM anime_groups
				WHERE group_id = {group_id[0]}
				''')

			number_anime = cursor.fetchone()[0] + 1
			cursor.execute(f'INSERT INTO anime_groups VALUES ({group_id}, {number_anime}, {anime_id})')
			print(f'Добавил аниме в группу {group_id=}, {number_anime=}, {anime_id=}')
			db.commit()
			return

	new_groups(result_list)
	return


def new_groups(url_list):
	cursor.execute(f'''
			SELECT max(group_id)
			FROM anime_groups
			''')
	group_id = cursor.fetchone()[0] + 1
	number_anime = 1

	for url in url_list:
		cursor.execute(f'''
			SELECT anime_id
			FROM anime
			WHERE anime_url LIKE '%{url.split('/')[-1][:-5]}%'
			''')	
		anime_id = cursor.fetchone()
		if anime_id:
			try:
				cursor.execute(f'INSERT INTO anime_groups VALUES ({group_id}, {number_anime}, {anime_id[0]})')
				print(f'Добавил группу и аниме туда {group_id=}, {number_anime=}, {anime_id=}')
				number_anime += 1
			except Exception as ex:
				print('Попытка добавить 2-й раз аниме\n', ex)
		else: print('Нету в базе АНИМЕ: ', url)
	print('Добавил группу:', group_id)				
	db.commit()
	return

def check_update():
	ua = UserAgent().random
	anime_urls = []
	all_urls = []
	update_anime_id_list = []

	# Собираем ссылки на последние 4-ри страницы Аниме. Приводим их к норм виду. 
	for p in range(1, 3): 
		url = f'{start_url}page/{p}/'
		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		container = soup.find('div', {'id': 'dle-content'})
		anime_urls.append(container.find_all('div', {'class': 'shortstory'}))

	for page in anime_urls: 
		for anime in page:
			all_urls.append(anime.select_one('h2 a')['href'])


	for url in all_urls:
		result = count_ep(url.split('.pw')[1])
		if not result:
			new_anime_db(url)
			continue		 		
		anime_id, out_anime, fact_ep = result

		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		data = soup.find_all('script')
		for el in data:
			if el.text.strip()[:50].count('var data = ') > 0:
				list_ep = re.findall(r'\d{6,}', el.text)

		if len(set(list_ep)) == fact_ep:
			break
		n_ep = fact_ep + 1
		list_ep = list(list_ep)
		for ep in list_ep[fact_ep:]:
			try: 
				cursor.execute(f'''
				INSERT INTO episode_url VALUES
				({ep}, {anime_id}, {n_ep});
				''')
				cursor.execute(f'''
				UPDATE anime
				SET episodes_came_out = {len(list_ep)}, date_update = datetime('now')
				WHERE anime_id = {anime_id}
				''')
				if anime_id not in update_anime_id_list:
					update_anime_id_list.append(anime_id)
				print(f'add {ep = }, {anime_id = }, {n_ep = }')
				n_ep += 1
			except Exception as ex:
				print(f'check_update = {ep},{anime_id=} \n{ex}')
		db.commit()
	return set(update_anime_id_list)


if __name__ == '__main__':
	data = check_update()