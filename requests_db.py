from bank import ru_alphabet, sorting_dict, genre_dict
from parsing import pars_ep
from activate_anime_bot import db, cursor
import asyncio



def find_name(name, offset=0):
    offset *= 5
    left_count = 0
    name = name.translate(str.maketrans("'", ' ', '"')).lower()
    where_lok = 'name_ru'
    if ru_alphabet.isdisjoint(name): where_lok = 'name_en'
    cursor.execute(f'''
        SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
        FROM anime
        WHERE {where_lok} LIKE '%{name}%'
        ORDER BY date_update DESC, anime_id ASC
        LIMIT  5
        OFFSET {offset}
        ''')

    result = list(cursor.fetchmany(5))

    if len(result) == 0:
        cursor.execute(f'''
            SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
            FROM anime
            WHERE description LIKE '%{name}%'
            ORDER BY date_update DESC, anime_id ASC
            LIMIT  5
            OFFSET {offset}
            ''')
        result = list(cursor.fetchmany(5))

    else: 
        cursor.execute(f'''
            SELECT COUNT(*)
            FROM anime
            WHERE {where_lok} LIKE '%{name}%'
            ''')    

        left_count = int(cursor.fetchone()[0]) - (offset + len(result))
    return result, left_count

def find_description(anime_id):
        cursor.execute(f'''
            SELECT name_ru, name_en, description
            FROM anime
            WHERE anime_id = {anime_id}
            ''')      
        return cursor.fetchone()


def find_episode(anime_id, number_ep=1):
    try:
        cursor.execute(f'''
            SELECT episodes_all, name_ru, number_ep, episode_id, episodes_came_out, anime_id
            FROM anime
            JOIN episode_url USING(anime_id)
            WHERE anime_id = {anime_id} AND number_ep = {number_ep}
            ''')    

        result = cursor.fetchone()
        return list(result) + pars_ep([result[3]])

    except (Exception) as ex:          
        print(ex,'\n?????? ?????????????? find_episode',anime_id, number_ep)
        return '???????????? ?? ????'



def find_favorit(user_id, offset=0, finishen=0):

    if finishen == 0:
        where = f'user_id = {user_id} AND favorit = 1 AND finished = 0'
    else:
        where = f'user_id = {user_id} AND finished = 1'

    offset *= 5

    cursor.execute(f'''
        SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
        FROM users
        JOIN anime USING (anime_id)
        WHERE {where}
        LIMIT 5
        OFFSET {offset}
        ''')

    result = list(cursor.fetchmany(5))

    cursor.execute(f'''
        SELECT COUNT(*)
        FROM users
        WHERE {where}
        ''')

    left_count = int(cursor.fetchone()[0]) - (offset + len(result))
    if left_count <= 0: left_count = 0
    return result, left_count


def find_recommendation(anime_id, offset=0):
    offset *= 5

    if anime_id:
        cursor.execute(f'''
            SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, anime.rating, popularity, anime.anime_id, type, connection_anime
            FROM recommendation
            JOIN anime
                ON recommendation.rec_anime_id = anime.anime_id
            WHERE recommendation.anime_id = {anime_id}
            LIMIT 20
            OFFSET {offset}
            ''')

        result = list(cursor.fetchmany(5))

    if not anime_id or not result:
        cursor.execute(f'''
            SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, anime.rating, popularity, anime.anime_id, type, connection_anime, count(*) as count
            FROM recommendation
            JOIN anime 
                ON recommendation.rec_anime_id = anime.anime_id
            GROUP BY rec_anime_id
            ORDER BY count DESC
            LIMIT 20
            OFFSET {offset}
        ''')
        result = list(cursor.fetchmany(5))


    left_count = 15 - offset
    if left_count <= 0: left_count = 0
    return result, left_count



def find_anime(anime_id):
    cursor.execute(f'''
        SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
        FROM anime
        WHERE anime_id = {anime_id}
        ''')       
    return cursor.fetchall()


def find_genre(genre, offset=0):
    offset *= 5
    genre_id = genre_dict.get(genre)
    cursor.execute(f'''
        SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
        FROM anime_genre
        JOIN anime USING(anime_id)
        WHERE genre_id == {genre_id}
        ORDER BY date_update DESC, anime_id ASC
        LIMIT 5
        OFFSET {offset}
        ''')
    result = list(cursor.fetchmany(5))

    cursor.execute(f'''
        SELECT COUNT(*)
        FROM anime_genre
        WHERE genre_id = {genre_id}
        ''')

    left_count = int(cursor.fetchone()[0]) - (offset + len(result))
    if left_count <= 0: left_count = 0
    return result, left_count


def find_sort(sort, offset=0):
    offset *= 5
    sort = sorting_dict.get(sort)
    cursor.execute(f'''
        SELECT name_ru, img_url, release, episodes_came_out, episodes_all, genre, rating, popularity, anime_id, type, connection_anime
        FROM anime
        ORDER BY {sort} DESC, date_update DESC, anime_id ASC
        LIMIT  5
        OFFSET {offset}
        ''')
    result = list(cursor.fetchmany(5))

    cursor.execute(f'''
        SELECT COUNT(anime_id)
        FROM anime          
        ''')

    left_count = int(cursor.fetchone()[0]) - (offset + len(result))
    if left_count <= 0: left_count = 0
    return result, left_count


def check_favorites(anime_id, user_id):
    try:
        cursor.execute(f'''
            SELECT favorit, anime_id
            FROM users
            WHERE anime_id = {anime_id} AND user_id = {user_id}
            ''')
        result = cursor.fetchone()

        if not result:
            cursor.execute(f'''
                INSERT INTO users (user_id, anime_id, favorit)
                VALUES ({user_id}, {anime_id}, 1)
                ''')

        elif result[0] == 1: 
            cursor.execute(f'''
                UPDATE users 
                SET favorit = 0
                WHERE anime_id = {anime_id} AND user_id = {user_id}
                ''')
            db.commit()
            return False

        else: 
            cursor.execute(f'''
                UPDATE users 
                SET favorit = 1
                WHERE anime_id = {anime_id} AND user_id = {user_id}
                ''')

        db.commit()
        return True

    except Exception as ex:
        print('???????????? ?? check_favorites\n',ex)

def check_episode(anime_id, user_id):
    try:
        cursor.execute(f'''
            SELECT episode_number, favorit
            FROM users
            WHERE anime_id = {anime_id} AND user_id = {user_id}
            ''')
        result = cursor.fetchone()

        if not result:
            cursor.execute(f'''
                INSERT INTO users (user_id, anime_id, episode_number)
                VALUES ({user_id}, {anime_id}, {1})
                ''')
            db.commit()
            return 1

        elif not result[0]:
            cursor.execute(f'''
                UPDATE users 
                SET episode_number = {1}
                WHERE anime_id = {anime_id} AND user_id = {user_id}
                ''')
            db.commit()
            return 1

        else: return int(result[0])

    except Exception as ex:
        print('???????????? ?? check_favorites\n',ex)


def save_user_ep(anime_id, user_id, epis, fin_ep):
    try:
        cursor.execute(f'''
            UPDATE users 
            SET episode_number = {epis},
                finished = {fin_ep}
            WHERE anime_id = {anime_id} AND user_id = {user_id} 
            ''')
        db.commit()

    except Exception as ex:
        print('???????????? ?? save_user_ep\n',ex)


# ???????????? ???? ?????? ???????????? ?? ??????????
def find_all_season(anime_id, group_id=None):

    if not group_id:
        cursor.execute(f'''
            SELECT group_id 
            FROM anime_groups 
            WHERE anime_id = {anime_id}
            ''')
        group_id = cursor.fetchone()[0]

    cursor.execute(f'''
        SELECT name_ru, anime_id
        FROM anime_groups 
        JOIN anime USING(anime_id)
        WHERE group_id = {group_id}
        ORDER BY number_anime ASC
        ''')
    return cursor.fetchall()


# ???????????? ???? ???????????? ???????????? ?? ?????????????? ?????????? ?? ??????????????????
def user_search(anime_id):
    cursor.execute(f'''
        SELECT user_id
        FROM users
        WHERE anime_id = {anime_id} AND favorit = 1
        ''')
    return cursor.fetchall()

# ?????????? ???????????????????? ?? ????????????????
async def torrent_search(name):
    cursor.execute(f'''
        SELECT year, name, cat, url
        FROM torrent
        WHERE name LIKE '%{name}%'
        ORDER BY year DESC
        ''')
    
    return cursor.fetchall()



if __name__ == '__main__':
    print(torrent_search('????????????'))

