import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from bank import genre_dict
import sqlite3
import datetime

'''
ua = UserAgent().random
all_urls = []  # Тут будут ссылки на страницы с аниме
anime_urls = []  # Тут будут ссылки в необработоном виде
args = []  # Массив с информацией по аниме
work_pages = 272 # кол-во страниц которе парсим
qs = 1 # Счетчик обработанных аниме
start_anime_id = 0


for number_page in range(work_pages, 0, -1): # Забираем ссылки на ание с сайта 
    url = f'https://v2.vost.pw/page/{number_page}/'

    response = requests.get(url, headers={'user-agent': ua})
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', {'id': 'dle-content'})
    anime_urls.append(container.find_all('div', {'class': 'shortstory'}))

for page in anime_urls: # приводим ссылки в нормальный вид
    for anime in page:
        url_a = anime.select_one('h2 a')['href']
        all_urls.append(url_a)


del anime_urls 
print('Все ссылки на Аниме собраны!')
'''


    # def select_url_dow(len_ep):
    #     number_ep = 0    
    #     star_url = 'https://v2.vost.pw/frame5.php?play='
    #     result_list = []

    #     try:
    #         for ur in len_ep:           
    #             try:
    #                 number_ep += 1
    #                 url_720p = url_480p = None
    #                 url = star_url + ur
    #                 response = requests.get(url, headers={'user-agent': ua})
    #                 html = response.text
    #                 soup = BeautifulSoup(html, 'lxml')

    #                 container = soup.find_all('a', target="_blank")
                    
    #                 for el in container:
    #                     if el.text == '480p (SD)': url_480p = el['href']                
    #                     elif el.text == '720p (HD)': url_720p = el['href']
                  
    #                 url_d = url.split('.pw')[1]     

    #                 cursor.execute(f'''
    #                 INSERT INTO episode_url 
    #                 (fk_anime_id, url_online_play, url_480, url_720, number_ep) 

    #                 VALUES
    #                 ('{start_anime_id}','{url_d}','{url_480p}','{url_720p}','{number_ep}');
    #                 ''')

    #             except Exception as ex:
    #                 print(ex, '\nВ ССЫЛКЕ НА ЗАГРУЗКУ: ', url)
    #     except (Error) as ex:
    #         print("Ошибка при работе с PostgreSQL\n", ex)
    #     return 'Серии записанны!'



def new_anime_db(url):
# for url in all_urls:
    with sqlite3.connect('anime.db') as db:
        cursor = db.cursor()
        try:
            # if start_anime_id %5 == 0:
            #     end = int(100-(1-(qs/(work_pages*10)))*100)
            #     print(f'Сбор данных завершен на {end}%')
            ua = UserAgent().random
            # qs += 1
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
                print('НОВАЯ ГРУППА')
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
            start_anime_id = int(cursor.fetchone()[0]) +1
            # start_anime_id += 1
            # data_update = 12
            # Записываем в табличку anime
            cursor.execute(f'''
                INSERT INTO anime VALUES (
                {start_anime_id}, '{name_ru}', '{name_en}', {episodes_came_out}, '{genre}', {rating},  
                {popularity}, '{description}', '{connection_anime}', '{anime_url}', 
                '{img_url}', {release}, {episodes_all}, datetime('now'), '{anime_type}');
                ''')

            # Записываем в табличку genre
            for el in genre.split(', '):
                genre_id = genre_dict.get(el)
                if genre_id:
                    cursor.execute(f'''
                    INSERT INTO anime_genre VALUES
                    ({start_anime_id}, {genre_id});
                    ''')
        
            # Записываем в табличку episode_url
            number_ep = 0
            for ep in list_ep:
                number_ep += 1
                if ep:
                    cursor.execute(f'''
                    INSERT INTO episode_url VALUES
                    ({ep}, {start_anime_id}, {number_ep});
                        ''')
            

            print(f'Добавил аниме {start_anime_id}: {name_ru}')
            db.commit()
            cursor.close()

        except (Exception) as ex:
            print("\n", ex,'\n', url,)




# print(new_anime_db('https://v2.vost.pw/tip/tv/7-naruto1.html'))
            

