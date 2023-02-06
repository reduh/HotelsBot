import telebot
from telebot import types, async_telebot
from datetime import datetime
import functools
import json
import random
import asyncio
import aiohttp
from collections.abc import Callable
from telebot.types import Message, CallbackQuery


class HotelBot:
    """
    Телеграм-бот, работающий с HotelAPI для поиска отелей.

    Args:
      telegram_token (str): токен телеграм-бота.
      api_key (str): ключ для HotelAPI.
    """

    # ---------------------------------------------[__init__]---------------------------------------------<Begin>

    def __init__(self, telegram_token: str, api_key: str) -> None:
        self.__bot = async_telebot.AsyncTeleBot(telegram_token)
        self.__api_key = api_key
        self.__data = dict()
        self.__history = dict()
        self.__last_keyboard_id = dict()
        self.__next_message_handler_data = dict()
        self.__bestdeal_settings = dict()
        self.__main_settings = dict()

        # Handlers

        @self.__bot.message_handler(func=lambda message: message.chat.id in self.__next_message_handler_data.keys())
        async def _next_step_handler(message: Message) -> None:
            await self.__next_step_handler(message)

        @self.__bot.message_handler(commands=['start', 'help'])
        async def _start(message: Message) -> None:
            await self.__start(message)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'ec_no')
        async def _callback_ec_no(call: CallbackQuery) -> None:
            await self.__callback_ec_no(call)

        @self.__bot.message_handler(commands=['reg'])
        async def _reg(message: Message) -> None:
            await self.__reg(message)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'checkIn')
        async def _callback_checkIn(call: CallbackQuery) -> None:
            await self.__callback_checkIn(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'checkOut')
        async def _callback_checkOut(call: CallbackQuery) -> None:
            await self.__callback_checkOut(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('room'))
        async def _callback_room(call: CallbackQuery) -> None:
            await self.__callback_room(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'add_room')
        async def _callback_add_room(call: CallbackQuery) -> None:
            await self.__callback_add_room(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'reset')
        async def _callback_reset(call: CallbackQuery) -> None:
            await self.__callback_reset(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'exit_reg')
        async def _callback_exit_reg(call: CallbackQuery) -> None:
            await self.__callback_exit_reg(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('adult'))
        async def _callback_adult(call: CallbackQuery) -> None:
            await self.__callback_adult(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('child'))
        async def _callback_child(call: CallbackQuery) -> None:
            await self.__callback_child(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('remove_child'))
        async def _callback_remove_child(call: CallbackQuery) -> None:
            await self.__callback_remove_child(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('add_child'))
        async def _callback_add_child(call: CallbackQuery) -> None:
            await self.__callback_add_child(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('remove_room'))
        async def _callback_remove_room(call: CallbackQuery) -> None:
            await self.__callback_remove_room(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'exit_room')
        async def _callback_exit_room(call: CallbackQuery) -> None:
            await self.__callback_exit_room(call)

        @self.__bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
        async def _main_commands(message: Message) -> None:
            await self.__main_commands(message)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('bestdeal_menu'))
        async def _callback_bestdeal_menu(call: CallbackQuery) -> None:
            await self.__callback_bestdeal_menu(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('bestdeal_filters'))
        async def _callback_bestdeal_filters(call: CallbackQuery) -> None:
            await self.__callback_bestdeal_filters(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'bestdeal_change_sort')
        async def _callback_bestdeal_change_sort(call: CallbackQuery) -> None:
            await self.__callback_bestdeal_change_sort(call)

        @self.__bot.callback_query_handler(
            func=lambda call: call.data.startswith('main_city') or call.data == 'bestdeal_exit')
        async def _callback_main_city(call: CallbackQuery) -> None:
            await self.__callback_main_city(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'photo_yes')
        async def _callback_photo_yes(call: CallbackQuery) -> None:
            await self.__callback_photo_yes(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'photo_no')
        async def _callback_photo_no(call: CallbackQuery) -> None:
            await self.__callback_photo_no(call)

        @self.__bot.callback_query_handler(func=lambda call: call.data == 'result_error')
        async def _callback_result_error(call: CallbackQuery) -> None:
            await self.__callback_result_error(call)

        @self.__bot.message_handler(commands=['history'])
        async def _get_history(message: Message) -> None:
            await self.__get_history(message)

        @self.__bot.callback_query_handler(func=lambda call: call.data.startswith('h_photo'))
        async def _callback_h_photo(message: Message) -> None:
            await self.__callback_h_photo(message)

    # ---------------------------------------------[__init__]---------------------------------------------<End>

    def __register_next_step_handler(self, message: Message, func: Callable, *args, **kwargs) -> None:
        """
        Метод, реализующий telebot.TeleBot.register_next_step_handler для async_telebot.AsyncTeleBot.

        :param:
          message (Message): сообщение.
          func (Callable): регистрируемая функция.
          args (list), kwargs (dict): аргументы func.
        """
        self.__next_message_handler_data[message.chat.id] = [func, args, kwargs]

    async def __next_step_handler(self, message: Message) -> None:
        """
        Метод, вызывающий зарегистрированную через __register_next_step_handler метод func.

        :param:
          message (Message): сообщение.
        """
        func, args, kwargs = self.__next_message_handler_data.pop(message.chat.id)
        await func(message, *args, **kwargs)

    def __clear_step_handler_by_chat_id(self, chat_id: int) -> None:
        """
        Метод, реализующий telebot.TeleBot.clear_step_handler_by_chat_id для async_telebot.AsyncTeleBot.

        :param:
          chat_id (int): id чата.
        """
        try:
            self.__next_message_handler_data.pop(chat_id)
        except:
            pass

    def __callback_func(func: Callable) -> Callable:

        functools.wraps(func)

        async def wrapped_func(self, call: CallbackQuery) -> None:
            self.__last_keyboard_id[call.message.chat.id] = None

            try:
                await self.__bot.delete_message(call.message.chat.id, call.message.id)
                await func(self, call)
            except Exception as err:
                print(err)
                await self.__bot.send_message(call.message.chat.id, '\U00002620 Ошибка.\U00002620')

        wrapped_func.__name__ = func.__name__
        wrapped_func.__doc__ = func.__doc__
        return wrapped_func

    def __command_func(func: Callable) -> Callable:

        functools.wraps(func)

        async def wrapped_func(self, message: Message) -> None:
            try:
                if self.__last_keyboard_id[message.chat.id] != None:
                    await self.__bot.delete_message(message.chat.id, self.__last_keyboard_id[message.chat.id])
            except:
                pass

            try:
                if self.__history[message.chat.id][-1:].get('hotels') == None:
                    self.__history[message.chat.id].pop(len(self.__history[message.chat.id]) - 1)
            except:
                pass

            try:
                await func(self, message)
            except Exception as err:
                print(err)
                await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')

        wrapped_func.__name__ = func.__name__
        wrapped_func.__doc__ = func.__doc__
        return wrapped_func

    async def __start(self, message: Message) -> None:
        """
        Метод, отвечающий командам (start, help).

        :param:
          message (Message): сообщение.
        """
        await self.__bot.send_message(message.chat.id,
                                      "Вы можете ввести следующие комманды:\n\n/start или /help для получения помощи по командам.\n\n/reg для регистрации своих данных. Для использования основных команд (lowprice и т.д.) вам потребуется как минимум заполнить даты заселения и выселения.\n\n/lowprice для поиска самых дешевых отелей в желаемом городе.\n\n/highprice для поиска самых дорогих отелей в желаемом городе.\n\n/bestdeal для поиска самых дешевых и\\или самых близких к центру отелей в желаемом городе. Доступно 3 вида сортировки: по цене, по расстоянию, по цене и расстоянию.\n\n/history для вывода истории ваших поисков.")

    # -----------------------------------(errorContinue)-----------------------------------<Begin>

    async def __errorContinue(self, chat_id: int, call_data: str) -> None:
        """
        Метод, который при возникновении ошибки во время ввода возвращает бота на предыдущий шаг с вызовом call_data или прерывает последовательность действий.

        :param:
          chat_id (int): id чата.
          call_data (str): название вызова.
        """
        ec_keyboard = types.InlineKeyboardMarkup()

        # Button: call_data
        ec_keyboard.row(types.InlineKeyboardButton(text='Да', callback_data=call_data))
        # Button: ec_no
        ec_keyboard.row(types.InlineKeyboardButton(text='Нет', callback_data='ec_no'))

        self.__last_keyboard_id[chat_id] = (
            await self.__bot.send_message(chat_id, "Ввести снова?", reply_markup=ec_keyboard)).id

    # Callback: ec_no
    async def __callback_ec_no(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке ec_no.

        :param:
          call (CallbackQuery): вызов.
        """
        self.__last_keyboard_id[call.message.chat.id] = None

        try:
            self.__main_settings.pop(call.message.chat.id)
        except:
            pass

        try:
            await self.__bot.delete_message(call.message.chat.id, call.message.id)
        except Exception as err:
            print(err)
            await self.__bot.send_message(call.message.chat.id, '\U00002620 Ошибка.\U00002620')

    # -----------------------------------(errorContinue)-----------------------------------<End>

    # ---------------------------------------------[/reg]---------------------------------------------<Begin>

    # -----------------------------------(reg_menu)-----------------------------------<Begin>

    @__command_func
    async def __reg(self, message: Message) -> None:
        """
        Метод, открывающий меню регистрации.

        :param:
          message (Message): сообщение.
        """
        self.__data[message.chat.id] = self.__data.get(message.chat.id,
                                                       {'in': None, 'out': None, 'rooms': [[1, []]], 'count': 1})
        reg_keyboard = types.InlineKeyboardMarkup()

        # Button: checkIn, checkOut
        reg_keyboard.row(types.InlineKeyboardButton(text='Въезд: ' + (
            str(self.__data[message.chat.id]['in']) if self.__data[message.chat.id]['in'] else 'Неопределенно'),
                                                    callback_data='checkIn'), types.InlineKeyboardButton(
            text='Выезд: ' + (
                str(self.__data[message.chat.id]['out']) if self.__data[message.chat.id]['out'] else 'Неопределенно'),
            callback_data='checkOut'))
        # Button: room[0..n]
        row = []
        for i, room in enumerate(self.__data[message.chat.id]['rooms']):
            if len(row) == 2:
                reg_keyboard.row(*row)
                row.clear()
            row.append(types.InlineKeyboardButton(text=f"Комната {i + 1}: {room[0]} взр, {len(room[1])} дет",
                                                  callback_data=f'room{i}'))
        reg_keyboard.row(*row)
        # Button: add_room
        if len(self.__data[message.chat.id]['rooms']) < 8 and self.__data[message.chat.id]['count'] < 20:
            reg_keyboard.row(
                types.InlineKeyboardButton(text='Добавить комнату (максимум 8 комнат)', callback_data='add_room'))
        # Button: reset
        reg_keyboard.row(types.InlineKeyboardButton(text='Сбросить информацию', callback_data='reset'))
        # Button: exit_reg
        reg_keyboard.row(types.InlineKeyboardButton(text='Готово', callback_data='exit_reg'))

        self.__last_keyboard_id[message.chat.id] = (await self.__bot.send_message(message.chat.id, (
            'Достигнут максимум людей в комнатах.\n' if self.__data[message.chat.id][
                                                            'count'] >= 20 else '') + "Ваша текущая информация:",
                                                                                  reply_markup=reg_keyboard)).id

        # Callback: checkIn

    @__callback_func
    async def __callback_checkIn(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке checkIn.

        :param:
          call (CallbackQuery): вызов.
        """
        message = await self.__bot.send_message(call.message.chat.id, 'Введите дату заселения (dd.mm.yyyy):')
        self.__register_next_step_handler(message, self.__checkIn)

    # Method: checkIn
    async def __checkIn(self, message: Message) -> None:
        """
        Метод, выполняющий проверку и запись даты заселения.

        :param:
          message (Message): сообщение.
        """
        try:
            result = datetime.strptime(message.text, '%d.%m.%Y').date()
            if datetime.today().date() > result:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nДата заселения должна быть больше или равна сегодняшней дате.')
            elif self.__data[message.chat.id]['out'] and self.__data[message.chat.id]['out'] < result:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nДата выселения должна быть больше или равна дате заселения.')
            else:
                self.__data[message.chat.id]['in'] = result
        except ValueError:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nНеправильный формат даты.')
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')
        await self.__reg(message)

    # Callback: checkOut
    @__callback_func
    async def __callback_checkOut(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке checkOut.

        :param:
          call (CallbackQuery): вызов.
        """
        message = await self.__bot.send_message(call.message.chat.id, 'Введите дату выселения (dd.mm.yyyy):')
        self.__register_next_step_handler(message, self.__checkOut)

    # Method: checkOut
    async def __checkOut(self, message: Message) -> None:
        """
        Метод, выполняющий проверку и запись даты выселения.

        :param:
          message (Message): сообщение.
        """
        try:
            result = datetime.strptime(message.text, '%d.%m.%Y').date()
            if datetime.today().date() > result:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nДата выселения должна быть больше или равна сегодняшней дате.')
            elif self.__data[message.chat.id]['in'] and self.__data[message.chat.id]['in'] > result:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nДата выселения должна быть больше или равна дате заселения.')
            else:
                self.__data[message.chat.id]['out'] = result
        except ValueError:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nНеправильный формат даты.')
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')
        await self.__reg(message)

    # Callback: room[0..n]
    @__callback_func
    async def __callback_room(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке room[0..n].

        :param:
          call (CallbackQuery): вызов.
        """
        await self.__reg_room(call.message, int(call.data[4:]))

    # Callback: add_room
    @__callback_func
    async def __callback_add_room(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке add_room.

        :param:
          call (CallbackQuery): вызов.
        """
        if self.__data[call.message.chat.id]['count'] >= 20:
            await self.__bot.send_message(call.message.chat.id,
                                          '\U00002620 Ошибка.\U00002620 \nВ команте должен быть минимум 1 человек.\nЛюдей должно быть суммарно не больше 20.')
        else:
            self.__data[call.message.chat.id]['rooms'].append([1, []])
            self.__data[call.message.chat.id]['count'] += 1
        await self.__reg(call.message)

    # Callback: reset
    @__callback_func
    async def __callback_reset(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке reset.

        :param:
          call (CallbackQuery): вызов.
        """
        self.__data[call.message.chat.id] = {'in': None, 'out': None, 'rooms': [[1, []]], 'count': 1}
        await self.__reg(call.message)

    # Callback: exit_reg
    async def __callback_exit_reg(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке exit_reg.

        :param:
          call (CallbackQuery): вызов.
        """
        self.__last_keyboard_id[call.message.chat.id] = None

        try:
            await self.__bot.delete_message(call.message.chat.id, call.message.id)
        except Exception as err:
            print(err)
            await self.__bot.send_message(call.message.chat.id, '\U00002620 Ошибка.\U00002620')

    # -----------------------------------(reg_menu)-----------------------------------<End>

    # -----------------------------------(reg_room_menu)-----------------------------------<Begin>

    async def __reg_room(self, message: Message, n: int) -> None:
        """
        Метод, открывающий меню регистрации комнаты.

        :param:
          message (Message): сообщение.
          n (int): индекс комнаты.
        """
        room_keyboard = types.InlineKeyboardMarkup()

        # Button: adult[n]
        room_keyboard.row(types.InlineKeyboardButton(text=f"Взрослых: {self.__data[message.chat.id]['rooms'][n][0]}.",
                                                     callback_data=f'adult{n}'))
        # Button: child[0..n]_[0..m]
        row = []
        for i, age in enumerate(self.__data[message.chat.id]['rooms'][n][1]):
            if len(row) == 2:
                room_keyboard.row(*row)
                row.clear()
            row.append(types.InlineKeyboardButton(text=f"Ребенок: {age if age > 0 else '< 1'} лет",
                                                  callback_data=f'child{n}_{i}'))
        room_keyboard.row(*row)
        # Button: add_child[n]
        if len(self.__data[message.chat.id]['rooms'][n][1]) < 6 and self.__data[message.chat.id]['count'] < 20:
            room_keyboard.row(
                types.InlineKeyboardButton(text="Добавить ребенка (максимум 6)", callback_data=f'add_child{n}'))
        # Button: remove_room[n]
        if len(self.__data[message.chat.id]['rooms']) > 1:
            room_keyboard.row(types.InlineKeyboardButton(text="Удалить комнату", callback_data=f'remove_room{n}'))
        # Button: exit_room
        room_keyboard.row(types.InlineKeyboardButton(text="Назад", callback_data='exit_room'))

        self.__last_keyboard_id[message.chat.id] = (await self.__bot.send_message(message.chat.id,
                                                                                  f"Количетсво людей во всех комнатах {self.__data[message.chat.id]['count']} (максимум 20)\nКомната {n + 1}: {self.__data[message.chat.id]['rooms'][n][0]} взрослых, {len(self.__data[message.chat.id]['rooms'][n][1])} детей.",
                                                                                  reply_markup=room_keyboard)).id

    # Callback: adult[n]
    @__callback_func
    async def __callback_adult(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке adult[n].

        :param:
          call (CallbackQuery): вызов.
        """
        message = await self.__bot.send_message(call.message.chat.id, 'Введите количество взрослых:')
        self.__register_next_step_handler(message, self.__set_adult, int(call.data[5:]))

    # Method: adult[n]
    async def __set_adult(self, message: Message, n: int) -> None:
        """
        Метод, выполняющий проверку и запись количества взрослых в комнате n.

        :param:
          message (Message): сообщение.
          n (int): индекс комнаты.
        """
        try:
            result = int(message.text)
            if result < 1:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nТребуется минимум 1 взрослый в комнате.')
            elif self.__data[message.chat.id]['count'] + result - self.__data[message.chat.id]['rooms'][n][0] > 20:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nЛюдей должно быть суммарно не больше 20.')
            else:
                self.__data[message.chat.id]['count'] += result - self.__data[message.chat.id]['rooms'][n][0]
                self.__data[message.chat.id]['rooms'][n][0] = result
        except ValueError:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nОшибка ввода.')
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')
        await self.__reg_room(message, n)

    # Callback: child[n]_[0..m]
    @__callback_func
    async def __callback_child(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке child[n]_[0..m].

        :param:
          call (CallbackQuery): вызов.
        """
        n, m = map(int, call.data[5:].split('_'))
        child_keyboard = types.InlineKeyboardMarkup()

        # Button: remove_child[n]_[m]
        child_keyboard.row(
            types.InlineKeyboardButton(text='Убрать выбранного ребенка.', callback_data=f"remove_child{n}_{m}"))

        message = await self.__bot.send_message(call.message.chat.id,
                                                'Введите возраст ребенка (от 0 до 17) в чат или уберите его, нажав на кнопку:',
                                                reply_markup=child_keyboard)
        self.__register_next_step_handler(message, self.__set_child, n, m, message)

    # Callback: remove_child[n]_[m]
    @__callback_func
    async def __callback_remove_child(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке remove_child[n]_[m].

        :param:
          call (CallbackQuery): вызов.
        """
        n, m = map(int, call.data[12:].split('_'))
        self.__data[call.message.chat.id]['rooms'][n][1].pop(m)
        self.__data[call.message.chat.id]['count'] -= 1
        self.__clear_step_handler_by_chat_id(call.message.chat.id)
        await self.__reg_room(call.message, n)

    # Method: child[n]_[0..m]
    async def __set_child(self, message: Message, n: int, m: int, msg: Message) -> None:
        """
        Метод, выполняющий проверку и запись возраста ребенка m из комнаты n.

        :param:
          message (Message): сообщение.
          n (int): индекс комнаты.
          m (int): индекс ребенка.
          msg (Message): предыдущие сообщение. Требуется для удаления клавиатуры.
        """
        await self.__bot.edit_message_reply_markup(chat_id=msg.chat.id, message_id=msg.id, reply_markup=None)
        try:
            result = int(message.text)
            if result < 0 or result > 17:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nВозраст ребенка должен быть от 0 до 17.')
            else:
                self.__data[message.chat.id]['rooms'][n][1][m] = result
        except ValueError:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nОшибка ввода.')
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')
        await self.__reg_room(message, n)

    # Callback: add_child[n]
    @__callback_func
    async def __callback_add_child(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке add_child[n].

        :param:
          call (CallbackQuery): вызов.
        """
        n = int(call.data[9:])
        self.__data[call.message.chat.id]['rooms'][n][1].append(0)
        self.__data[call.message.chat.id]['count'] += 1
        await self.__reg_room(call.message, n)

    # Callback: remove_room[n]
    @__callback_func
    async def __callback_remove_room(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке remove_room[n].

        :param:
          call (CallbackQuery): вызов.
        """
        n = int(call.data[11:])
        self.__data[call.message.chat.id]['count'] -= self.__data[call.message.chat.id]['rooms'][n][0] + len(
            self.__data[call.message.chat.id]['rooms'][n][1])
        self.__data[call.message.chat.id]['rooms'].pop(n)
        await self.__reg(call.message)

    # Callback: exit_room
    @__callback_func
    async def __callback_exit_room(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке exit_reg.

        :param:
          call (CallbackQuery): вызов.
        """
        await self.__reg(call.message)

    # -----------------------------------(reg_room_menu)-----------------------------------<End>

    # ---------------------------------------------[/reg]---------------------------------------------<End>

    # ---------------------------------------------[main]---------------------------------------------<Begin>

    @__command_func
    async def __main_commands(self, message: Message) -> None:
        """
        Метод, отвечающий основным командам (lowprice, highprice, bestdeal) бота.

        :param:
          message (Message): сообщение.
        """
        try:
            if self.__data[message.chat.id]['in'] == None or self.__data[message.chat.id]['out'] == None:
                raise Exception

            msg = await self.__bot.send_message(message.chat.id, 'Введите название города:')
            self.__history[message.chat.id] = self.__history.get(message.chat.id, []) + [
                {'command': message.text, 'time': datetime.fromtimestamp(message.date)}]
            self.__main_settings[message.chat.id] = {'mode': message.text[1:]}
            self.__register_next_step_handler(msg, self.__main_city)
        except:
            await self.__bot.send_message(message.chat.id,
                                          '\U00002620 Ошибка.\U00002620 \nПройдите регистрацию своей информации (/reg).')

    async def __main_city(self, message: Message) -> None:
        """
        Метод, который ищет города с названием message.text в https://hotels4.p.rapidapi.com/locations/v3/search.

        :param:
          message (Message): сообщение.
        """
        try:
            url = "https://hotels4.p.rapidapi.com/locations/v3/search"
            querystring = {"q": message.text}
            headers = {"X-RapidAPI-Key": self.__api_key, "X-RapidAPI-Host": "hotels4.p.rapidapi.com"}

            async with aiohttp.ClientSession() as session:
                response = await session.request("GET", url, headers=headers, params=querystring)
            text = await response.text()

            cities = []
            json.loads(text)['sr']

            for obj in json.loads(text)['sr']:
                if obj['type'] == 'CITY':
                    cities.append(obj)

            if len(cities) == 0:

                await self.__bot.send_message(message.chat.id, f"Город '{message.text}' не найден.")
            else:
                city_keyboard = types.InlineKeyboardMarkup()

                # Button: bestdeal_menu[gaiaId], main_city[gaiaId]
                for city in cities:
                    city_keyboard.row(types.InlineKeyboardButton(text=city['regionNames']['displayName'],
                                                                 callback_data=(('bestdeal_menu' if
                                                                                 self.__main_settings[message.chat.id][
                                                                                     'mode'] == 'bestdeal' else 'main_city') + f"{city['gaiaId']}")))

                self.__last_keyboard_id[message.chat.id] = (
                    await self.__bot.send_message(message.chat.id, "Выберите город из списка найденных:",
                                                  reply_markup=city_keyboard)).id
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \n')

    # -----------------------------------(/bestdeal)-----------------------------------<Begin>

    # Callback: bestdeal_menu[gaiaId]
    @__callback_func
    async def __callback_bestdeal_menu(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке bestdeal_menu[gaiaId].

        :param:
          call (CallbackQuery): вызов.
        """
        self.__main_settings[call.message.chat.id]['cityId'] = call.data[13:]
        await self.__bestdeal_menu(call.message.chat.id)

    async def __bestdeal_menu(self, chat_id: int) -> None:
        """
        Метод, выполняющийся в случае введения команды bestdeal после выбора города. Открывает меню с настройками bestdeal.

        :param:
          chat_id (int): id чата.
        """
        self.__bestdeal_settings[chat_id] = self.__bestdeal_settings.get(chat_id, {'price': {'min': None, 'max': None},
                                                                                   'dist': {'min': None, 'max': None},
                                                                                   'sort': 0})

        bestdeal_keyboard = types.InlineKeyboardMarkup()

        # Button: bestdeal_filters[price]_[min], bestdeal_filters[price]_[max]
        bestdeal_keyboard.row(
            types.InlineKeyboardButton(text=f"Мин. цена ($): {self.__bestdeal_settings[chat_id]['price']['min']}",
                                       callback_data='bestdeal_filtersprice_min'),
            types.InlineKeyboardButton(text=f"Макс. цена ($): {self.__bestdeal_settings[chat_id]['price']['max']}",
                                       callback_data='bestdeal_filtersprice_max'))
        # Button: bestdeal_filters[dist]_[min], bestdeal_filters[dist]_[max]
        bestdeal_keyboard.row(
            types.InlineKeyboardButton(text=f"Мин. дистанция (км): {self.__bestdeal_settings[chat_id]['dist']['min']}",
                                       callback_data='bestdeal_filtersdist_min'),
            types.InlineKeyboardButton(text=f"Макс. дистанция (км): {self.__bestdeal_settings[chat_id]['dist']['max']}",
                                       callback_data='bestdeal_filtersdist_max'))
        # Button: bestdeal_change_sort
        bestdeal_keyboard.row(types.InlineKeyboardButton(
            text='Сортировка по %sцене и дистанции, %sцене, %sдистанции' % tuple(
                map(lambda sort: '\U00002705' * (self.__bestdeal_settings[chat_id]['sort'] == sort), (0, 1, 2))),
            callback_data='bestdeal_change_sort'))
        # Button: bestdeal_exit
        bestdeal_keyboard.row(types.InlineKeyboardButton(text='Готово', callback_data='bestdeal_exit'))

        self.__last_keyboard_id[chat_id] = (await self.__bot.send_message(chat_id, 'Ваши текущие настройки bestdeal:',
                                                                          reply_markup=bestdeal_keyboard)).id

    # Callback: bestdeal_filters[price]_[min], bestdeal_filters[price]_[max], bestdeal_filters[dist]_[min], bestdeal_filters[dist]_[max]
    @__callback_func
    async def __callback_bestdeal_filters(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопкам bestdeal_filters[price]_[min], bestdeal_filters[price]_[max], bestdeal_filters[dist]_[min], bestdeal_filters[dist]_[max].

        :param:
          call (CallbackQuery): вызов.
        """
        p_d, min_max = call.data[16:].split('_')
        message = await self.__bot.send_message(call.message.chat.id,
                                                f"Введите {'минимальную' if min_max == 'min' else 'максимальную'} {'цену' if p_d == 'price' else 'дистанцию'}:")
        self.__register_next_step_handler(message, self.__bestdeal_filters, p_d, min_max)

    async def __bestdeal_filters(self, message: Message, p_d: str, min_max: str) -> None:
        """
        Метод, выполняющий проверку и запись выбранного для настройки фильтра для bestdeal.

        :param:
          message (Message): сообщение.
          p_d (str): выбранная настройка из price\dist.
          min_max (str): выбранная настройка из min\max.
        """
        try:
            min_max = ['min', 'max'] if min_max == 'min' else ['max', 'min']
            result = float(message.text)

            if result < 0:
                await self.__bot.send_message(message.chat.id,
                                              f"\U00002620 Ошибка.\U00002620 \n{'Цена' if p_d == 'price' else 'Дистанция'} не может быть меньше 0.")
            elif self.__bestdeal_settings[message.chat.id][p_d][min_max[1]] and (
                    (min_max[1] == 'max' and self.__bestdeal_settings[message.chat.id][p_d][min_max[1]] < result) or (
                    min_max[1] == 'min' and self.__bestdeal_settings[message.chat.id][p_d][min_max[1]] > result)):
                await self.__bot.send_message(message.chat.id,
                                              f"\U00002620 Ошибка.\U00002620 \nМинимальная {'цена' if p_d == 'price' else 'дистанция'} должна быть не больше максимальной.")
            else:
                self.__bestdeal_settings[message.chat.id][p_d][min_max[0]] = result
        except ValueError:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nНеправильный формат даты.')
        except Exception as err:
            print(err)
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620')

        await self.__bestdeal_menu(message.chat.id)

    # Callback: bestdeal_change_sort
    @__callback_func
    async def __callback_bestdeal_change_sort(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке bestdeal_change_sort.

        :param:
          call (CallbackQuery): вызов.
        """
        self.__bestdeal_settings[call.message.chat.id]['sort'] = (self.__bestdeal_settings[call.message.chat.id][
                                                                      'sort'] + 1) % 3

        await self.__bestdeal_menu(call.message.chat.id)

    # -----------------------------------(/bestdeal)-----------------------------------<End>

    # Callback: bestdeal_exit, main_city[gaiaId]
    @__callback_func
    async def __callback_main_city(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопкам bestdeal_exit, main_city[gaiaId].

        :param:
          call (CallbackQuery): вызов.
        """
        self.__main_settings[call.message.chat.id]['cityId'] = self.__main_settings[call.message.chat.id].get('cityId',
                                                                                                              call.data[
                                                                                                              9:])
        msg = await self.__bot.send_message(call.message.chat.id, 'Введите колчество отелей (максимум 5):')
        self.__register_next_step_handler(msg, self.__main_hotels, call.data)

    async def __main_hotels(self, message: Message, call_data: str) -> None:
        """
        Метод, выполняющий проверку и запись желаемого количества отелей для поиска. Максимум 5.

        :param:
          message (Message): сообщение.
          call_data (str): название вызова предыдущего шага.
        """
        try:
            hotels = int(message.text)

            if hotels < 1:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nКоличество должно быть больше 0.')
                await self.__errorContinue(message.chat.id, call_data)
            elif hotels > 5:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nКоличество должно быть не больше 5.')
                await self.__errorContinue(message.chat.id, call_data)
            else:
                self.__main_settings[message.chat.id]['hotels'] = hotels
                photo_keyboard = types.InlineKeyboardMarkup()

                # Button: photo_yes
                photo_keyboard.row(types.InlineKeyboardButton(text='Да', callback_data='photo_yes'))
                # Button: photo_no
                photo_keyboard.row(types.InlineKeyboardButton(text='Нет', callback_data='photo_no'))

                self.__last_keyboard_id[message.chat.id] = (
                    await self.__bot.send_message(message.chat.id, "Показать фотографии отелей?",
                                                  reply_markup=photo_keyboard)).id
        except:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nОшибка ввода.')
            await self.__errorContinue(message.chat.id, call_data)

    # Callback: photo_yes
    @__callback_func
    async def __callback_photo_yes(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке photo_yes.

        :param:
          call (CallbackQuery): вызов.
        """
        msg = await self.__bot.send_message(call.message.chat.id, 'Введите колчество фотографий (максимум 5):')
        self.__register_next_step_handler(msg, self.__main_photo, call.data)

    # Callback: photo_no
    @__callback_func
    async def __callback_photo_no(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке photo_no.

        :param:
          call (CallbackQuery): вызов.
        """
        self.__main_settings[call.message.chat.id]['photo'] = 0
        await self.__main_result(call.message.chat.id)

    async def __main_photo(self, message: Message, call_data: str) -> None:
        """
        Метод, выполняющий проверку и запись желаемого количества фотографий отелей для поиска. Максимум 5.

        :param:
          message (Message): сообщение.
          call_data (str): название вызова предыдущего шага.
        """
        try:
            photo = int(message.text)

            if photo < 0:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nКоличество должно быть не меньше 0.')
                await self.__errorContinue(message.chat.id, call_data)
                return
            elif photo > 5:
                await self.__bot.send_message(message.chat.id,
                                              '\U00002620 Ошибка.\U00002620 \nКоличество должно быть не больше 5.')
                await self.__errorContinue(message.chat.id, call_data)
                return
        except:
            await self.__bot.send_message(message.chat.id, '\U00002620 Ошибка.\U00002620 \nОшибка ввода.')
            await self.__errorContinue(message.chat.id, call_data)
            return

        self.__main_settings[message.chat.id]['photo'] = photo
        await self.__main_result(message.chat.id)

    async def __main_result(self, chat_id: int) -> None:
        """
        Метод, который ищет подходящие к выбранным настройкам отели в https://hotels4.p.rapidapi.com/properties/v2/list.

        :param:
          chat_id (int): id чата.
        """
        url = "https://hotels4.p.rapidapi.com/properties/v2/list"

        payload = dict()

        payload['destination'] = {'regionId': self.__main_settings[chat_id]['cityId']}
        payload['checkInDate'] = {
            'day': self.__data[chat_id]['in'].day,
            'month': self.__data[chat_id]['in'].month,
            'year': self.__data[chat_id]['in'].year
        }
        payload['checkOutDate'] = {
            "day": self.__data[chat_id]['out'].day,
            "month": self.__data[chat_id]['out'].month,
            "year": self.__data[chat_id]['out'].year
        }
        payload['rooms'] = []
        for room in self.__data[chat_id]['rooms']:
            payload['rooms'].append({
                'adults': room[0],
                'children': list(map(lambda age: {'age': age}, room[1]))
            })
        payload['resultsStartingIndex'] = 0
        payload['resultsSize'] = self.__main_settings[chat_id]['hotels'] if self.__main_settings[chat_id][
                                                                                'mode'] == 'lowprice' else 200
        payload['sort'] = 'PROPERTY_CLASS' if self.__main_settings[chat_id][
                                                  'mode'] == 'highprice' else 'PRICE_LOW_TO_HIGH'
        payload['filters'] = {'price': {'min': 1, 'max': 999999}}

        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.__api_key,
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }

        try:
            if self.__main_settings[chat_id]['mode'] == 'bestdeal':
                response = await self.__bestdeal_result(chat_id, url, payload, headers)
            else:
                async with aiohttp.ClientSession() as session:
                    response = json.loads(
                        await (await session.request("POST", url, json=payload, headers=headers)).text())
                    response = response['data']['propertySearch']['properties'] if response['data'] else []

            if len(response) == 0:
                await self.__bot.send_message(chat_id, 'Отелей по запросу не найдено.')
                return

            if self.__main_settings[chat_id]['mode'] == 'highprice':
                response = sorted(response, key=lambda item: item['price']['lead']['amount'])[
                           -self.__main_settings[chat_id]['hotels']:][::-1]

            hotels_log = []

            for hotel in response:
                name = hotel['name']
                price = hotel['price']['lead']['formatted']
                dist = round(hotel['destinationInfo']['distanceFromDestination']['value'] / 0.621371, 2)
                address, photoes = await self.__hotel_detail(hotel['id'], self.__main_settings[chat_id]['photo'])

                await self.__bot.send_message(chat_id,
                                              f"Название: {name}\nЦена: {price}\nДистанция от центра (км): {dist}\nАдрес: {address}")

                if len(photoes):
                    await self.__bot.send_media_group(chat_id, list(map(telebot.types.InputMediaPhoto, photoes)))

                hotels_log.append({'name': name, 'price': price, 'dist': dist, 'address': address, 'photoes': photoes})

            self.__history[chat_id][len(self.__history[chat_id]) - 1].update({'hotels': hotels_log})
        except Exception as err:
            print(err)
            error_keyboard = types.InlineKeyboardMarkup()

            # Button: result_error
            error_keyboard.row(types.InlineKeyboardButton(text='Да', callback_data='result_error'))
            # Button: ec_no
            error_keyboard.row(types.InlineKeyboardButton(text='Нет', callback_data='ec_no'))

            self.__last_keyboard_id[chat_id] = (await self.__bot.send_message(chat_id,
                                                                              '\U00002620 API не отвечает на запрос. \U00002620 \nХотите повторить попытку?',
                                                                              reply_markup=error_keyboard)).id

    async def __bestdeal_result(self, chat_id: int, url: str, payload: dict, headers: dict):
        """
        Метод, специализированный на поиске отелей для команды bestdeal.
        Методы сортировки по индексам:
          0. По цене от меньшего к большему.
          1. По расстоянию от центра от меньшего к большему.
          2. По цене и расстоянию. Специальный метод сортировки, который отбирает отели одновременно из двух списков, рассортированных один по цене, другой по расстоянию, выбирая те, которые появились в обоих списках раньше остальных.

        :param:
          chat_id (int): id чата.
          url (str): ссылка на API.
          payload (dict): настройки поиска.
          headers (dict): ключи для поиска.
        """

        async def bestdeal_get_response(sort: str) -> None:
            """
            Метод для сортировки [0], запрашивающий следущие отели, начиная с индекса starting_index[sort], для списка sort.

            sort (str): сортировка списка (price\dist).
            """
            payload['sort'] = 'PRICE_LOW_TO_HIGH' if sort == 'price' else 'DISTANCE'
            payload['resultsStartingIndex'] = starting_index[sort]
            async with aiohttp.ClientSession() as session:
                response[sort] = json.loads(
                    await (await session.request("POST", url, json=payload, headers=headers)).text())
                response[sort] = response[sort]['data']['propertySearch']['properties'] if response[sort][
                    'data'] else []
            if len(response[sort]) == 0:
                end[sort] = True
            else:
                can_continue[sort] = len(response[sort]) == 200
                response[sort] = list(filter(
                    lambda hotel: dist['min'] <= hotel['destinationInfo']['distanceFromDestination']['value'] <= dist[
                        'max'], response[sort]))

        async def bestdeal_next_hotel(sort: str) -> None:
            """
            Метод для сортировки [0], выбирающий следущий в списке sort отель и проверающий, если он появился в обоих списках.

            sort (str): сортировка списка (price\dist).
            """
            try:
                hotel = response[sort].pop(0)
                if hotel['id'] in hotels_found:
                    hotels.append(hotel)
                    if len(hotels) == self.__main_settings[chat_id]['hotels']:
                        return True
                else:
                    hotels_found.append(hotel['id'])
            except:
                if can_continue[sort]:
                    starting_index[sort] += 200
                    await bestdeal_get_response(sort)
                else:
                    end[sort] = True

        payload['filters']['price']['min'] = self.__bestdeal_settings[chat_id]['price']['min'] if \
        self.__bestdeal_settings[chat_id]['price']['min'] else 1
        payload['filters']['price']['max'] = self.__bestdeal_settings[chat_id]['price']['max'] if \
        self.__bestdeal_settings[chat_id]['price']['max'] else (
            999999 if self.__bestdeal_settings[chat_id]['price']['max'] == None else 1)
        dist = {'min': (self.__bestdeal_settings[chat_id]['dist']['min'] if self.__bestdeal_settings[chat_id]['dist'][
            'min'] else 0) * 0.621371, 'max': (self.__bestdeal_settings[chat_id]['dist']['max'] if
                                               self.__bestdeal_settings[chat_id]['dist'][
                                                   'max'] != None else 999999.0) * 0.621371}
        hotels = []

        if self.__bestdeal_settings[chat_id]['sort'] == 1:
            payload['sort'] = 'PRICE_LOW_TO_HIGH' if self.__bestdeal_settings[chat_id]['sort'] == 1 else 'DISTANCE'
            can_continue = True

            while can_continue:
                async with aiohttp.ClientSession() as session:
                    response = json.loads(
                        await (await session.request("POST", url, json=payload, headers=headers)).text())
                    response = response['data']['propertySearch']['properties'] if response['data'] else []
                if len(response) == 0:
                    break
                can_continue = len(response) == 200

                for hotel in response:
                    if dist['min'] <= hotel['destinationInfo']['distanceFromDestination']['value'] <= dist['max']:
                        hotels.append(hotel)
                        if len(hotels) == self.__main_settings[chat_id]['hotels']:
                            break
                else:
                    payload['resultsStartingIndex'] += 200
                    continue
                break

            return hotels
        elif self.__bestdeal_settings[chat_id]['sort'] == 2:
            payload['sort'] = 'PRICE_LOW_TO_HIGH' if self.__bestdeal_settings[chat_id]['sort'] == 1 else 'DISTANCE'
            can_continue = True

            while can_continue:
                async with aiohttp.ClientSession() as session:
                    response = json.loads(
                        await (await session.request("POST", url, json=payload, headers=headers)).text())
                response = response['data']['propertySearch']['properties'] if response['data'] else []
                if len(response) == 0:
                    break
                can_continue = len(response) == 200

                for hotel in response:
                    if hotel['destinationInfo']['distanceFromDestination']['value'] > dist['max']:
                        break
                    if dist['min'] <= hotel['destinationInfo']['distanceFromDestination']['value']:
                        hotels.append(hotel)
                        if len(hotels) == self.__main_settings[chat_id]['hotels']:
                            break
                else:
                    payload['resultsStartingIndex'] += 200
                    continue
                break

            return hotels
        else:
            response = dict()
            end = {'price': False, 'dist': False}
            can_continue = {'price': False, 'dist': False}
            starting_index = {'price': 0, 'dist': 0}
            hotels_found = []

            await bestdeal_get_response('price')
            await bestdeal_get_response('dist')

            while not end['price'] and not end['dist']:
                if await bestdeal_next_hotel('price') or await bestdeal_next_hotel('dist'):
                    break

            if len(hotels) == self.__main_settings[chat_id]['hotels'] or end['price'] == end['dist']:
                return hotels

            if end['price']:
                while not end['dist']:
                    if await bestdeal_next_hotel('dist'):
                        break
            else:
                while not end['price']:
                    if await bestdeal_next_hotel('price'):
                        break

            return hotels

    async def __hotel_detail(self, hotel_id: str, photo: int) -> list:
        """
        Метод, запрашивающий детали (адрес и фото) отеля с id hotel_id из https://hotels4.p.rapidapi.com/properties/v2/detail.

        :param:
          hotel_id (str): id отеля.
          photo (int): количество фото.

        :return:
          [address, photoes] (list[Any]): адрес и фото отеля.
        """
        url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

        payload = {"propertyId": hotel_id}

        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.__api_key,
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }

        async with aiohttp.ClientSession() as session:
            response = json.loads(await (await session.request("POST", url, json=payload, headers=headers)).text())

        address = response['data']['propertyInfo']['summary']['location']['address']['addressLine']

        gallery = response['data']['propertyInfo']['propertyGallery']['images']
        photoes = []
        for _ in range(min(int(photo), len(gallery))):
            photoes.append(gallery.pop(random.randint(0, len(gallery) - 1))['image']['url'])

        return [address, photoes]

    # Callback: result_error
    @__callback_func
    async def __callback_result_error(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопке result_error.

        :param:
          call (CallbackQuery): вызов.
        """
        await self.__main_result(call.message.chat.id)

    # ---------------------------------------------[main]---------------------------------------------<End>

    # ---------------------------------------------[/history]---------------------------------------------<Begin>

    @__command_func
    async def __get_history(self, message: Message) -> None:
        """
        Метод, отвечающий основной команде history бота.

        :param:
          message (Message): сообщение.
        """
        if self.__history.get(message.chat.id) == None:
            await self.__bot.send_message(message.chat.id, 'История пуста.')
            return

        history_keyboard = types.InlineKeyboardMarkup()

        # Button: h_photo_yes
        history_keyboard.row(types.InlineKeyboardButton(text='Да.', callback_data='h_photo_yes'))
        # Button: h_photo_no
        history_keyboard.row(types.InlineKeyboardButton(text='Нет.', callback_data='h_photo_no'))

        await self.__bot.send_message(message.chat.id, 'С фотографиями?', reply_markup=history_keyboard)

    # Callback: h_photo_yes, h_photo_no
    @__callback_func
    async def __callback_h_photo(self, call: CallbackQuery) -> None:
        """
        Метод, отвечающий кнопкам h_photo_yes, h_photo_no.

        :param:
          call (CallbackQuery): вызов.
        """
        await self.__history_result(call.message.chat.id, call.data == 'h_photo_yes')

    async def __history_result(self, chat_id, photo):
        try:
            for result in self.__history[chat_id]:
                await self.__bot.send_message(chat_id,
                                              f"Команда: {result['command']}\nВремя ввода команды: {result['time']}\nОтели:")
                for hotel in result['hotels']:
                    await self.__bot.send_message(chat_id,
                                                  f"Название: {hotel['name']}\nЦена: {hotel['price']}\nДистанция от центра (км): {hotel['dist']}\nАдрес: {hotel['address']}")

                    if photo and len(hotel['photoes']):
                        await self.__bot.send_media_group(chat_id,
                                                          list(map(telebot.types.InputMediaPhoto, hotel['photoes'])))
        except:
            await self.__bot.send_message(chat_id, '\U00002620 Ошибка.\U00002620 \n')

    # ---------------------------------------------[/history]---------------------------------------------<End>

    def start(self):
        """
        Функция запускающая бота.
        """
        asyncio.run(self.__bot.polling(none_stop=True))