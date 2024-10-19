from PIL import Image, ImageDraw
from weather_display.assest.font.cubic_font import font48

house = Image.new('1', (96, 96), 255)
house_draw = ImageDraw.Draw(house)


house_tip = (50, 10)
left_wall = (20, 40)
left_ground = (20, 80)
right_wall = (80, 40)
right_ground = (80, 80)


house_draw.polygon(
    ([house_tip, left_wall, left_ground, right_ground, right_wall, house_tip]),
    255,
    0,
    12,
)
# house_draw.line(((65, 15), (65, 27)), 0, 2)
# house_draw.line(((65, 15), (71, 15)), 0, 2)
# house_draw.line(((71, 15), (71, 31)), 0, 2)

house_draw.text((30, 40), f'{29.6}', font=font48, fill=0)
# house_draw.text((30, 60), f'{60.9}', font=font18, fill=0)

house.show()
