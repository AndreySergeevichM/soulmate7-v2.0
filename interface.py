# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools

import data_base_my
# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0
        self.checkkeys = {"city": "Город", "sex": "Свой пол", "year": "Год своего рождения", "relation": "Семейное положение"}
        self.emptykeys = []

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

# обработка событий / получение сообщений

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет друг, {self.params["name"]}')
                    self.checkuserfilldata(event)
                elif event.text.lower() == 'поиск':
                    if(self.checkuserfilldata(event,False)):
                        '''Логика для поиска анкет'''
                        self.message_send(
                            event.user_id, 'Начинаем поиск')
                        worksheet, photo_string =  self.finduser(event)

                        if(worksheet == None):
                            self.message_send(
                                event.user_id,
                                "Никого не нашли",
                                attachment=photo_string)
                        else:
                            self.message_send(
                                event.user_id,
                                f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                                attachment=photo_string)
                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч')
                elif event.text.lower() != '' and self.emptykeys:
                    self.fillemptykey(event,event.text)
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')

    def finduser(self,event):
        while True:
            if not self.worksheets:
                self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                self.offset += 10

            if not self.worksheets:
                return None, None

            worksheet = self.worksheets.pop()

            #если пользователь уже в бд, значит уже выдавали идем дальше
            if(data_base_my.check_user(event.user_id, worksheet['id'])): continue

            photos = self.vk_tools.get_photos(worksheet['id'])
            photo_string = ''
            for photo in photos:
                photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

            #сохраняем в бд
            data_base_my.add_user(event.user_id, worksheet['id'])
            return worksheet, photo_string

    def checkuserfilldata(self, event, sendsuccesmessage = True):
        for key, value in self.checkkeys.items():
            if (self.params[key] == None or self.params[key] == 0 or self.params[key]=="") and (key not in self.emptykeys) :
                self.emptykeys.append(key)

        if self.emptykeys:
            self.message_send(event.user_id, f'Есть не заполненные поля. Введите {self.checkkeys[self.emptykeys[0]]}')
            return False
        else:
            if sendsuccesmessage:
                self.message_send(event.user_id, f'Все поля заполнены, можно проводить поиск')
            return True


    def fillemptykey(self, event, text):
        self.params[self.emptykeys[0]]=text
        del self.emptykeys[0]
        self.checkuserfilldata(event)


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()



