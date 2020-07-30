update_delay = 1.0 # seconds
single_connection_update_delay = 1.0 # seconds
update_min_signal = 20 # from 0 to 100
update_max_signal = 40 # from 0 to 100

wait_configure_before_ignore_timeout = 30.0
ignore_waiting_time_exceeded_timeout = 30.0

ignore_wrong_auth_timeout = 60.0*3

service_working_flag_check_update = 1.0

# Был использован tuple вместо класса, так как tuple можно хэшировать и поместить в set
# Также эта функция используется для получение нужных методов у библиотеки без документации :D
# Я серьёзно, спасли dir() и гугление спецификаций 802-11 в linux сервисе NetworkManager
# Этот tuple можно, но не рекомендуется расширять, но нельзя менять первые 4 наименования.
# Для расширения придётся изменить вре итераторы по этому tuple-у
WIFI_SCAN_KEYS = ('Ssid', 'HwAddress', 'Frequency', 'Strength')
