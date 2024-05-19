import telebot
import random
from datetime import date


today = date.today().strftime('%d.%m.%Y')

token = "6649972886:AAHgZSHS1TGULWazEtkDx7GDaFx6hSi7BoA"

bot = telebot.TeleBot(token)

task_all = {}

random_task = ['Погладить кота', 'Выгулять собаку', 'Покормить рыбок', 'Помыть посуду', 'Лечь спать', 'Вынести мусор']

HELP = '''
Список доступных команд:
/show  - Напечать все задачи на заданную дату
/todo - Добавить задачу
/help - Напечатать help
/exit - Завершение работы
/random - Добавить случайную задачу на сегодня
/print - Напечать все задачи на несколько дат
'''
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, HELP)

def add_todo(date, task):
    if date in task_all:
        task_all[date].append(task)
    else:
        task_all[date] = [task]

@bot.message_handler(commands=['todo'])
def add(message):
    command = message.text.split(maxsplit=2)
    data = command[1].lower()
    task = command[2]
    if len(task) < 3:
        text = 'Некорректная задача'
    else:
        if data == 'сегодня':
            data = today
            add_todo(data, task)
            text = f'Задача {task} добавлена на сегодня.'
        else:
            add_todo(data, task)
            text = f'Задача {task} добавлена на {data}.'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['random'])
def random_add(message):
    data = today
    task = random.choice(random_task)
    add_todo(data, task)
    bot.send_message(message.chat.id, f'Задача {task} добавлена на сегодня.')

@bot.message_handler(commands=['show', 'print'])
def show(message):
    command = message.text.split()
    text = ''
    for i in range(1, len(command)):
        data = command[i].lower()
        if data == 'сегодня':
            data = today
        if data in task_all:

            for i in task_all[data]:
                if data == today:
                    data = 'сегодня'
                    text += data.upper() + ':' + '\n'
                    text += f'* {i} \n'
                else:
                    text += data.upper() + ':' + '\n'
                    text += f'* {i} \n'
        else:
            text += f'На {data.upper()} задач нет! \n****************\n'
            if message.text == '/show':
                break
    bot.send_message(message.chat.id, text)

bot.polling(none_stop=True)
