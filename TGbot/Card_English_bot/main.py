import random
import sqlalchemy
import enchant
import requests
import telebot
from telebot import types
from sqlalchemy.orm import sessionmaker
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from TGbot.Card_English_bot.models import create_tables, Users, UsersWords, Words, drop_tables, words_add
"""Телеграмм бот для изучения Английского. Для работы с
 ним понадобится API TGБота, Yandex переводчика и доступ к БД
  Он умеет добовлять слова на Английском и Русском языках"""

log_sql = input('Введите логин postgres: ')
pas_sql = input('Введите пароль postgres: ')
DSN = f'postgresql://{log_sql}:{pas_sql}@localhost:5432/englishcard_db'
engine = sqlalchemy.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()

# drop_tables(engine) #УДАЛЕНИЕ ВСЕЙ ТАБЛИЦИ
create_tables(engine)
words_add(session) #заполнение таблици 10ю первыми словами

state_storage = StateMemoryStorage()
token_tg = input('Введите токен ТГ бота: ')
bot = telebot.TeleBot(token_tg)
token_ya = input('Введите токен YA переводчик: ')
class Yan:
    """Класс яндекс переводчика с одним методом
     который возвращает английское и русское слово"""
    def Translator(self):
        word_ = self.text.capitalize()
        url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
        d = enchant.Dict("en_US")
        params = {
            'key': token_ya,
            'lang': 'en-ru',
            'text': word_,
            'ui': 'ru'
            }
        try:
            if d.check(word_):
                response = requests.get(url=url, params=params).json()
                return [word_, response['def'][0]['tr'][0]['text'].capitalize()]

            else:
                params.update(lang='ru-en')
                response = requests.get(url=url, params=params).json()
                return [response['def'][0]['tr'][0]['text'].capitalize(), word_]
        except LookupError:
            pass


class Cards_DB:
    """ Класс для взаимодействия с БД"""
    def dell_words_db(self):
        '''Удаляет слова у пользователя'''
        word_eng = Yan.Translator(self)
        q = (session.query(UsersWords)
            .filter((UsersWords.id_words == Cards_DB.get_id_word(word_eng[0]))
                     & (UsersWords.id_user == Cards_DB.get_id_u(self))))
        if bool(q.all()) == True:
            q.delete()
            session.commit()
            return bot.send_message(self.chat.id,
                                    f'Слово <b>{self.text.capitalize()}</b> было удаленно из твоего словаря.',
                                    parse_mode='HTML')
        else:
            return bot.send_message(self.chat.id,
                                    f'Слова <b>{self.text.capitalize()}</b> и так нет у вас в словаре.',
                                     parse_mode='HTML')

    def get_id_u(self):
        """Возвращает id юзера"""
        q = session.query(Users).filter(Users.user == self.from_user.id)
        for i in q.all():
            return i.id_u

    def get_id_word(self):
        """Возвращает id слова из основной таблици слов"""
        q = session.query(Words).filter(Words.words_eng == self)
        for i_w in q.all():
            return i_w.id

    def get_words(self):
        """Возвращает список слов ['англ','рус']"""
        words = []
        q = (session.query(Words)
             .join(UsersWords)
             .filter(UsersWords.id_user == Cards_DB.get_id_u(self))
             )
        for i in q.all():
            words.append((i.words_eng, i.translation))
        random.shuffle(words)
        return words

    def add_db_new_user(self):
        '''Добовляет нового пользователя в БД'''

        if bool(Cards_DB.get_id_u(self)) == False:
            session.add(Users(id_u=Cards_DB.get_id_u(self), user=self.from_user.id))
            add_ = session.query(Words).filter(Words.id <= 10)
            for s in add_.all():
                session.add(UsersWords(id_user=Cards_DB.get_id_u(self), id_words=s.id))
            session.commit()
    def add_db_new_words(self):
        '''Добавляет новые слова пользовыателю при помощи метода класса Yan'''
        res = Yan.Translator(self)
        if res != None:
            eng = res[0]
            rus = res[1]
            q = session.query(Words).filter(Words.words_eng == eng)
            uw = (session.query(UsersWords).filter((UsersWords.id_user == Cards_DB.get_id_u(self))
                                                   & (UsersWords.id_words == Cards_DB.get_id_word(eng))))
            if bool(q.all()) == False:
                session.add(Words(words_eng=eng, translation=rus))
                session.add(UsersWords(id_user=Cards_DB.get_id_u(self), id_words=Cards_DB.get_id_word(eng)))

                session.commit()
            elif bool(uw.all()) == False:
                session.add(UsersWords(id_user=Cards_DB.get_id_u(self), id_words=Cards_DB.get_id_word(eng)))
                session.commit()
            else:
                return bot.send_message(self.chat.id, f'Такое слово уже есть в твоем словаре!')
            count_ = session.query(UsersWords).filter(UsersWords.id_user == Cards_DB.get_id_u(self)).count()
            return bot.send_message(self.chat.id, f'Слово 🇺🇸<b>{eng}</b> --> 🇷🇺<b>{rus}</b>\
             было добавленно в твой словарь.\
Теперь в словаре {count_} слов!', parse_mode='HTML')

        else:
            return bot.send_message(self.chat.id, f'Слово {self.text} слишком короткое либо его не существует.')


class Command:
    '''Список команд ТГ бота'''
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    LESSON = 'Поехали 🚀'

class MyStates(StatesGroup):
    correct = State()
    translate = State()
    other_words = State()

class Telegram:
    """Класс ТГбота"""

    @bot.message_handler(commands=['start'])
    def starts(message):

        if bool(Cards_DB.get_id_u(message)) == False:
            Cards_DB.add_db_new_user(message)
            bot.send_message(message.chat.id,
    f'Привет 👋 Давай попрактикуемся в английском языке.Тренировки можешь проходить в удобном для себя темпе.\n\
                             \n\
У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения\
. Для этого воспрользуйся инструментами:\n\
        \n\
        добавить слово ➕,\n\
        удалить слово 🔙.\n\
                             \n\
        Ну что, начнём ⬇️')

        markup = types.ReplyKeyboardMarkup(row_width=2)
        buttons = []
        words = Cards_DB.get_words(message)
        translate = words[0][1]
        correct = words[0][0]
        correct_btn = types.KeyboardButton(correct)
        buttons.append(correct_btn)
        other_words = [words[i+1][0] for i in range(len(words[1:4]))]
        other_words_btn = [types.KeyboardButton(word) for word in other_words]
        buttons.extend(other_words_btn)
        random.shuffle(buttons)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        buttons.extend([add_word_btn, delete_word_btn, next_btn])

        markup.add(*buttons)

        greeting = f"Выбери перевод слова:\n🇷🇺 <b>{translate}</b>"
        bot.send_message(message.chat.id, greeting, parse_mode='HTML', reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.correct, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['correct'] = correct
            data['translate'] = translate
            data['other_words'] = other_words


    @bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
    def add_words(message):
        add_word = bot.send_message(message.chat.id, 'Какое слово хотите добавить?')
        bot.register_next_step_handler(add_word, Cards_DB.add_db_new_words)


    @bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
    def delete_words(message):
        del_word = bot.send_message(message.chat.id, 'Какое слово хотите удалить?')
        bot.register_next_step_handler(del_word, Cards_DB.dell_words_db)

    @bot.message_handler(func=lambda message: message.text == Command.NEXT)
    def next(message):
        Telegram.starts(message)

    @bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'sticker'])
    def message_reply(message):
        text = message.text

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            correct = data['correct']
            translate = data['translate']

            if text == correct:
                markup = types.ReplyKeyboardMarkup(row_width=2)
                buttons = []
                next_btn = types.KeyboardButton(Command.NEXT)
                add_word_btn = types.KeyboardButton(Command.ADD_WORD)
                delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
                buttons.extend([add_word_btn, delete_word_btn, next_btn])

                markup.add(*buttons)
                bot.send_message(message.chat.id,
                                 f'🥳🥳🥳Отлично слово 🇷🇺<b>{translate}</b> --> 🇺🇸<b>{correct}</b>',
                                      parse_mode='HTML', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, f'❌ попробуйте еще раз вспомнить слово 🇷🇺<b>{translate}</b> ?',
                                     parse_mode='HTML')

session.close()
bot.polling(none_stop=True)
if __name__=='__main__':
    pass