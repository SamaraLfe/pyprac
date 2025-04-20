import gettext

# Домены переводов
DOMAINS = {
    '1': 'messages',
    '2': 'messages_alt'
}


def set_locale(lang, domain):
    t = gettext.translation(domain, localedir='locales', languages=[lang], fallback=True)
    t.install()
    return t.gettext, t.ngettext


def count_words(lang, domain):
    _, ngettext = set_locale(lang, domain)

    print(f"\n=== Текущий домен: {domain} ===")
    while True:
        text = input(_("Введите строку для подсчета слов (или 'exit' для выхода): "))
        if text.lower() == 'exit':
            break

        words = text.split()
        count = len(words)
        print(ngettext("Найдено {} слово", "Найдено {} слова", count).format(count))


while True:
    print("\nВыберите язык и домен:")
    print("1. Русский (основной домен)")
    print("2. Русский (альтернативный домен)")
    print("3. English (default domain)")
    print("4. English (alternative domain)")
    print("0. Выход")

    choice = input("Ваш выбор (1-4 или 0): ").strip()

    if choice == '0':
        break

    lang_domain = {
        '1': ('ru', 'messages'),
        '2': ('ru', 'messages_alt'),
        '3': ('en', 'messages'),
        '4': ('en', 'messages_alt')
    }.get(choice)

    if lang_domain:
        lang, domain = lang_domain
        count_words(lang, domain)
    else:
        print("Неверный ввод, попробуйте снова")