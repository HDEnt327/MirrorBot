import json
import asyncio
import requests
import io

from PIL import Image
from khl import Bot, Message, PublicTextChannel, api, MessageTypes

# setup bot and tokens
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot = Bot(token=config['token'])

activated = False
type = ''
direction = ''
toBeReplied = None

# handle image message
# execute only when activated is True
# send to flip_image function if type is flip
async def image_handler(msg: Message):
    global activated
    global type
    global direction
    if activated:
        try:
            if type == 'flip':
                img_url = msg.content
                img = Image.open(io.BytesIO(requests.get(img_url).content))
                resimg = await flip_image(img)
                imgByteArr = io.BytesIO()
                resimg.save(imgByteArr, format='PNG')
                imgByte = io.BytesIO(imgByteArr.getvalue())
                img_url = await bot.client.create_asset(imgByte)
                await msg.reply(img_url, type=MessageTypes.IMG)
                activated = False
                type = ''
                direction = ''
        except:
            await msg.reply('unknown error, please try again')


# register image message handler
bot.client.register(MessageTypes.IMG, image_handler)


# take left half of the image, flip it, and paste it to the right half
async def flip_image(img):
    if direction == 'left':
        width, height = img.size
        left = img.crop((0, 0, width // 2, height))
        left = left.transpose(Image.FLIP_LEFT_RIGHT)
        new_img = img.copy()
        new_img.paste(left, (width // 2, 0))
        return new_img
    if direction == 'right':
        width, height = img.size
        right = img.crop((width // 2, 0, width, height))
        right = right.transpose(Image.FLIP_LEFT_RIGHT)
        new_img = img.copy()
        new_img.paste(right, (0, 0))
        return new_img
    if direction == 'up':
        width, height = img.size
        up = img.crop((0, 0, width, height // 2))
        up = up.transpose(Image.FLIP_TOP_BOTTOM)
        new_img = img.copy()
        new_img.paste(up, (0, height // 2))
        return new_img
    if direction == 'down':
        width, height = img.size
        down = img.crop((0, height // 2, width, height))
        down = down.transpose(Image.FLIP_TOP_BOTTOM)
        new_img = img.copy()
        new_img.paste(down, (0, 0))
        return new_img


# start a timer that will do something in 30 seconds
# if the timer is not cancelled, the activated will be set to False
async def timer():
    global activated
    global type
    global direction
    global toBeReplied
    print("timer started")
    await asyncio.sleep(30)
    if activated:
        activated = False
        type = ''
        direction = ''
        await toBeReplied.reply('error: time out, please try again')
        toBeReplied = None


# on command flip, activated is set to True, and type is set to flip, send prompt message to user to send image
@bot.command('flip')
async def flip(msg: Message, d: str = ''):
    global activated
    global type
    global direction
    global toBeReplied
    activated = True
    type = 'flip'
    toBeReplied = msg
    if d == 'left' or d == 'right' or d == 'up' or d == 'down':
        direction = d
        await msg.reply('send me an image to flip')
        await timer()
    else:
        await msg.reply('please specify the direction to flip')


@bot.command('ihelp')
async def ihelp(msg: Message):
    await msg.reply('flip left/right/up/down: flip image')




# bot run
bot.run()