

def divide_categories(anime_list):
    '''
    Разделяем результат запроса списка аниме на категории. 
    '''
    result_dict = {}
    for id, name, cat in anime_list:
        anime = (id, name)
        if result_dict.get(cat):
            result_dict[cat].append(anime)
        else:
            result_dict.update({cat: [anime]})

    return result_dict

if __name__ == '__main__':
    print(divide_categories((
        (14, 'anime1', 'cat1'),
        (2, 'anime2', 'cat1'),
        (13, 'anime3', 'cat2'),
        (145, 'anime4', 'cat3'),
        (125, 'anime5', 'cat3')
    )))