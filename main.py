import telebot
import sqlite3
import random
import datetime
import schedule
import time
import os
import logging
from telebot import types

bot = telebot.TeleBot("6094614699:AAGqZjKvLlza2aiVI3rH2SKEuWWpEruIkOc")

logging.basicConfig(level=logging.INFO)

db = sqlite3.connect("users.db", check_same_thread=False)
sql = db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER,
             username TEXT, 
             fio TEXT,
             wish TEXT)""")

STATE_START = 0
STATE_WAIT_DATA = 1
STATE_WAIT_RANDOM_PHOTO = 2

user_state = {}


@bot.message_handler(commands=['start'])
def start(message):
    if start_was_called(message.from_user.id):
        bot.send_message(message.chat.id, "Ты уже с нами)")
        return
    username = message.from_user.username
    if user_state.get(message.chat.id) == STATE_WAIT_DATA:
        # User is in the state of entering data
        user_state[message.chat.id] = STATE_WAIT_RANDOM_PHOTO  # Update user state
        bot.send_message(message.chat.id, "Чего бы ты хотел к Новому году?")
        bot.register_next_step_handler(message, get_wish, username)
    elif user_state.get(message.chat.id) == STATE_WAIT_RANDOM_PHOTO:
        # User is in the state of waiting for a random photo
        user_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        rbutton = types.KeyboardButton('Фото')
        user_markup.add(rbutton)
        # user_markup.row('random_photo')  # Add the '/random_photo' command button
        bot.send_message(message.from_user.id, "Choose a command:", reply_markup=user_markup)
    else:
        # User is in the default state
        bot.send_message(message.chat.id, """🎅🎉 **Привет, коллега!** Рад видеть тебя в нашем волшебном мире **Тайного Санты!** 🎁✨

🎄 Добро пожаловать в новогоднюю сказку, где мы собрались вместе, чтобы **поделиться радостью и дарить улыбки** друг другу! У нас есть особый функционал, который сделает нашу игру еще более веселой и захватывающей.  

📝 Примите участие, введя ваше имя и пожелания к подарку. Пусть это будет ваше личное волшебное пожелание, которое мы подарим вашему **Тайному Санте!** 21 декабря покажем тебе - чей ты Тайный Санта!

⏰ Каждый день в 13:00 вам будет приходить сообщение с **нашими достижениями.** Будьте в курсе всех прекрасных моментов, которые мы создали вместе!  

📸 А еще, нажимая на кнопку "Фото", вы будете получать **случайные фотографии** наших замечательных команд за прошедший год. Позвольте вам вспомнить самые яркие моменты и поделиться улыбками среди коллег!

**Счастливого волшебства** и приятного участия в игре Тайного Санты! Пусть каждый подарок будет полон сюрпризов и добрых пожеланий. Вместе мы создадим новогоднюю атмосферу, которая переполнена радостью и взаимным вниманием. **Счастливого Нового года!** 🎅🎉✨""")
        bot.send_message(message.chat.id, "Как тебя зовут?")
        user_state[message.chat.id] = STATE_WAIT_DATA  # Update user state
        bot.register_next_step_handler(message, get_fio, username)


# Функция для записи данных пользователя в БД
def save_user(user_id, username, fio, wish):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, username, fio, wish) VALUES (?, ?, ?, ?)",
                       (user_id, username, fio, wish))
        logging.info(f"User {user_id} saved to the database.")
        conn.commit()


# Функция для отправки сообщения пользователю
def send_message(user_id, message):
    bot.send_message(user_id, message)


def start_was_called(user_id):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return row is not None


# Функция для генерации случайного распределения пользователей
def generate_distribution():
    users = []
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        conn.commit()
        for row in cursor:
            users.append({
                "user_id": row[0],
                "username": row[1],
                "fio": row[2],
                "wish": row[3]
            })

    # Если пользователей нечетное количество, удаляем лишнего
    # if len(users) % 2 == 1:
    #     users.pop(users.index({"user_id": '12345'}))

    used_targets = []  # список использованных получателей

    # распределение
    for user in users:
        got_target = False
        while not got_target:

            target_user = random.choice(users)  # выбираем случайного

            # проверки
            if target_user["user_id"] != user["user_id"] and target_user["username"] != user["username"] and \
                    target_user["fio"] != user["fio"] and target_user["wish"] != user[
                "wish"] and target_user not in used_targets:
                # сохраняем
                user["target_user"] = target_user
                user["target_userid"] = target_user["user_id"]

                used_targets.append(target_user)
                got_target = True

    return users


def send_random_photo(user_id):
    photos_folder = "./photos"  # Replace with the actual folder name
    photo_files = [f for f in os.listdir(photos_folder) if os.path.isfile(os.path.join(photos_folder, f))]

    if not photo_files:
        send_message(user_id, "Фоток нет(")
        return

    random_photo = random.choice(photo_files)
    photo_path = os.path.join(photos_folder, random_photo)

    # Send the photo
    with open(photo_path, 'rb') as photo:
        bot.send_photo(user_id, photo)


# Основная логика бота


def get_fio(message, username):
    fio = message.text
    user_id = message.chat.id
    user_state[user_id] = {'fio': fio}  # Save the entered 'ФИО'

    bot.send_message(message.chat.id, "Что бы ты хотел к Новому году?")
    bot.register_next_step_handler(message, get_wish, username)


def get_wish(message, username):
    wish = message.text
    user_id = message.chat.id
    user_state[user_id]['wish'] = wish  # Save the entered 'пожелания к подарку'

    save_user(user_id, username, user_state[user_id]['fio'], user_state[user_id]['wish'])
    user_state.pop(user_id)  # Reset user state

    user_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    rbutton = types.KeyboardButton('Фото')
    user_markup.add(rbutton)
    # user_markup.row('random_photo')  # Add the '/random_photo' command button
    bot.send_message(message.from_user.id,
                     "🎅🎉Пока ждешь резульатов, нажимай на кнопку Фото, и получай **случайные фотографии** наших замечательных команд за прошедший год.🌟 Позвольте вам вспомнить самые яркие моменты и поделиться улыбками среди коллег!",
                     reply_markup=user_markup)
    # bot.send_message(message.chat.id, "Данные сохранены! Теперь вы можете использовать /random_photo.")


@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id) == STATE_WAIT_DATA)
def get_data(message):
    data = message.text.split()

    user_state[message.chat.id] = STATE_START

    user_id = message.chat.id
    username = data[0]
    fio = data[1]
    wish = data[2]

    save_user(user_id, username, fio, wish)
    bot.send_message(message.chat.id, "А теперь ждем резульатов 21 декабря!)")


@bot.message_handler(commands=["info"])
def info(message):
    send_message(message.from_user.id, "Осталось всего чуть-чуть!")


@bot.message_handler(commands=["finish"])
def finish(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    # draw_date = datetime.datetime(2023, 12, 29, 12, 0, 0)
    # if datetime.datetime.fromtimestamp(message.date) >= draw_date:
    users = generate_distribution()
    for user in users:
        target_username = user["target_user"]["username"]
        fio = user["target_user"]["fio"]
        wishes = user["target_user"]["wish"]

        send_message(user["user_id"], f"Подари: @{target_username}\nЕго зовут: {fio}\nПожелания к подарку: {wishes}")
        time.sleep(1)

@bot.message_handler(commands=["one"])
def one(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""
    🎊✨ Достижения Транзакционного стрима! 🎉🌟

    

    🏢 Корпоративные карты:
    Корпоративные карты с возможностью бесплатного снятия до 300 тысяч рублей в месяц. Облегчите финансовые операции и управляйте бюджетом вашего бизнеса без дополнительных комиссий! 💳💰

    💰 Налоговая копилка:
    Откройте налоговую копилку и начисляйте проценты на ежедневный остаток. Оплачивайте налоги вовремя и легко с лучшими условиями и простым подключением! Ваш бизнес будет более прозрачным, а ваше настроение - праздничным! ✨📉

    🙋‍♂️ Самозанятые:
    Открывайте РКО прямо в нашем приложении розницы без посещения офиса и подписи бумажных форм. Упрощайте финансовые процессы и заботьтесь о своем бизнесе с легкостью и юмором! 📱💼

    🌏 ВЭД:
    Примите участие в акции "Курс на Восток" и "Курс на Юани". Пользуйтесь бесплатными переводами в юанях, получайте льготные условия и сделайте свой бизнес более успешным на восточных рынках. Погрузитесь в новые возможности и откройте двери к успешным деловым связям! 🚀💱

    💼 Тариф "Старт с 0":
    Откройте лучший тариф на рынке для микропредприятий. Ноль рублей обслуживания, ноль комиссий за переводы и льготные условия. Развивайте свой бизнес с комфортом и экономьте деньги - это заслуженный подарок для вашего успеха! 💼💲

    🏦 РКО - открытие счета:
    Просто, быстро и без хлопот открывайте расчетный счет в нашем онлайн-банке. Не нужно ездить в офис или подписывать бумажные формы. Управляйте своими финансами с легкостью и стартуйте в новый год с энтузиазмом! 🏢💼

    🏢 Корпоративные карты:
    Благодаря этой интеграции, ваши выписки теперь передаются в сервис "Моё дело" автоматически, без необходимости ручной обработки. Вы сможете экономить много времени, которое раньше тратилось на передачу документов, и аккуратно использовать его для чего-то более приятного и веселого в наступающем году! 📊🎉

    🎁 Наслаждайтесь новогодними праздниками и дарите своему бизнесу невероятные возможности с нашими праздничными продуктами! Празднуйте, развивайтесь и открывайте новую главу успеха в кругу вашей команды! Счастливых праздников и процветания в новом году! 🎊✨💰
    """)

@bot.message_handler(commands=["two"])
def two(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""**Приветствую, радостные команды малого и среднего бизнеса в нашем онлайн банке!** Наступает чудесное время новогодних хлопот, когда все мы пытаемся справиться со всеми задачами и при этом сохранить праздничное настроение.

    У нас есть замечательная новость, которая принесет вам порцию позитива и суровую иронию! Мы разработали новую фичу, которая сократит время формирования актов эквайринга с 30 минут до невероятных 40 СЕКУНД! Да-да, вы не ослышались, друзья! Теперь вам останется только выбрать варианты платежей и наша система автоматически сгенерирует акты для вас.

    **Хотите знать еще? Но разумеется!** Как только акты будут сформированы, наша надежная система сделает что-то, что самые опытные люди даже не могут - она автоматически сверит акты с платежными системами! Да, да, никаких вручную проверяемых сравнений. Наша система быстро и точно справляется с этой задачей, оставляя вас свободными для более интересных и важных дел.

    **Мы сами не перестаем удивляться, как вам не приходит в голову, как такая фича могла обойтись без вас столько времени!** Но вот, лучше поздно, чем никогда, правда?

    С нашей новой фичей формирования актов эквайринга вам останется лишь набрать запрограммированные варианты и банк автоматически сформирует и сверит все акты за вас! Только не забудьте посмотреть, как система справляется быстрее, чем ваше окошко на зекольтышках!

    Волшебные праздники на носу, мы желаем вам бесконечного позитива, удачи в работе и пусть ваш бизнес процветает в новом году! И пускай наша фича сокращения времени формирования актов эквайринга подарит вам долю сарказма и улыбку на лицах!
    """)

@bot.message_handler(commands=["three"])
def three(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""🌟 **Приветствую вас, уважаемые представители бизнес-команды в нашем онлайн банке!** 🌟

    У нас есть потрясающая новость от команды банковских гарантий, которая, безусловно, добавит в ваши новогодние праздники долю радости и экономии.

    Мы рады сообщить, что мы значительно улучшили **скорость выпуска банковских гарантий** и снизили затраты на бумагу и отправку. Теперь процесс выдачи гарантий проходит в несколько раз быстрее, что означает, что вы сможете предоставить заказчику необходимую гарантию в самое кратчайшее время. Быстрые и эффективные решения - вот что нам пришло в голову!

    Но это еще не все. Мы предусмотрели возможность **электронной доставки гарантий**, что позволяет вам значительно сэкономить на доставке оригиналов. Представьте себе: теперь нет необходимости высылать физические документы, все происходит онлайн! Это не только гораздо удобнее, но и экономит ваши деньги на транспортных расходах и почтовых услугах.

    Таким образом, **скорость выпуска гарантий увеличена, затраты на бумагу и отправку снижены**, а для вас и ваших клиентов это означает быстрое получение необходимой гарантии и экономию денег на доставке оригинала.

    **Волшебство новогодних праздников обрушивается на нас**, и мы хотим пожелать вам неиссякаемой энергии, процветания в бизнесе и моментального получения всех необходимых гарантий. Позвольте нашей команде банковских гарантий принести вам радость и уверенность в наступающем году! 🎉🚀
    """)

@bot.message_handler(commands=["four"])
def four(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    # draw_date = datetime.datetime(2023, 12, 29, 12, 0, 0)
    send_message_to_all("""🎉 **Друзья-банкиры, давайте сделаем новый год сказочным и зарядимся праздничным вайбом!** 🌟

    У нас есть порция приятной новости от команды **Дистанционного Банковского Обслуживания (ДБО)** – они сделали что-то волшебное, что вы просто непременно полюбите!

    Радостно объявляем, что в рамках зарплатного проекта мы дарим вам функционал по загрузке и отправке ведомостей, эффективной оплате и просмотру списка ваших замечательных сотрудников! Теперь у вас есть возможность легко и удобно работать со своими зарплатными данными – это просто настоящая магия!

    Конечно же, мы понимаем, что даже волшебники бывают чуть-чуть шаловливыми. Поэтому полностью не доделали нашу новую фичу. Но не беспокойтесь, в самом начале 2024 года мы добавим невиданную ранее возможность – функцию добавления и удаления сотрудника напрямую из приложения. Таким образом, наш зарплатный проект будет на равных условиях с конкурентами, не оставляя ни единого шанса нашему чудесному приложению!

    Верьте в магию и будьте уверены, что в нашем **ДБО** встречаются самые настоящие феи и колдуны, работающие над непревзойденными инновациями, чтобы сделать вашу жизнь проще и удобнее. Мы стремимся сделать все возможное, чтобы вы почувствовали себя настоящими героями, руководящими своими денежными волшебными странами!

    Счастливого Рождества и волшебных праздников! Пусть наша команда **ДБО** не передаст вам только волшебные способности, но и подарит чудесный функционал в вашем новогоднем бизнесе! 🎄✨
    """)

@bot.message_handler(commands=["five"])
def five(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""✨ **Волшебные приветствия, уважаемые пользователи нашего онлайн банка!** ✨

    С радостью хотим рассказать вам о нашей захватывающей новой функции - **ролевой модели**. Эта уникальная фича позволяет подключать несколько пользователей к одному ИНН и предоставлять различные роли для просмотра информации в режиме онлайн.

    Представьте себе эту сцену: вы владелец бизнеса, и у вас есть команда верных помощников. Каждому из них нужен доступ к информации, но необходимо ограничить ее видимость в соответствии с их ролями. И вот тут наша ролевая модель вступает в игру!

    С нашей новой функцией вы можете прикрепить несколько пользователей к одному ИНН и назначить каждому из них конкретную роль. Например, один пользователь может иметь доступ только для просмотра информации, другой может быть уполномочен на редактирование данных, а третий может быть истинным хранителем полномочий. Это просто фантастический способ управления доступом к бизнесу!

    И самое интересное – все эти возможности доступны в режиме онлайн. Вам больше не нужно тратить время на отправку и обмен физическими копиями документов. Просто управляйте ролями, нажимайте кнопку, и волшебство происходит в реальном времени!

    Однако давайте будем честными – даже самые магические фичи могут иметь свои ограничения. В нашем случае, мы пока не смогли реализовать функцию трансформации пользователей в настоящих эльфов или фей. Но, кто знает, возможно, к следующему году эта фантастическая возможность станет реальностью!

    Так что дорогие пользователи, пускай наша ролевая модель добавит в ваш бизнес шарм и порцию магии! Пусть ваша команда работает четко и последовательно, и каждый из вас займет свое место в этой увлекательной игре успеха!

    🎉 **Счастливых праздников и пусть ваша команда будет настоящим волшебным союзом!** 🌟
    """)

@bot.message_handler(commands=["six"])
def six(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""🌟 **Приветствую, уважаемые пользователи нашего онлайн банка!** 🌟

    С великим весельем и радостью мы хотим поделиться с вами новостью от нашей замечательной команды **CVM (управление взаимодействием с клиентами)**. Мы придумали нечто особенное - захватывающую фичу, которая открывает совершенно новый канал коммуникации с вами, уважаемыми клиентами.

    Дамы и господа, позвольте представить вам нашу гордость - **функцию онбординга**! Мы приготовили для вас специальные баннеры, которые будут отображаться прямо в вашем личном кабинете. Через них мы сможем рассказать о преимуществах новых продуктов, а также ознакомить вас с последними новинками в нашем приложении.

    Представьте: вы открываете свой личный кабинет и встречаете яркие и привлекательные баннеры. Они будут информировать вас о важных функциях и возможностях, которые теперь доступны в нашем приложении. Благодаря этому, вы легко узнаете о новых продуктах, которые помогут вам управлять вашими финансами более эффективно!

    Но давайте не забудем подкинуть долю юмора в эту непревзойденную атмосферу. Хотя мы заботливо разместим все требуемые баннеры в личном кабинете, мы все еще выполняем последние телодвижения и танцы, чтобы их полное количество было с вами в самый короткий срок. Шутка юмора в стиле новогодней резиденции Санта Клауса!

    Так что дорогие клиенты, открывайте ваш личный кабинет, наслаждайтесь нашими сверкающими баннерами и открывайте двери в мир новых возможностей. Ведь знание - это сила, а наша команда **CVM** старается предоставить вам все необходимые знания, чтобы вы строили успешное финансовое будущее!

    Пусть ваше новогоднее путешествие с нашей командой **CVM** будет наполнено удивительными открытиями и впечатляющими возможностями. **Счастливых праздников и пусть каждый баннер принесет вам добрые эмоции и новые знания о нашем банке!** 🎉
    """)


@bot.message_handler(commands=["seven"])
def seven(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_all("""С наступлением нового года, наша волшебная команда маркетинга внесла некоторые улучшения в нашу коллекцию предложений! 🎉✨

    1️⃣ **Аналитика** - теперь вы можете использовать наш мощный инструмент анализа рынка, чтобы выбрать самые доходные ниши и лидеров для вашего бизнеса. Ловите выгодные тенденции и принимайте правильные решения для успеха! 💼📈

    2️⃣ **Закупки из Китая** - наша команда знает, как сделать ваши закупки из Китая максимально простыми и выгодными. Мы найдем проверенных поставщиков, поможем вам найти то, что вам нужно, и даже возьмем на себя процесс сертификации товаров. Погрузитесь в мир бесконечных возможностей! 🌏🛒

    3️⃣ **Фулфилмент** - доверьте нам заботу о физическом выполнении и доставке ваших товаров. Наша команда упакует и пометит товары с заботой и профессионализмом, готовя их к поставке на маркетплейсы или прямо к вам. Возлагайте на нас ваши желания, и мы превратим их в реальность! 📦🚚

    4️⃣ **Управление складом** - взвлетите на новый уровень с нашим инструментом управления складом. Мы предлагаем вам учет товаров, обработку заказов из разных каналов, а также прогнозирование остатков. Будьте уверены в том, что ваш склад будет работать эффективно и беспроблемно! 🔍📊

    Мы готовы подарить вам незабываемое волшебство и помочь вам достичь новых высот в вашем бизнесе в этом новом году. Пусть наша команда маркетинга сделает ваш путь к успеху еще более ярким и захватывающим! 🌟🎁
    """)


@bot.message_handler(commands=["eight"])
def eight(message):
    admin_id = 5200228179  # user_id админа

    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "Ты не админ)")
        return
    send_message_to_me("""Когда наступает новый год, мы с благодарностью вспоминаем нашу **волшебную команду продуктовых аналитиков**! 🎉🔮 Они проводили весь год, работая над сложными аналитическими задачами и находя правильные гипотезы, а также визуализировали информацию своими магическими навыками!

    **Волшебники аналитики**, спасибо вам за то, что помогали нам понимать данные, раскрывая тайны нашего бизнеса. Вы выводили правильные гипотезы, подбирали оптимальные стратегии и визуализировали информацию так, что она становилась понятной даже для самых запутанных умов!

    Ваше волшебство с данными и аналитикой поднимало наши бизнес-процессы на новый уровень. Вы были настоящими колдунами, превращая цифры и графики в понятные и полезные инсайты.

    Но знаете, мы тоже обнаружили маленькую загадку в вашей работе. Видимо, вы постоянно носили на голове волшебные колпаки аналитики, которые давали вам невероятные способности анализировать и делать прогнозы. Хотя мы все видели, как вы извлекаете правильные выводы из сложных данных и волшебным образом преображаете информацию, чтоб она стала ясной и понятной!

    Так что, **дорогие аналитики**, примите наши благодарности за ваше волшебство и работу, которая помогла нам сделать правильные решения и достичь успеха во всем нашем бизнесе! 🌟🔮 Желаем вам счастливых праздников, море волшебства и продолжайте раскрывать тайны данных и аналитики в новом году! Это будет настоящее волшебство! ✨😄
    """)


@bot.message_handler(func=lambda message: message.text == "Фото")
def random_photo(message):
    send_random_photo(message.chat.id)

def send_message_to_me(message_text):
    user_id = 6679534024
    send_message(user_id, message_text)
    time.sleep(1)
    print(user_id)


# Function to send a message to all users
def send_message_to_all(message_text):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        send_message(user_id, message_text)
        time.sleep(1)
        print(user_id)

user_ids = [6679534024, 5200228179, 356591982, 234255739, 184745533, 568244869, 1773538768, 500250334, 170119259, 1003766557, 917446964, 1103363577, 52231723, 464225334, 6562462768, 255125686, 742369179, 873869517, 667276461, 452112435, 42786538, 999101706, 274030458, 527085993, 215826853, 1507820402, 341702869, 203187563, 83670786, 279410694, 6679534024, 892600188]  # список id пользователей
question = "Привет, Друг!🌟 MVP бота не получил твоего пожелания к подарку (баги она такие, надеюсь ты простишь меня)( Напиши, пожалуйста, еще раз что бы ты хотел получить от Тайного Санты и завтра в 14:00 я отправлю тебе того, кому предстоит отправить подарок)"


responses = {}

user_auis = [5200228179, 6679534024, 356591982, 234255739, 184745533, 568244869, 1773538768, 500250334, 1003766557, 917446964, 1103363577, 52231723, 464225334, 6562462768, 255125686, 742369179, 873869517, 667276461, 452112435, 42786538, 999101706, 274030458, 527085993, 215826853, 1507820402, 341702869, 203187563, 83670786, 279410694, 892600188]  # список id пользователей
santas = [ """Привет! Ты Тайны""",
        """Привет! Ты Тайный Сан""",
          """Привет! Ты Тайный Санта для: Татьяна Ежикова @Teresena. Передали пожелание: Мандарины и какой-нибудь новогодний аксессуар (например елочный букетик или шар со снегом)""",
          """Привет! Ты Тайный Санта для: Татьяна Коваль @tapopova99""",
          """Привет! Ты Тайный Санта для: Анастасия Яковлева @Nastasii47. Передали пожелание: Вкусный чай""",
          """Привет! Ты Тайный Санта для: Андрей Островский @Thndrw. Передали пожелание: Фото""",
          """Привет! Ты Тайный Санта для: Оля Веретенникова @veretennikoova. Передали пожелание: Буду Рада красивой гирлянде с миллион тысячью огней 😍😍😍""",
          """Привет! Ты Тайный Санта для: Эльдар Ахмедов @aheldar. Передали пожелание: https://market.yandex.ru/product--oda-e-manga-one-piece-bolshoi-kush-kn-1-oda-e/1781944880?sku=664233953&do-waremd5=l_xYPd6vz_0G46Wnc_4WqA&uniqueId=924574""",
          """Привет! Ты Тайный Санта для: Полина Трофимова @o_0_polina. Передали пожелание: Сюрприз""",
          """Привет! Ты Тайный Санта для: Чернова Валерия @chernovaleriya. Передали пожелание: Ароматические свечи, новогодний чай""",
          """Привет! Ты Тайный Санта для: Манукян Сурен @surenmanukyan.""",
          """Привет! Ты Тайный Санта для: Роман Дмитров @rdmitrov5. Передали пожелание: Любой подарок на твой выбор)""",
          """Привет! Ты Тайный Санта для: Руслан Рязанцев @ryazantcevvv. Передали пожелание: Статуэтка Голова Давида кашпо с маленьким кактусом внутри""",
          """Привет! Ты Тайный Санта для: Юлия Чуманова @HoustonWeHaveAnIdea. Передали пожелание: Пожелаю себе новых ольфкакторных впечатлений 🌚""",
          """Привет! Ты Тайный Санта для: Надежда Апресянц @NadejdaAnd. Передали пожелание: 2 книги Юваля Ноя Харари в бумажном переплете: 1. "Sapiens. Краткая история человечества" 2.«Homo Deus. Краткая история будущего»""",
          """Привет! Ты Тайный Санта для: Роза Базина @lili_rozalie. Передали пожелание: Идеи для подарков: https://ozon.ru/t/Jd0QMn1 https://ozon.ru/t/0l3rGyr https://ozon.ru/t/MP4L24V https://ozon.ru/t/ApaX4d8 https://ozon.ru/t/8Vg2z3G""",
          """Привет! Ты Тайный Санта для: Екатерина Федина @efed123. Передали пожелание: Сюрприз - лучший вариант. Если нет, то можно настольную игру, необычный пазл или что-то в этом стиле.""",
          """Привет! Ты Тайный Санта для: None ахахха. Передали пожелание: Калоши""",
          """Привет! Ты Тайный Санта для: Дмитрий Андропов @Dima_OA. Передали пожелание: Какую нибудь приятную новогоднюю мелочь)""",
          """Привет! Ты Тайный Санта для: Надежда Панчурина ))) @nadine_pna. Передали пожелание: Убрать 144 бага и еще что-то интересное""",
          """Привет! Ты Тайный Санта для: Полина Клейнер @mrplln""",
          """Привет! Ты Тайный Санта для: Альфия Абсалямова @AbsalyamovaAlfiya. Передали пожелание: Книгу""",
          """Привет! Ты Тайный Санта для: Ольга Артамонова @artamon4ik. """,
          """Привет! Ты Тайный Санта для: Рябова Олеся @Lesichkaaaa. Передали пожелание: Новогоднюю чашку и новогоднюю тарелку""",
          """Привет! Ты Тайный Санта для: Константин Гришин @G_K_A.""",
          """Привет! Ты Тайный Санта для: Потемкин Василий @vpotemkin. Передали пожелание: Сюрприз""",
          """Привет! Ты Тайный Санта для: Вадим Часовских @vadimchasovskikh. Передали пожелание: Интересная художественная книга)""",
          """Привет! Ты Тайный Санта для: Филиппов Артем @Lupus5. Передали пожелание: Не одежду, не носки, что-то практичное.""",
          """Привет! Ты Тайный Санта для: Дмитрий Фрижикини @Dmitry_fq. Передали пожелание: Книгу, которую ты считаешь маст хэв""",
          """Привет! Ты Тайный Санта для: Павел Калугин @Pavel_Kalugin. Передали пожелание: Люблю все собирать и разбирать(но не пазлы), машинки и лего, звездных воинов, любою майки и носки с прикольным принтом! А вообще любому подарку буду рад!""",
          ]

@bot.message_handler(commands=['ten'])
def send_messages(message):
    for user_id, text in zip(user_auis, santas):
        try:
            bot.send_message(user_id, text)
            logging.info(f"Sent message '{text}' to user {user_id}")
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")


# Обработчик команды /nine
@bot.message_handler(commands=['nine'])
def cmd_nine(message):
    send_question_to_all_users()


# Функция рассылки вопроса
def send_question_to_all_users():
    for user_id in user_ids:
        try:
            user = bot.get_chat(user_id)
            username = user.username

            msg = bot.send_message(user_id, question)
            logging.info(f"Пользователь {username} ({user_id}) плдучил вопрос")
            time.sleep(1)
            bot.register_next_step_handler(msg, process_response)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


# Обработчик ответов
def process_response(message):
    user_id = message.from_user.id
    username = message.from_user.username
    response = message.text

    logging.info(f"Пользователь {username} ({user_id}) ответил: {response}")

    responses[user_id] = {'username': username, 'response': response}


# Function to keep the bot running
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=5)
        except Exception as e:
            print(f"Error in polling: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_bot()
