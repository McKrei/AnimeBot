import aiohttp
import asyncio
from bs4 import BeautifulSoup as bs
from activate_anime_bot import db, cursor

async def get_page_data(url):
    async with aiohttp.request('GET', url) as resp:

        if resp.status == 200:
            html  = await resp.text()
            soup  = bs(html, 'lxml')
            blocs = soup.find_all('article', class_='story')

            for bloc in blocs:
                title = bloc.find('div', class_='story_h')
                el    = title.select_one('a')
                name  = el.text.strip().lower().translate(str.maketrans("'",' ','"'))
                url   = el['href'][22:]
                cat   = title.find_all('div', class_='lcol')[-1].text.strip()

                try:
                    year = int(
                        bloc.find('div', class_='xfinfodata').find('a').text
                        )

                except (AttributeError, ValueError):
                    year = 0

                result_data.append((name, cat, year, url))
        else: 
            print(resp.status)

        return result_data


async def load_site_data(pages):
    tasks = []
    for page in pages:
        url  = f'https://tr.anidub.com/page/{page}'
        task = asyncio.create_task(get_page_data(url))
        tasks.append(task)
    await asyncio.gather(*tasks)


async def parsing_anidub(loop, beginner, end_page):
    global result_data
    result_data = []
    pages_list  = list(range(beginner, end_page))
    loop.run_until_complete(load_site_data(pages_list))
    # return result_data
    cursor.executemany('INSERT INTO torrent (name, cat, year, url) VALUES(?, ?, ?, ?)', result_data)
    db.commit()
    





# data = []
# for i in range(1, 225, 25): # 225 кол-во страниц, 25 шаг, что бы было сложностей с сервером
#     data += parsing_anidub(i, i + 25)
#     break
# cursor.executemany('INSERT INTO torrent (name, cat, year, url) VALUES(?, ?, ?, ?)', data)
# db.commit()
# cursor.close()
# db.close()