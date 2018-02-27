#### Описание

YaTank-Mail - плагин для Yandex-Tank, который предназначен для отправки соответствующих уведомлений по почте.

Для использования требуется [плагин](https://github.com/sputnik-load/yatank-report), собирающий данные для отчета
 
#### Использование

Опции в конфиге:

```
[mail]
to = <user_mail_list>
from = <user_mail_sender>

# если plugin_data опция тут не задана, будет браться из
# соответствующей plugin_data опции из tank
plugin_data=<plugin_for_data>

# опция message_template_<stage> содержит шаблон сообщения,
# которое отправляется на соответствующей стадии теста
# (имеет больший приоритет, чем message_template_file_path_*)
message_template_<stage> = 

# опция message_template_file_path_<stage> содержит путь к файлу с
# шаблоном сообщения,
# которое отправляется на соответствующей стадии теста
message_template_file_path_<stage> =
```
