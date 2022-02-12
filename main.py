import asyncio
from random import randint
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import requests_db
import markups as nav

from activate_anime_bot import token
from parsing import check_update
from bank import genre_dict, sorting_list, start_url


# Активация бота
bot = Bot(token=token)
dp = Dispatcher(bot)


# Ловим старт и help
@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await bot.send_message(message.from_user.id, 'Привет {0.first_name}'.format(message.from_user), \
                           reply_markup=nav.main_menu)
    # Ответ на help
    if message.text == '/help':
        await bot.send_message(message.from_user.id, 'Сам разбирайся, для кого я создал столь удобный интерфейс!')


# Основное меню
@dp.message_handler(Text(equals='Меню', ignore_case=True))
async def catching_menu(message: types.Message):
    await bot.send_message(message.from_user.id, 'Меню', reply_markup=nav.main_menu)


# Меню Сортировки
@dp.message_handler(Text(equals='Сортировка', ignore_case=True))
async def catching_sorting(message: types.Message):
    await bot.send_message(message.from_user.id, 'Как будем сортировать?', reply_markup=nav.sorting_menu)


# Меню жанры
@dp.message_handler(Text(equals=['Жанры', 'Остальные'], ignore_case=True))
async def catching_genre(message: types.Message):
    if message.text == 'Жанры':
        await bot.send_message(message.from_user.id, 'Выбери жанр', reply_markup=nav.genre_menu)

    elif message.text == 'Остальные':
        await bot.send_message(message.from_user.id, 'Выбери жанр', reply_markup=nav.other_genre_menu)


# Меню поисковой выдачи
@dp.message_handler(Text(equals='Поиск', ignore_case=True))
async def catching_sorting(message: types.Message):
    await bot.send_message(message.from_user.id, 'Введите название аниме', reply_markup=nav.only_menu)


# Выдача Аниме по названию фильтры сортировки
@dp.message_handler()
async def looking_anime(message: types.Message):
    await bot.send_message(message.from_user.id, 'Подождите...', reply_markup=nav.only_menu)

    # Ловим Избранное
    if message.text == 'Избранное':
        a_list, left_count = requests_db.find_favorit(message.from_user.id)

    # Ловим жанр на фильтр
    elif message.text in genre_dict:
        a_list, left_count = requests_db.find_genre(message.text)

    # Ловим метод сортировки
    elif message.text in sorting_list:
        a_list, left_count = requests_db.find_sort(message.text)
        if message.text == 'Высший рейтинг':message.text = 'Высший_рейтинг'


    #  По названию
    else:
        a_list, left_count = requests_db.find_name(message.text)

    if not a_list:
        await bot.send_message(message.from_user.id, 'Не смог найти!')

    else:

        for a in a_list:
            try:            
                but_list = [InlineKeyboardButton('Описание', callback_data=f'description {a[8]}'), \
                InlineKeyboardButton('Смотреть', callback_data=f'watch {a[8]} {0}'), \
                InlineKeyboardButton('Список серий', callback_data=f'list_ep {a[8]} {a[3]}'), \
                InlineKeyboardButton('Избранное', callback_data=f'favorites {a[8]}')]
                if a[10] != None and a[10] and a[10] != 'None': but_list.append(InlineKeyboardButton('Все сезоны', callback_data=f'all_seasons {a[8]}'))
                
                await bot.send_photo(message.from_user.id, start_url + a[1], f'''
            {a[0].title()}\nТип: {a[9]}\nГод релиза: {a[2]} Серий {a[3]} из {a[4]}\n{a[5].title()}\nРейтинг: {a[6] // 10}/5, {a[7]} оценок.''',\
                reply_markup=InlineKeyboardMarkup(row_width=2).add(*but_list))

            except Exception as ex:
                print(ex, '\n', a)
        if left_count > 0:
            await bot.send_message(message.from_user.id, f'Осталось: {left_count}', reply_markup=InlineKeyboardMarkup().add( \
                    InlineKeyboardButton('Еще', callback_data=f'more {message.text}')))


''' ЛОВИМ CALLVACK DATA '''

# Ловим запрос на подробное описание
@dp.callback_query_handler(Text(startswith='description '))
async def description_anime(callback: types.CallbackQuery):
    obj = requests_db.find_description(int(callback.data.split()[1]))
    await callback.message.answer(f'{obj[0].title()} / {obj[1].title()}\n\n{obj[2]}')
    await callback.answer()


# Ловим запрос на просмотр
@dp.callback_query_handler(Text(startswith='watch '))
async def watch_anime(callback: types.CallbackQuery):
    anime_id, number_ep, user_id = int(callback.data.split()[1]), int(callback.data.split()[2]), callback.from_user.id
    # Чекаем юзера на просмотр сериала
    if number_ep == 0:
        number_ep = requests_db.check_episode(anime_id, user_id)

    obj = requests_db.find_episode(anime_id, number_ep)
    if obj == 'Ошибка в БД':
        await callback.answer('Не смог найти..')
    else:
        await callback.message.answer(f'{obj[0].title()}\nЭпизод {obj[1]} из {obj[3]}',
            reply_markup=InlineKeyboardMarkup(row_width=3).add( \
            InlineKeyboardButton(text='720p', url=obj[5]), \
            InlineKeyboardButton(text='480p', url=obj[6]), \
            InlineKeyboardButton(text='Смотреть онлайн', url=obj[7]), \
            InlineKeyboardButton('Предыдущий эпизод', callback_data=f'watch {obj[4]} {obj[1] - 1}'), \
            InlineKeyboardButton('Следующий эпизод', callback_data=f'watch {obj[4]} {obj[1] + 1}') \
            ))
        # Сохраняем эпизод за юзером
        requests_db.save_user_ep(anime_id, user_id, obj[1])

    await callback.answer()


# Ловим запрос на Список серий аниме
@dp.callback_query_handler(Text(startswith='list_ep '))
async def list_ep_anime(callback: types.CallbackQuery):
    anime_id, count_ep = int(callback.data.split()[1]), int(callback.data.split()[2])
    anime_name = requests_db.find_anime(anime_id)[0][0].title()
    count = 0
    for i_100 in range(count_ep // 100 + 1):
        but_list = []
        for i in range(count + 1, count_ep + 1):
            count += 1
            but_list.append(InlineKeyboardButton(f'{i}', callback_data=f'watch {anime_id} {i}'))

            if count % 100 == 0:
                break
        await callback.message.answer(anime_name, reply_markup=InlineKeyboardMarkup(row_width=6).add(*but_list))
        del but_list
    await callback.answer()


# Ловим запрос Еще! применяем метод поиска и прокрутку 
@dp.callback_query_handler(Text(startswith='more '))
async def more_anime(callback: types.CallbackQuery):
    this_scrolling = int(callback.data.split()[2]) if len(callback.data.split()) == 3 else 1
    mes = callback.data.split()[1]

    await callback.message.answer( 'Подождите...', reply_markup=nav.only_menu)

    # Ловим Избранное
    if mes == 'Избранное':
        a_list, left_count = requests_db.find_favorit(callback.from_user.id, this_scrolling)

    # Ловим жанр на фильтр
    elif mes in genre_dict:
        a_list, left_count = requests_db.find_genre(mes, this_scrolling)

    # Ловим метод сортировки
    elif mes in sorting_list:
        a_list, left_count = requests_db.find_sort(mes, this_scrolling)

    # Ловим запрос на конкретное аниме по ID
    elif mes[:3] == 'ID_':
        a_list, left_count = requests_db.find_anime(int(mes[3:])), 0

    #  По названию
    else:
        a_list, left_count = requests_db.find_name(mes, this_scrolling)


    for a in a_list:
        
        try:            
            but_list = [InlineKeyboardButton('Описание', callback_data=f'description {a[8]}'), \
            InlineKeyboardButton('Смотреть', callback_data=f'watch {a[8]} {0}'), \
            InlineKeyboardButton('Список серий', callback_data=f'list_ep {a[8]} {a[3]}'), \
            InlineKeyboardButton('Избранное', callback_data=f'favorites {a[8]}')]
            if a[10] != None and a[10] and a[10] != 'None': but_list.append(InlineKeyboardButton('Все сезоны', callback_data=f'all_seasons {a[8]}'))

            await callback.message.answer_photo(start_url + a[1], f'''
        {a[0].title()}\nТип: {a[9]}\nГод релиза: {a[2]} Серий {a[3]} из {a[4]}\n{a[5].title()}\nРейтинг: {a[6] // 10}/5, {a[7]} оценок.''',\
            reply_markup=InlineKeyboardMarkup(row_width=2).add(*but_list))
            del but_list

        except Exception as ex:
            print(ex, '\n', a)
    if left_count > 0:
        await callback.message.answer(f'Осталось: {left_count}', reply_markup=InlineKeyboardMarkup().add( \
                InlineKeyboardButton('Еще', callback_data=f'more {mes} {this_scrolling + 1}')))

    await callback.answer()


# Ловим запрос на добавление в Избранное
@dp.callback_query_handler(Text(startswith='favorites '))
async def click_facori(callback: types.CallbackQuery):
    result = requests_db.check_favorites(int(callback.data.split()[1]), callback.from_user.id)
    mes = 'Добавлено!' if result == True else 'Удаленно!'
    await callback.answer(mes)


# Ловим запрос на связанные аниме 
@dp.callback_query_handler(Text(startswith='all_seasons '))
async def click_facori(callback: types.CallbackQuery):
    result = requests_db.find_all_season(int(callback.data.split()[1]))    
    but_list = []
    for i, el in enumerate(result):
        but_list.append(InlineKeyboardButton(f'{i+1}: {el[0].title()}', callback_data=f'more ID_{el[1]}'))
               
    await callback.message.answer('Связанные аниме', reply_markup=InlineKeyboardMarkup(row_width=1).add(*but_list))
    del but_list
    await callback.answer()


# Функция проверки обновлений аниме и отправки сообщений 
async def loop_checking_for_updates(wait):
  while True:   
    print('Начал проверку обновлений')
    update_anime_id_list = check_update()
    for anime_id in update_anime_id_list:
        users_id = requests_db.user_search(anime_id)
        if users_id:
            anime_name = requests_db.find_anime(anime_id)[0][0].title()
            for user in users_id:
                try:
                    await bot.send_message(user[0], 'Вышили новые серии: ', reply_markup=InlineKeyboardMarkup().add(\
                        InlineKeyboardButton(f'{anime_name}', callback_data=f'more ID_{anime_id}')
                        ))
                except Exception as ex:
                    print(f'loop_checking_for_updates:\n{ex}')
                    
    await asyncio.sleep(wait)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(loop_checking_for_updates(randint(10_000, 50_000)))
    executor.start_polling(dp, skip_updates=True)
