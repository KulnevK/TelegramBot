from PIL import Image, ImageDraw, ImageFont
import math

# Создаем изображение 512x512 (стандарт для Telegram)
size = 512
img = Image.new('RGB', (size, size), color='white')
draw = ImageDraw.Draw(img)

# Градиент от синего к фиолетовому
for y in range(size):
    # Интерполяция цвета
    ratio = y / size
    r = int(66 + (138 - 66) * ratio)    # От #4285F4 к #8A2BE2
    g = int(133 + (43 - 133) * ratio)
    b = int(244 + (226 - 244) * ratio)
    draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b))

# Рисуем большую стрелку вниз (download icon)
arrow_center_x = size // 2
arrow_center_y = size // 2 - 30
arrow_width = 80
arrow_height = 100
arrow_head_size = 60

# Стрелка - прямоугольник (стержень)
draw.rectangle([
    (arrow_center_x - arrow_width//4, arrow_center_y - arrow_height//2),
    (arrow_center_x + arrow_width//4, arrow_center_y + arrow_height//4)
], fill='white')

# Треугольник (наконечник стрелки)
arrow_tip = [
    (arrow_center_x, arrow_center_y + arrow_height//2 + arrow_head_size//2),  # Нижняя точка
    (arrow_center_x - arrow_head_size, arrow_center_y + arrow_height//4),      # Левая точка
    (arrow_center_x + arrow_head_size, arrow_center_y + arrow_height//4)       # Правая точка
]
draw.polygon(arrow_tip, fill='white')

# Рисуем круглые иконки соцсетей внизу (упрощенные)
icon_y = size - 100
icon_radius = 25
icon_spacing = 70
start_x = size // 2 - icon_spacing * 1.5

# 4 кружка для соцсетей
for i in range(4):
    x = int(start_x + i * icon_spacing)
    # Белый круг
    draw.ellipse([
        (x - icon_radius, icon_y - icon_radius),
        (x + icon_radius, icon_y + icon_radius)
    ], fill='white', outline='white')

    # Маленькая иконка внутри (просто буква для простоты)
    letters = ['Y', 'T', 'I', 'X']  # YouTube, TikTok, Instagram, X(Twitter)

    # Рисуем букву (упрощенно, без шрифта)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    text = letters[i]
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(
        (x - text_width//2, icon_y - text_height//2 - 2),
        text,
        fill=(66, 133, 244),
        font=font
    )

# Сохраняем
img.save('bot_avatar.png')
print("Аватарка создана: bot_avatar.png")
