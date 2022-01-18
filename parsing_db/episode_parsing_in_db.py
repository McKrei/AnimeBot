import sqlite3

import re
import requests

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

start_url = 'https://v2.vost.pw/'


with sqlite3.connect('anime.db') as db:
	cursor = db.cursor()
	cursor.execute(f'''
		SELECT anime_id, anime_url, episodes_came_out
		FROM anime
		''')
	anime_list = cursor.fetchall()
	ua = UserAgent().random
	for anime_id, anime_url, episodes_came_out in anime_list:
		number_ep = 1
		html = requests.get(start_url+anime_url, headers={'user-agent': ua}).text
		soup = BeautifulSoup(html, 'lxml')
		data = soup.find_all('script')	
		for el in data:
			if el.text.strip()[:50].count('var data = ') > 0:
				list_ep = re.findall(r'\d{6,}', el.text)
				for ep in list_ep:
					try:
						cursor.execute(f'''
							INSERT INTO episode_url VALUES
							({ep}, {anime_id}, {number_ep});
							''')
						number_ep += 1
					except Exception as ex:
						print(f'{anime_id=} {ep=}\n{ex}')

				cursor.execute(f'''
					SELECT COUNT(number_ep)
					FROM episode_url
					WHERE anime_id = {anime_id}
					''')
				print(f'{anime_id=} эпизоды добавил')
				count_ep = cursor.fetchone()[0]
				if count_ep != episodes_came_out:
					cursor.execute(f'''
					UPDATE anime
					SET episodes_came_out = {count_ep}
					WHERE anime_id = {anime_id}
					''')
					print(f'{anime_id=}:Было {episodes_came_out}, Стало {count_ep}')
		db.commit()
	cursor.close()



# data = soup.find_all('script')
# for i, el in enumerate(data):
# 	if el.text.strip()[:50].count('var data = ') > 0:
# 		s = el
# 		print(i, el.text.strip()[:50])
# 		list_ep_2 = re.findall(r'\d{6,}', el.text)
# 		print(len(list_ep_2))
# 		print(el.text.count(' серия"'))

# print(len(list_ep))
