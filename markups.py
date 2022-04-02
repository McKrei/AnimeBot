from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



but_menu = KeyboardButton('Меню')
only_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(but_menu)

''' ######### Главное меню ######### '''
select_name = KeyboardButton('Поиск')
new_add = KeyboardButton('Обновления')
button_sorting = KeyboardButton('Сортировка')
button_genre = KeyboardButton('Жанры')
button_fav_sort = KeyboardButton('Избранное')
button_finishen = KeyboardButton('Просмотренные')

main_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(new_add, button_sorting, button_genre,\
	button_fav_sort, select_name, button_finishen)

''' ######### Меню Сортировки ######### '''
button_sort_new = KeyboardButton('Новые')
button_sort_pop = KeyboardButton('Популярные')
button_sort_raiting = KeyboardButton('Высший рейтинг')

sorting_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(button_sort_new, button_sort_pop,\
	button_sort_raiting, but_menu)

''' ######### Меню жанры ######### ''' # ДОБАВИТЬ ЕЩЕ ЖАНРОВ
# ТОП 5
button_adventure = KeyboardButton('Приключения')
button_comedy = KeyboardButton('Комедия')
button_fantasy = KeyboardButton('Фэнтези')
button_romance = KeyboardButton('Романтика')
button_life = KeyboardButton('Повседневность')
button_drama = KeyboardButton('Драма')
button_other_genre = KeyboardButton('Остальные')

genre_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(button_adventure, button_comedy,\
	button_fantasy, button_romance,button_romance, button_drama, button_other_genre, button_life, but_menu,)
		
# Остальные 
button_school = KeyboardButton('Школа')
button_fantastic = KeyboardButton('Фантастика')
button_mystic = KeyboardButton('Мистика')
button_shunen = KeyboardButton('Сёнэн')
button_story = KeyboardButton('Сказка')
button_sport = KeyboardButton('Спорт')
button_detective = KeyboardButton('Детектив')
button_horror = KeyboardButton('Ужасы')
button_etty = KeyboardButton('Этти')

other_genre_menu = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True).add(button_school,\
	button_fantastic, button_mystic, button_shunen, button_sport, button_detective,\
	button_horror, button_etty, but_menu)

''' ######### Меню серии ######### '''
button_next_ep = KeyboardButton('Следующая серия')
button_all_ep = KeyboardButton('Список серий')

button_favourit = KeyboardButton('Добавить в Избранное')
button_anime = KeyboardButton('К аниме')

episode_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(button_next_ep, button_all_ep, button_favourit,\
	button_anime, but_menu)


''' ######### Меню избаное ######### '''
button_finishen = KeyboardButton('Просмотренные')
finishen_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(button_finishen, but_menu)