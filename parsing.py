import datetime
from email import header

import re
import requests
import aiohttp
import asyncio

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from activate_anime_bot import db, cursor

from bank import srart_url_pleer, start_url, genre_dict, domen, srart_url_pleer_mirror


def get_rating_and_popular(soup):
	try:
		popularity = int(soup.find('span', {'style': 'font-size:11px; color:#000;'}).text.split(': ')[1][:-1])
		rating 	   = int(soup.find('li', {'class': 'current-rating'}).text) // 2
	except Exception as ex:
		popularity = rating = 0

	return popularity, rating


async def get_page_data(id, url):
	async with aiohttp.request('GET', url) as resp:
		if resp.status == 200:
			html = await resp.text()
			soup = BeautifulSoup(html, 'lxml')
			popularity, rating = get_rating_and_popular(soup)
			
			if popularity > 0:
				result_tuple = (popularity, rating, id)
				result_data.append(result_tuple)

		return result_data


async def load_site_data(url_list):
	tasks = []
	for id, url in url_list:
		task = asyncio.create_task(get_page_data(id, url))
		tasks.append(task)
	await asyncio.gather(*tasks)

def writing_popularity_rating(w_list):
		cursor.executemany(f'''
			UPDATE anime
			SET popularity = ?,
				rating 	   = ?,
				date_update_rating = datetime('now')
			WHERE anime_id = ?
			
		''', w_list)
		db.commit()


def update_popularity_rating():
	try: 
		global result_data
		result_data = []

		cursor.execute('''
			SELECT anime_id, anime_url
			FROM anime
			ORDER BY date_update_rating
			LIMIT 100
		''')
		url_tuple = tuple(cursor.fetchall())

		url_list = [[id, start_url + url] for id, url in url_tuple]
		
		asyncio.get_event_loop().run_until_complete(load_site_data(url_list))
		writing_popularity_rating(result_data)

		del result_data

	except Exception as ex:
		print('Ошибка update_popularity_rating\n', ex)


def pars_ep(list_url_ep):
	result = []
	ua = UserAgent().random

	for ep in list_url_ep:	 	
		url = srart_url_pleer + str(ep)
		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		url_list = [None, None, srart_url_pleer_mirror + str(ep)]
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
		popularity, rating = get_rating_and_popular(soup)

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
		anime_url = url.split(domen)[1]


		data_update = datetime.datetime.now()

		list_ep = re.findall(r'\d{9,}', str(soup.find_all('script')))
		if list_ep: 
			if episodes_came_out != len(list_ep):
				episodes_came_out = len(list_ep)
				if episodes_came_out > episodes_all:
					episodes_all = episodes_came_out

		cursor.execute(f'''
		SELECT MAX(anime_id)
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

		# Записываем группы 
		if connection_anime:
			group_id = checking_connect_anime(url, anime_id)
			db.commit()
			return group_id, anime_id, name_ru
		
		db.commit()
	except (Exception) as ex:
		print(f'new_anime_db = {url}\n{ex}')


def count_ep(a_url):
	'''
	Проверяем, наличие аниме в БД, возвращаем его ID, серии которые вышли, серии факт, всего серий. либо None
	'''
	cursor.execute(f'''
		SELECT anime_id, episodes_all
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
			cursor.execute(f'INSERT INTO anime_groups VALUES ({group_id[0]}, {number_anime}, {anime_id})')
			print(f'Добавил аниме в группу {group_id=}, {number_anime=}, {anime_id=}')
			db.commit()
			return group_id

	group_id = new_groups(result_list)
	return group_id


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
	return group_id


def check_update():
	ua = UserAgent().random
	anime_urls 			 = []
	all_urls			 = []
	update_anime_id_list = []
	new_anime_group		 = []

	# Собираем ссылки на последние 2-е страницы Аниме. Приводим их к норм виду. 
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
		result = count_ep(url.split(domen)[1])
		if not result:
			group_id = new_anime_db(url)
			new_anime_group.append(group_id)
			continue
		anime_id, episodes_all, fact_ep = result

		# Ищем ИД серий которые вышли по аниме 
		html = requests.get(url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		data = soup.find_all('script')
		for el in data:
			if el.text.strip()[:50].count('var data = ') > 0:
				list_ep = re.findall(r'\d{6,}', el.text)

		popularity, rating = get_rating_and_popular(soup)
		# Находим указанное количество серий. Если есть отличие, вносим изменение в БД
		try:
			element = soup.find('div', {'class': 'shortstoryContent'}).find_all('p')[3].text
			episodes_all_page = int(re.findall(r'\d+', element)[0])			
		except Exception:
			episodes_all_page = 0
		episodes_all = episodes_all_page if episodes_all_page > episodes_all else episodes_all

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
				SET episodes_came_out = {len(list_ep)}, 
					date_update = datetime('now'),
					episodes_all = {episodes_all},
					popularity 	= {popularity},
					rating = {rating}
				WHERE anime_id = {anime_id}
				''')
				if anime_id not in update_anime_id_list:
					update_anime_id_list.append(anime_id)
				print(f'add {ep = }, {anime_id = }, {n_ep = }')
				n_ep += 1
			except Exception as ex:
				print(f'check_update = {ep},{anime_id=} \n{ex}')
		db.commit()
	return set(update_anime_id_list), new_anime_group


# if __name__ == '__main__':
# 	now = datetime.datetime.now()
# 	list_ = []
# 	s = update_popularity_rating(list_)
# 	print(datetime.datetime.now() - now)