��    (      \              �      �  |   �     ;     C     W     i     }     �     �     �      �     �          )     ;  
   O     Z     k     �     �  *   �     �     �     �          #     ,     8  	   D  	   N  	   X     b  	   n     x  	   �  
   �     �  
   �     �  �  �  <   x  T  �     
	  *   	     A	  (   ]	  1   �	  +   �	  <   �	  %   !
  U   G
  ,   �
  F   �
  &     %   8     ^     s  (   �  7   �  '   �  r     %   �  )   �  1   �  $     5   3  �   i  �   ?  -   �  �     /   �  �   �  �   �  �   X     �  1     �   4  N   �  /      %s added %s at (%d,%d) saying %s %s attacked %s with %s, dealing %d damage. %s was killed! %s attacked %s with %s, dealing %d damage. %s has %d HP remaining. %s died %s joined the game! %s left the game! %s moved to (%d,%d) %s now has %d hp Added monster at (%d, %d) Attacked %s, damage %d hp Available commands: %s Invalid state: use 'on' or 'off' Message "%s" sent Monster %s moved one cell %s Moved to (%d, %d) Moving monsters: %s No %s here Player not found Replaced the old monster Server uptime: %d seconds Set up locale: %s Type 'help <command>' for more information Unknown command Unknown command: %s Unsupported locale: %s Welcome, %s! help_EOF help_addmon help_attack help_down help_help help_left help_locale help_move help_movemonsters help_quit help_right help_sayall help_timer help_up Project-Id-Version: MOOD Game 1.0
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2025-05-26 01:31+0200
PO-Revision-Date: 2025-05-26 01:31+0200
Last-Translator: 
Language: ru_RU
Language-Team: Russian <ru@li.org>
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.17.0
 %s добавил %s на (%d,%d) с сообщением %s %s атаковал %s используя %s, нанеся %d урона. %s убит! %s атаковал %s используя %s, нанеся %d урона. У %s осталось %d очко здоровья. %s атаковал %s используя %s, нанеся %d урона. У %s осталось %d очка здоровья. %s умер %s присоединился к игре! %s покинул игру! %s переместился на (%d,%d) У %s теперь %d очков здоровья Добавлен монстр на (%d, %d) Атаковал %s, урон %d очков здоровья Доступные команды: %s Недопустимое состояние: используйте 'on' или 'off' Сообщение "%s" отправлено Монстр %s переместился на одну клетку %s Переместился на (%d, %d) Движение монстров: %s Здесь нет %s Игрок не найден Заменён старый монстр Время работы сервера: %d секунд Установлена локаль: %s Введите 'help <команда>' для получения дополнительной информации Неизвестная команда Неизвестная команда: %s Неподдерживаемая локаль: %s Добро пожаловать, %s! Выйти из игры (аналогично quit). Добавить монстра на игровое поле.
Формат: addmon <имя> coords <x> <y> hello <сообщение> hp <здоровье>
Пример: addmon cower coords 0 0 hello "Moo!" hp 100 Атаковать монстра указанным оружием.
Формат: attack <монстр> [with <оружие>]
Пример: attack cower with sword Переместить игрока вниз. Показать список доступных команд или помощь по конкретной команде.
Формат: help [команда]
Пример: help attack Переместить игрока влево. Установить локаль.
Формат: locale <имя_локали>
Пример: locale ru_RU
Доступные локали: en_US, ru_RU Переместить игрока в указанном направлении.
Формат: move <направление>
Направления: up, down, left, right
Пример: move right Включить или выключить движение монстров.
Формат: movemonsters <on|off>
Пример: movemonsters on Выйти из игры. Переместить игрока вправо. Отправить сообщение всем игрокам.
Формат: sayall <сообщение>
Пример: sayall "Привет, мир!" Запросить время работы сервера.
Формат: timer Переместить игрока вверх. 