# **Исследование безопасных способов беспроводной передачи данных через Wi-Fi по протоколам ROS с автоматической реконфигурацией сети**



# **ОГЛАВЛЕНИЕ**

[**1 Обзор существующих технологий**](#1-обзор-существующих-технологий)

- [1.1 Обзор WPA2-Enterprise](#11--обзор-wpa2-enterprise)
- [1.2 OpenWRT](#12--openwrt)

[**2 Исследование возможностей демонов в Linux**](#2--исследование-возможностей-демонов-в-linux)

[**3 Исследование способов синхронизации топиков в ROS**](#3--исследование-способов-синхронизации-топиков-в-ros)

- [3.1 Решения на сокетах](#31--решения-на-сокетах)

- [3.2 Пакет multimaster_fkie для ROS](#32--пакет-multimaster_fkie-для-ros)

[**4 Разработанная программа**](#4--разработанная-программа)

- [4.1 Описание](#41--описание)
- [4.2 Решатели](#42--решатели)
- - [4.2.1 Stairs](#421--stairs)

[**5 Процесс установки и настройки**](#5--процесс-установки-и-настройки)

- [5.1 Установка ubuntu 16.04 на raspberry pi 4](#51--установка-ubuntu-1604-на-raspberry-pi-4)

- [5.2 Установка NetworkManager и pynmcli](#52--установка-networkmanager-и-pynmcli)

- [5.3 Установка пакета проекта качестве фонового демона](#53--установка-пакета-проекта-качестве-фонового-демона)

- - [5.3.1 Установка](#531--установка)
  
- - [5.3.2 Настройки](#532--настройки)

[**6 Поиск Wi-Fi роутера для увеличения дальности и уровня безопасности связи**](#6--поиск-wi-fi-роутера-для-увеличения-дальности-и-уровня-безопасности-связи)

[**7 Поиск антенн для роутера и анализ способов их размещения в роутере Xiaomi Mi WiFi Router pro (r3p)**](#7--поиск-антенн-для-роутера-и-анализ-способов-их-размещения-в-роутере-xiaomi-mi-wifi-router-pro-r3p)

[**8 Тесты**](#8--тесты)

- [8.1 Анализ скорости соединения через Wi-Fi сеть](#81--анализ-скорости-соединения-через-wi-fi-сеть)

- [8.2 Анализ возможности доступа к ROS через внешний IP адрес](#82--анализ-возможности-доступа-к-ros-через-внешний-ip-адрес)

- - [8.2.1 Установка и настройка сервиса VPN Hamachi на raspberry pi 4](#821--установка-и-настройка-сервиса-vpn-hamachi-на-raspberry-pi-4)
  
- - [8.2.2 Тест скорости при подключении системы через открытый VPN сервис Hamachi](#822--тест-скорости-при-подключении-системы-через-открытый-vpn-сервис-hamachi)

[**9 Результат**](#9--результат)



# 1 Обзор существующих технологий

​	Для решения этой непростой задачи было решено обратится к эксперту в области информационной безопасности, который рассказал нам о самых популярных и безопасных Wi-Fi протоколах. 

​	Wi-Fi-Direct - хранит огромное множество уязвимостей в безопасности. Простейшая доступная атака - замена MAC адреса и перехват подключения устройства из-за более высокого уровня сигнала.
​	Mesh-сети - более безопасны, но не удобны в использовании из-за бесшовности, т.е. когда сигнал от одной точки доступа становится слабым, то адаптер не переключается на другую. При желании и в mesh-сетях можно найти уязвимость.

​	WPA2-Enterprise - протокол с динамическим шифрованием, постоянно меняющий ключи для каждого нового подключения. Способы проникновения в сеть найти очень сложно. Самый безопасный на сегодняшний день.

## **1.1**  **Обзор WPA2-Enterprise**

​	Корпоративные сети с шифрованием WPA2-Enterprise строятся на аутентификации по протоколу 802.1x через RADIUS-сервер. Протокол 802.1x (EAPOL) определяет методы отправки и приема запроса данных аутентификации и обычно встроен в операционные системы и специальные программные пакеты.

​	Есть несколько режимов работы 802.1x, но самый распространенный и надежный следующий:

1. Аутентификатор передает EAP-запрос на клиентское устройство, как только обнаруживает активное соединение.

2. Клиент отправляет EAP-ответ - пакет идентификации. Аутентификатор пересылает этот пакет на сервер аутентификации (RADIUS).

3. RADIUS проверяет пакет и право доступа клиентского устройства по базе данных пользователя или другим признакам и затем отправляет на аутентификатор разрешение или запрет на подключение. Соответственно, аутентификатор разрешает или запрещает доступ в сеть.

![img](https://lh3.googleusercontent.com/ftcuSMOe1HRznZ0s_-a-tj1SIW3KypCn3cC_w30NId36VyQWgNefHDiW4csMzjWN1kiuOHBgt6Q8CWt19jN6bpLMlJ1zJj51xNXtAr0R_8kcZEupFbgIF-WWwiinmnK8yvcd0P8n)

*Рисунок 1 - Внутренние протоколы (методы) EAP*

​	Доступные в WPA2-Enterprise варианты шифрования таковы:

- None - отсутствие шифрования, данные передаются в открытом виде

- WEP - основанный на алгоритме RC4 шифр с разной длиной статического или динамического ключа (64 или 128 бит)

- CKIP - проприетарная замена WEP от Cisco, ранний вариант TKIP

- TKIP - улучшенная замена WEP с дополнительными проверками и защитой

- AES/CCMP - наиболее совершенный алгоритм, основанный на AES256 с дополнительными проверками и защитой




​	Доступные в WPA2-Enterprise способы проверки подлинности подключаемого устройства внешним сервером:

- EAP-FAST (Flexible Authentication via Secure Tunneling) - разработан фирмой Cisco; позволяет проводить авторизацию по логину-паролю, передаваемому внутри TLS туннеля между суппликантом и RADIUS-сервером

- EAP-TLS (Transport Layer Security). Использует инфраструктуру открытых ключей (PKI) для авторизации клиента и сервера (суппликанта и RADIUS-сервера) через сертификаты, выписанные доверенным удостоверяющим центром (CA). Требует выписывания и установки клиентских сертификатов на каждое беспроводное устройство, поэтому подходит только для управляемой корпоративной среды. Сервер сертификатов Windows имеет средства, позволяющие клиенту самостоятельно генерировать себе сертификат, если клиент - член домена. Блокирование клиента легко производится отзывом его сертификата (либо через учетные записи).

- EAP-TTLS (Tunneled Transport Layer Security) аналогичен EAP-TLS, но при создании туннеля не требуется клиентский сертификат. В таком туннеле, аналогичном SSL-соединению браузера, производится дополнительная авторизация (по паролю или как-то ещё).

- PEAP-MSCHAPv2 (Protected EAP) - схож с EAP-TTLS в плане изначального установления шифрованного TLS туннеля между клиентом и сервером, требующего серверного сертификата. В дальнейшем в таком туннеле происходит авторизация по известному протоколу MSCHAPv2

- PEAP-GTC (Generic Token Card) - аналогично предыдущему, но требует карт одноразовых паролей (и соответствующей инфраструктуры)


## **1.2**  **OpenWRT**

​	OpenWRT (https://openwrt.org/) - операционная система с ядром Linux, предназначенная для встраиваемых систем. Имеет собственный менеджер пакетов. Рассматривается как альтернатива стандартной прошивке роутера. OpenWrt расширяет возможности роутера в плане безопасности, отказоустойчивости и функциональности. Позволяет самостоятельно развернуть RADIUS сервер на роутере, а также установить или написать дополнительные полезные сервисы для него.



# **2**  **Исследование возможностей демонов в Linux**

​	Что такое демон? Это программа, запускаемая на фоне и не взаимодействующая с пользователем напрямую (из стандартных IO потоков остается лишь System.err, информацию из которого мы перенаправляем в .log файл).

​	Написание демона не сильно сложнее написания обычной программы, за исключением некоторых дополнительных шагов по настройке.

​	Что касается отказоустойчивости, моментальный перезапуск приложения при правильной настройке при убийстве процесса гарантирован.



# **3**  **Исследование способов синхронизации топиков в ROS**

## **3.1**  **Решения на сокетах**

​	Сокет - название программного интерфейса для обеспечения обмена данными между процессами. Процессы при таком обмене могут исполняться как на одной ЭВМ, так и на различных ЭВМ, связанных между собой сетью. 	Сокет - абстрактный объект, представляющий конечную точку соединения.

​	Преимущество использования сокетов - незначительный прирост в быстродействии.
​	Недостатки - сложности совместимости, плохая отказоустойчивость конечной системы, отсутствие гибкости выполняемых функций канала данных. 

## **3.2**  **Пакет multimaster_fkie для ROS**

​	multimaster_fkie - метапакет ROS для объединения узлов, необходимых для создания и управления сетью с несколькими roscore. 
​	Преимущества - прост в настройке и в развертывании на новой машине. Изменения в сети автоматически обнаруживаются и топики синхронизируются. 

​	Недостатки - скорость немного ниже, чем у сокетов, а также топики следует называть с учётом того, что они будут синхронизированы с тем же именем на других устройствах, либо стоит настроить выборочный проброс топиков, что возможно в multimaster_fkie.



# **4**  **Разработанная программа**

## **4.1**  **Описание**

​	В качестве языка был выбран удобный в разработке Python. Само приложение написано мультипоточным - для каждого адаптера существует свой асинхронный обработчик, набор общих функций, а также переменная состояния подключения, при этом система ведет учет подключенных адаптеров. Система имеет механизм обработки ошибок подключения и систему хранения ключей доступа к сетям на основе файловой системы. Алгоритм работы может выбираться пользователем из множества “решателей”

![img](https://lh6.googleusercontent.com/GJFrXuXK3LIFKu6SKkMB2K09rdpEiCIY79lcBXkPo7oltHABvRPlUCagPdVtuuwf51sRr3joft_4O5Xx0p8pHUJODPOPM6vcg14zhK6FUON-mwB8glaGKtkY7FkSIXeqgqVG4ba0)

*Рисунок 2 - UML диаграмма классов и сервисов написанной системы*

​	Исходный код системы

​	https://github.com/ITMO-lab/wifi-autoconnector 

## **4.2**  **Решатели**

### 4.2.1  Stairs

​	Stairs - относительно простой простой “жадный” решатель с мертвой зоной сигнала при переподключении к новой сети.

![img](https://lh5.googleusercontent.com/uRqOaQ3U6JTXy2_FWEIufj6dXX-lcathcCW8GdHIVdqjXTn-UJOLFvig8nzKYIVPooqRwA_3etGC8iNyjFU80qMZyuJxugc9DP3q0sGhwt3QZV01eOd10649y9fzhA2Me9fcR37S)

*Рисунок 3 - Схема к решателю Stairs*

​	На данном изображении описано, как работает переподключение к альтернативным сетям при низком уровне сигнала.

​	Сам алгоритм поиска оптимальной конфигурации сетей сначала сортирует список адаптеров по убыванию “относительной силы приёма” самого адаптера. Находится как сумма разностей квадратов уровня сигнала всех доступных сетей для данного адаптера от квадратов уровня сигнала точно таких же сетей, видимых другими адаптерами. При том сети, которые мы не видим конкретным адаптером, имеют в нашей матрице уровень сигнала None, и это корректно обрабатывается.



*Таблица 1 - матрица сигналов сетей для каждого адаптера, строки которой отсортированы по убыванию “относительной силы приёма”*

| Adapter \ BSSID | 14:CC:20:D0:F0:20 | 02:ED:2B:5D:B6:1D | 50:FF:20:14:08:95 |
| --------------- | ----------------- | ----------------- | ----------------- |
| wlan0           | 100               | 95                | 92                |
| wlx2967ga30     | 95                | 97                | None              |
| wlx1992aa       | 87                | None              | 78                |

​	Далее мы идём по отсортированному таким образом списку адаптеров и если параметр `stability` выставлен на True, мы максимизируем стабильность соединений. То есть идем по списку в обратном порядке, выставляя сначала значения для самых “слабых” адаптеров как самое мощное из еще не использованных.



*Таблица 2 - матрица сигналов сетей для каждого адаптера, иллюстрирующая оптимальный в плане стабильности соединения выбор конфигурации сети*

| Adapter \ BSSID | 14:CC:20:D0:F0:20 | 02:ED:2B:5D:B6:1D | 50:FF:20:14:08:95 |
| --------------- | ----------------- | ----------------- | ----------------- |
| wlan0           | 100               | 90                | **`80`**          |
| wlx2967ga30     | 95                | **`85`**          | 80                |
| wlx1992aa       | **`90`**          | 80                | 70                |



​	Для параметра `stability = False` конфигурация сети будет выглядеть следующем образом. 



*Таблица 3 - матрица сигналов сетей для каждого адаптера, иллюстрирующая оптимальный в плане стабильности самого сильного соединения выбор конфигурации сети*

| Adapter \ BSSID | 14:CC:20:D0:F0:20 | 02:ED:2B:5D:B6:1D | 50:FF:20:14:08:95 |
| --------------- | ----------------- | ----------------- | ----------------- |
| wlan0           | **`100`**         | 90                | 80                |
| wlx2967ga30     | 95                | **`85`**          | 80                |
| wlx1992aa       | 90                | 80                | **`70`**          |



# **5**  **Процесс установки и настройки**

## **5.1**  **Установка ubuntu 16.04 на raspberry pi 4**

​	Ссылка для скачивания рабочего образа операционной системы:
[ubiquity-xenial-lxde-raspberry-pi.img.xz](https://ubiquity-pi-image.sfo2.cdn.digitaloceanspaces.com/2020-02-10-ubiquity-xenial-lxde-raspberry-pi.img.xz)
​	Также можно поискать более актуальную версию на сайте:
https://downloads.ubiquityrobotics.com/pi.html 
​	Для загрузки операционной системой системы на SD-карту рекомендую использовать бесплатное приложение etcher:
https://www.balena.io/etcher/ 
​	Когда Raspberry Pi загружается в первый раз, он изменяет размер файловой системы, чтобы заполнить SD-карту, поэтому первая загрузка может занять некоторое время.

​	При старте системы должна появиться точка доступа Wi-Fi. SSID - это **ubiquityrobotXXXX**, где XXXX является частью MAC-адреса. Пароль от Wi-Fi - **robotseverywhere**.

​	После подключения можно войти в **Raspberry Pi 4** с помощью ssh ubuntu@10.42.0.1 c паролем **ubuntu**. Если вы подключаете клавиатуру и мышь, введите пароль **ubuntu** в командной строке.

​	По умолчанию данный дистрибутив поставляется с несколькими предустановленными пакетами и сервисами. Для их отключения введите:

`sudo systemctl disable magni-base`

​	И если вы хотите убрать автозапуск **roscore**:

`sudo systemctl disable roscore`

​	Дальнейшая конфигурация системы зависит от ваших персональных потребностей. Больше информации о дистрибутиве можно найти на сайте:
https://learn.ubiquityrobotics.com/ 

## **5.2**  **Установка NetworkManager и pynmcli**

​	Пакет pynmcli не имеет зависимостей и работает с python 2.7+
pynmcli напрямую использует Network-Manager. Для установки введите в консоль следующие команды:

`sudo apt update -y sudo apt upgrade -y `

`sudo apt install network-manager -y`

​	Установить пакет можно двумя путями. Первый - через pip. Используйте `pip3 install` вместо `pip install`, если хотите работать с версией python 3+

`pip install pynmcli`

​	Также пакет можно собрать из исходников:

`git clone https://github.com/fbarresi/PyNmcli.git`

`cd PyNmcli python setup.py install`

## **5.3**  **Установка пакета проекта качестве фонового демона**

### 5.3.1  Установка

`cd /etc/systemd/system`

`sudo git clone https://github.com/ITMO-lab/wifi-autoconnector.git`

`sudo cp wifi-autoconnector/wifi-autoconnector.service .`

`sudo systemctl daemon-reload`

`sudo systemctl stop wifi-autoconnector.service`

`sudo systemctl disable wifi-autoconnector.service`

`sudo systemctl enable wifi-autoconnector.service`

`sudo systemctl start wifi-autoconnector.service`

`sudo systemctl status wifi-autoconnector.service`

​	Сервис периодически ест ресурсы процессора, поэтому его можно выключать, когда он не нужен, командой:

`cd /etc/systemd/system`

`sudo systemctl stop wifi-autoconnector.service`

​	Или обратно включать командой:

`cd /etc/systemd/system`

`sudo systemctl start wifi-autoconnector.service`

​	Далее вам необходимо настроить файл **wifi-autoconnector/secret.json** для подключения к вашим точкам доступа. Формат записи следующий (в целях безопасности рекомендуется использовать BSSID сети, а саму сеть сделать скрытой. Следует помнить, что вы можете оставить любое поле, кроме BSSID/SSID пустым. Это нужно для подключения к открытым сетям Wi-Fi, не требующим авторизации, или к WPA/WPA2-PSK, где не требуется логин клиента сети, а требуется лишь общий ключ безопасности):

`{`

`. . .`

​	`"{BSSID} or {SSID}": {`	

​		`"password": "{your password}",`		

​		`"login": "{your WPA2-Enterprise login}"`

​	`},`

`. . .`

`}`

​	Для того, чтобы включить проброс топиков в ROS, надо выполнить в качестве трёх отдельных процессов (roscore уже запущен в фоне, если вы используете наш дистрибутив):

`roscore  rosrun fkie_master_discovery zeroconf`

`rosrun fkie_master_sync master_sync`

​	Для проброса конкретных топиков и кастомизации настроек рекомендую ознакомиться с короткой официальной документацией:
http://wiki.ros.org/master_discovery_fkie 

### 5.3.2  Настройки

​	Класс Connection в wifi-autoconnector/connection.py имеет поле:

`self.delay = 10 # seconds`

​	Это задержка на обработку события от одного адаптера. Главный скрипт в wifi-autoconnector/connection_handler.py имеет схожее поле, только в этот раз это задержка на обработку всех событий роутера:

`update_delay = 10 # seconds`

​	Под этой переменной заданы границы для “решателя” Stairs:

`update_min_signal = 20 # from 0 to 100`

`update_max_signal = 40 # from 0 to 100`

​	Также вы можете настроить поведение системы в случае возникновения ошибки подключения к роутеру. По умолчанию выставляется таймаут на данный BSSID в секундах:

`ignore_wrong_bssid_timeout = 0.0`

`ignore_wrong_auth_timeout = 30.0`

`ignore_unexpected_error_timeout = 60.0`

​	Далее выбирается “стабильный” режим работы “решателя” Stairs:

`matcher = Stairs(stability=True)`



# **6**  **Поиск Wi-Fi роутера для увеличения дальности и уровня безопасности связи**

​	Wi-Fi роутер - это беспроводная базовая станция, предназначенная для обеспечения беспроводного доступа к уже существующей сети (беспроводной или проводной) или создания новой беспроводной сети.

​	Требования по безопасности к роутеру:

- Поддержка системы контроля пользователей RADIUS (возможность работы с ней или предустановленная система контроля версий).

- Поддержка установки OpenWRT (см пункт 1.2) с целью усиления безопасности, поддержки таких важных библиотек как OpenSSL в актуальном состоянии, а также возможности установки RADIUS сервера на роутер вручную.

- Поддержка роутером, как минимум, стандартов WPA2-Enterprise с шифрованием AES/CCMP и фреймворком аутентификации EAP-TLS, PEAP-MSCHAPv2 или PEAP-GTC.




​	Рассмотренные модели с их кратким описанием:

1. XIAOMI Mi WiFi Router [3g v.2]
   Маловероятно установится прошивка, так как на сайте точно присутствуют неточности по версии. У них написано v2, а у той 16 МБ flash, хотя в описании ситилинка написано 128. На v1 с 128 МБ flash памяти мы можем поставить ось через какие-то ЛЕСА. А вот v2 поддерживается неофициально.

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/1100030/

   https://openwrt.org/toh/xiaomi/mir3g

2. ASUS RT-AC58U

   Было несколько сообщений о нестабильности этого устройства под нагрузкой. На форуме по этому роутеру установилось мнение, что 128 МБ ОЗУ недостаточно для двух радиостанций "ath10k". Использование драйверов и микропрограмм "не-CT" ath10k может улучшить стабильность.

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/413631/

   https://openwrt.org/toh/asus/rt-ac58u

3. KEENETIC Viva

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/1106600/ 

   Необычный роутер, в магазине написано одно, не уверен, что это ZyXEL, но при поиске информации о роутере выдает только с этой припиской. При поиске прошивки было выявлено нечто странное. На сайте OpenWRT есть только ZyXEL Keenetic Viva rev B.

   https://openwrt.org/toh/hwdata/zyxel/zyxel_keenetic_viva_rev._b 

   На форуме ниже указаны некоторые странные подробности.

   https://forum.openwrt.org/t/zyxel-keenetic-viva-rev-a/3732

   Этот роутер не является надежно работающим выбором, т.к. приписка "rev B" может оказаться чем то весомым, что мы не знали. Кроме того, информация касательно памяти в магазине 128/128, а при поиске прошивки они для rev A и rev B 16/128.

4. KEENETIC Duo, ADSL 2/2+

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/1099917/ 

   Интересный аппарат, т.к. прошивка на OpenWRT для него не находится, а с припиской ZyXEL и без суффикса мы можем найти этот товар на форума 4PDA, где во вкладке прошивок нет ничего кроме некой KeeneticOS. Сама идея выбирать роутер с не широко распространенной прошивкой - это плохая идея. Поэтому за отсутствием прошивки OpenWRT этот вариант не рекомендуется.

5. Xiaomi Mi WiFi Router pro (r3p)

   У данной модели есть инструкция по установке OpenWRT на 4pda:

   https://4pda.ru/forum/index.php?showtopic=810698&st=3220#entry82315996 

   И также тут:

   https://openwrt.org/toh/xiaomi/xiaomi_r3p_pro 

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/1100035/ 

   https://openwrt.org/toh/xiaomi/xiaomi_r3p_pro 

   Для установки OpenWRT на данную модель не требуется его прошивка через SPI, которая может привести к полной потери функциональности устройства без возможности восстановления. У большинства роутеров Xiaomi такая проблема присутствует, но не у этого. 

   Так как существует возможность установки OpenWRT на данный роутер, то на него можно установить весь необходимый список протоколов, а также развернуть RADIUS сервер непосредственно на роутере, для этого у него имеется 512 MB оперативной памяти и 256 MB flash памяти, чего по предварительным оценкам хватит на 256 подключенных дрона.

6. Xiaomi Mi WiFi Router 4

   https://www.citilink.ru/catalog/computers_and_notebooks/net_equipment/routers/1100031/ 

   Описание магазина Ситилинк не сильно соответствует продаваемому товару. И так, если там версия с гигабитным ethernet, тогда придётся прошивать этот роутер через SPI, подключаясь к материнке роутера, что может привести к безвозвратной потере функциональности роутера. Но у гигабитной версии 16 МБ флеша, а на сайте заявлено 128. 128 было только у первой ревизии роутеров, у которых не было гигабитного ethernet. Так как данная ошибка в описании является критической.

   Форумы ниже описывают попытки установить прошивку OpenWRT на данный роутер.

   https://openwrt.org/toh/hwdata/xiaomi/xiaomi_miwifi_r4 

   https://openwrt.org/toh/hwdata/xiaomi/xiaomi_mi_router_4a_gbit 

   https://forum.openwrt.org/t/xiaomi-mi-router-4a-gigabit-edition-r4ag-r4a-gigabit-fully-supported-but-requires-overwriting-spi-flash-with-programmer/36685 



​	Таким образом в качестве роутера был выбран Xiaomi Mi WiFi Router pro (r3p) как роутер с гарантированной возможностью установки прошивки OpenWRT с установкой всех необходимых протоколов. 



# **7**  **Поиск антенн для роутера и анализ способов их размещения в роутере Xiaomi Mi WiFi Router pro (r3p)** 

![img](https://lh6.googleusercontent.com/Lbwb7LWrbWapkXQxks0LS-mVpk99kHSyLsQKho38jqnnR8a5UujyXfdew1OVYcNqLDbgJPiFBtFlTWhAGFKkh-l0Uny156W49L5sCLLwbrYstRM5iviN41yqRnUbNWeO0qkHTNPO)

*Рисунок 4 - Роутер Xiaomi Mi WiFi Router pro (r3p)*

​	Существует несколько способов размещения антенн у роутера. Самый распространенный из них - простое вертикальное расположение. Однако, это было бы наиболее выгодно в условиях домашнего потребления, т.к. делиться wifi с соседями не является нашей задачей. У нас же все обстоит немного иначе. Т.к. мы будем работать в воздушным пространством, то будет иметь смысл расположение либо горизонтально (Что несомненно уменьшит покрытие вширь), либо под углом 90 или 45 градусов друг к другу. В случае двух антенн, нам будет наиболее выгодно расположить каждую из них под 45 градусов относительно оси роутера, таким образом, между собой они будут образовывать прямой угол и иметь наибольшее покрытие как в воздухе, так и в горизонтальном пространстве. Что касается четырех антенн, то тут ситуация почти такая же, за исключением того, что две другие антенны надо будет располагать также перпендикулярно плоскости первых двух и под 45 градусов к плоскости роутера.

​	Если же антенны будут выведены вне роутера, то плоскость роутера в определении их расположения сменяется на плоскость земли.

​	В случае, если нам необходимо вывести антенны вне роутера, то такая возможность имеет место быть. Ниже представлена схема роутера, на которой мы можем заметить несколько белых линих, исходящих от краев. Они показывают как и куда можно провести антенны. они подключаются к каналам (Они указаны как 2G_CH3/5G_CH0, 2G_CH2/5G_CH1, 2G_CH1/5G_CH2, 2G_CH0/5G_CH3). Сама антенна подключается через разъем RP-SMA. К роутеру же нужен разъем U.FL. Таким образом, для подключения внешних антенн нам будут необходимы переходники RP-SMA - U.FL или же удлинитель RP-SMA - RP-SMA. Мы можем использовать любую антенну на рынке с разъемом RP-SMA.

​	Для обеспечения водонепроницаемости роутера можно использовать антенны с водонепроницаемым дизайном. (Например: [Eoth](https://aliexpress.ru/item/32964934150.html?aff_platform=default&sk=CS44FoqU&aff_trace_key=9d09d8b09b4944ff9aa1543768d141cf-1584109191901-08196-CS44FoqU&dp=gl.andantefilm.se&tmLog=new_Detail_6220&terminal_id=ed3b0fd829a44f7d881e28471ab05473&aff_request_id=9d09d8b09b4944ff9aa1543768d141cf-1584109191901-08196-CS44FoqU) или [Bingfu](https://wlaniot.com/collections/4g-antenna/products/bingfu-4g-lte-outdoor-fixed-bracket-wall-mount-waterproof-antenna-5dbi-sma-male-antenna-for-verizon-at-t-t-mobile-sprint-4g-lte-router-gateway-modem-mobile-cell-phone-signal-booster-cellular-amplifier-2))

​	Из последнего можно взять способ крепления к корпусу станции.

![img](https://lh6.googleusercontent.com/D316jGxv85VbjaH9LEFNlMJgHp3pX7Gee6Jes8IkI5BkPzMQV_EGGFnlihNmCOjEl9LCKuHznfP0mq-n5FfLu-5a-xoUHhZfvv2SJjfT9UgNicWXF9VF6jn6u8Yuq7T139q-uRk7)

*Рисунок 5 - Схема роутера без антенн*

![img](https://lh3.googleusercontent.com/g3uteuSI7mL_k64nNyzM4i0lbs2W4rRF8ekc8mioXt4qOkCfkxZ65pp_ap_8qZhTNzteFyY8lXK2RHaS9z3eaAC56xQL1oXi67geRrYX_NzDXTA8Y5ti8OjqMlvaH6tEr4aW9ENM)

*Рисунок 6 - Схема с подключенными антеннами*



# **8**  **Тесты** 

## **8.1**  **Анализ скорости соединения через Wi-Fi сеть**

​	При подключении по Wi-Fi через разработанную систему мы имеем скорость почти в 12 мегабайт в секунду, что близко к 100 мегабитам в секунду, а это максимальная скорость, раздаваемая нашим роутером.

![img](https://lh3.googleusercontent.com/0L4GEvdfM58RJSPuFpCTH-7oFW7TAytbh8eDpKoovhSGqR-q0VMinCCPDcOL_MEP1kC_5L42yT-UOc1Rdv3-z4R-QNSOm-pL1WD0CPmHAapLGifEsXq_0Hej-LtmbvgxOXkJc7rO)

*Рисунок 7 - Скорость соединения напрямую через Wi-Fi*

## **8.2**  **Анализ возможности доступа к ROS через внешний IP адрес**

### **8.2.1**  **Установка и настройка сервиса VPN Hamachi на raspberry pi 4**

​	Для установки hamachi необходимо зайти на оффициальный сайт https://vpn.net/linux и скачать актуальную версию для архитектуры ARMHF, подходящую системе в расширении “deb”. Важно, чтобы версия оказалась на raspberry pi 4. Далее в директории с файлом logmein-hamachi_{ВЕРСИЯ}_armhf.deb нужно открыть терминал и ввести следующие команды:

`sudo dpkg -i logmein-hamachi_*_armhf.deb` 

`sudo /etc/init.d/logmein-hamachi start` 

`sudo systemctl daemon-reload`

`sudo systemctl enable logmein-hamachi.service` 

`sudo systemctl start logmein-hamachi.service`

​	После чего требуется создать аккаунт hamachi на их официальном сайте, создать собственную VPN сеть в hamachi, обращаем внимание на адрес электронной почты, на который регистрировался аккаунт (на него придет подтверждение, его надо подтвердить), также на номер созданной вами VPN сети. Далее нужно снова открыть терминал и ввести следующие команды (Команда “do-join” может привести к запросу пароля, если вы его задали для вашей сети. Вам будет необходимо его ввести):

`sudo hamachi logon`

`sudo hamachi attach <Email адрес аккаунта>` 

`sudo hamachi do-join <network ID>` 

`sudo hamachi list`

​	Последняя команда выведет список активных и неактивных пользователей данной сети, чтобы можно было убедиться в работоспособности сервиса.

### **8.2.2**  **Тест скорости при подключении системы через открытый VPN сервис Hamachi**

​	При подключении через VPN сервис hamachi и при использовании в качестве основной сети независимое от сети raspberry pi мобильное 4G соединение была достигнута скорость передачи информации 5 мегабайт в секунду, чего хватило на передачу видеопотока в 640x480 с частотой в 30 fps с минимальными визуальными задержками.

![img](https://lh5.googleusercontent.com/6rjtFXuLNlzC25EqzbaddpYzgkstShOJjkD6PZV70CY2QBMFzouzhP14-RsPT0ftkhtrQuUWh2qHN0j3wpnO01xqqvbcbDcarBWQoULDZyNTx7eJCNVwNRB0Duqy0sF9yDDlUEGB)

*Рисунок 8 - Скорость соединения через IP адрес, предоставленный VPN*



# **9**  **Результат**

​	Система выполняет автоматическую реконфигурацию подключений, используя профили, хранимые в secret.json

​	Присутствует полная поддержка сетей WPA2-Enterprise.

​	При отключении от точки (или точек) доступа, выполняется автоматическое переподключение к наиболее оптимальным (в смысле стабильности или в смысле скорости. см. “Решатели”) сетям. При низком уровне сигнала ищется более оптимальная сеть и выполняется переподключение в случае нахождения такой сети.

​	Внутри сети автоматически конфигурируется ROS multimaster, позволяющий организовать высокоскоростную передачу информации между устройствами с запущенным roscore посредством стандартных средств - топиков ROS.

​	Вся система работает на уровне фоновых сервисов в Linux и равномерно использует процессор, благодаря оптимизации мультипоточных запросов.