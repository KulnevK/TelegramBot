from yookassa import Configuration, Payment
import uuid

# Настройки ЮKassa (заполните после регистрации)
SHOP_ID = "YOUR_SHOP_ID"  # ID магазина из личного кабинета ЮKassa
SECRET_KEY = "YOUR_SECRET_KEY"  # Секретный ключ из личного кабинета

# Цены
PREMIUM_MONTH_PRICE = 100  # 100 рублей за месяц

def init_yookassa():
    """Инициализация ЮKassa"""
    Configuration.account_id = SHOP_ID
    Configuration.secret_key = SECRET_KEY

def create_payment(user_id, amount, description):
    """Создать платеж"""
    init_yookassa()

    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/YOUR_BOT_USERNAME"  # Замените на username вашего бота
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": user_id
        }
    }, uuid.uuid4())

    return payment

def check_payment(payment_id):
    """Проверить статус платежа"""
    init_yookassa()

    payment = Payment.find_one(payment_id)
    return payment.status
