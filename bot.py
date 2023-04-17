import json
import asyncio
import requests
import io
import traceback
import threading

from PIL import Image, ImageOps
from PIL.Image import Transpose
from khl import Bot, Message, PublicTextChannel, api, MessageTypes



# setup bot and tokens
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot = Bot(token=config['token'])


# setup global variables
activated = False
type = ''
direction = ''
toBeReplied = None
mode = ''
task = None

# handle image message
# execute only when activated is True
# send to flip_image function if type is flip
async def image_handler(msg: Message):
    global activated
    global type
    global direction
    global toBeReplied
    global task
    resimg = None
    img_url = msg.content
    img = Image.open(io.BytesIO(requests.get(img_url).content))
    if activated and toBeReplied.author_id == msg.author_id:
        try:
            if type == 'flip':
                resimg = await flip_image(img)
            if type == 'merge':
                resimg = await merge_image(img)
            imgByteArr = io.BytesIO()
            resimg.save(imgByteArr, format='PNG')
            imgByte = io.BytesIO(imgByteArr.getvalue())
            res_img_url = await bot.client.create_asset(imgByte)
            await msg.reply(res_img_url, type=MessageTypes.IMG)
            img.close()
            task.cancel()
            await reset()
        except Exception as e:
            await msg.reply('error: something went wrong, please try again')
            print(str(e))
            print(traceback.format_exc())



# register image message handler
bot.client.register(MessageTypes.IMG, image_handler)


# take left half of the image, flip it, and paste it to the right half
# same logic for other directions
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


# merge the image in ./src/charac.png with the image sent by user
# resize and crop the image sent by user to make it fit the charac.png
# make charac.png transparent, and put it on top of the image sent by user
async def merge_image(img: Image):
    global mode
    charac = Image.open('./src/charac.png')
    cwidth, cheight = (880, 880)
    charac = charac.convert('RGBA')
    img = img.convert('RGBA')
    new_img = Image.new('RGB', img.size, (255, 255, 255))
    new_img.paste(img, mask=img)
    img = new_img
    width, height = img.size
    print(width)
    print(height)
    if mode == 'expand':
        if width < height:
            r = cwidth / width
            img = img.resize((int(width * r), int(height * r)), resample = Image.LANCZOS)
        elif height < width:
            r = cheight / height
            img = img.resize((int(width * r), int(height * r)), resample = Image.LANCZOS)
        elif width == height:
            img = img.resize((cwidth, cwidth), resample = Image.LANCZOS)
            width, height = img.size
            new_img = Image.new('RGB', charac.size, (255, 255, 255))
            new_img.paste(img, (145, 177))
            new_img.paste(charac, (0, 0), charac)
        width, height = img.size
        new_img = Image.new('RGB', charac.size, (255, 255, 255))
        new_img.paste(img, (145+(880-width)//2, 177))
        new_img.paste(charac, (0, 0), charac)
    elif mode == 'shrink':
        if width < height:
            r = cheight / height
            img = img.resize((int(width * r), int(height * r)), resample = Image.LANCZOS)
        elif height < width:
            r = cwidth / width
            img = img.resize((int(width * r), int(height * r)), resample = Image.LANCZOS)
        elif width == height:
            img = img.resize((cwidth, cwidth), resample = Image.LANCZOS)
            width, height = img.size
            new_img = Image.new('RGB', charac.size, (255, 255, 255))
            new_img.paste(img, (145, 177))
            new_img.paste(charac, (0, 0), charac)
        width, height = img.size
        new_img = Image.new('RGB', charac.size, (255, 255, 255))
        new_img.paste(img, (145 + (880-width)//2, 177))
        new_img.paste(charac, (0, 0), charac)
    mode = ''
    return new_img


# start timer
async def start_timer():
    global task
    print('[info] task initiated')
    task = asyncio.create_task(async_timer())


# start a timer that will do something in 30 seconds
# if the timer is not cancelled, the activated will be set to False
async def async_timer():
    global activated
    print('timer started')
    await asyncio.sleep(30)
    if activated:
        await toBeReplied.reply('error: time out, please try again')
        await reset()


# reset all the global variables
async def reset():
    global activated
    global type
    global direction
    global toBeReplied
    global mode
    global task
    print('[info] global variables reset')
    activated = False
    type = ''
    direction = ''
    toBeReplied = None
    mode = ''
    task = None


# on command cancel, cancel timer
@bot.command('cancel')
async def cancel(msg: Message):
    global activated
    global task
    if activated:
        task.cancel()
        await msg.reply('cancelled')
        await reset()
        print('[info] task cancelled')


# async def timer():
#     global task
#     timer = threading.Timer(10000, )
#     timer.start()
#     print('timer started')
#     task = timer

# async def timer_actions():
#     global activated
#     global type
#     global direction
#     global toBeReplied
#     global mode
#     global task
#     print("timer ended")
#     await toBeReplied.reply('error: time out, please try again')
#     activated = False
#     type = ''
#     direction = ''
#     toBeReplied = None
#     mode = ''
#     task = None


# on command flip, activated is set to True, and type is set to flip, send prompt message to user to send image
@bot.command('flip')
async def flip(msg: Message, d: str = ''):
    global activated
    global type
    global direction
    global toBeReplied
    if activated:
        await msg.reply('error: another person is using a command or a command is processing, please wait. \nthis won\'t take more than 30 seconds')
        return
    if d not in ('left', 'right', 'up', 'down'):
        await msg.reply('please specify the direction to flip')
        return
    print('[info] flip command activated')
    direction = d
    activated = True
    type = 'flip'
    toBeReplied = msg
    await msg.reply('send me an image to flip')
    await start_timer()


# on command merge, activated is set to True, and type is set to merge, send prompt message to user to send image
# parameters include the type of merge, which will be numbers from 1 to 4
# we don't need the direction global variable, direction is only used to specify the direction to flip
@bot.command('merge')
async def merge(msg: Message, t: str = '', m: str = ''):
    global activated
    global type
    global toBeReplied
    global mode
    if activated:
        await msg.reply('error: another person is using a command or a command is processing, please wait. \nThis won\'t take more than 30 seconds')
        return
    if t not in ('1', '2', '3', '4'):
        await msg.reply('please specify the type of merge, use /mergelist to see the list of merge types')
        return
    activated = True
    type = 'merge'
    toBeReplied = msg
    if mode == 'shrink' or mode == 'expand':
        mode = m
    else:
        mode = 'expand'
    await msg.reply('send me an image to merge')
    await start_timer()


# on command mergelist, send a list of merge types
# merge types are to be determined, create the command first, the description will be filled later
@bot.command('mergelist')
async def mergelist(msg: Message):
    await msg.reply('merge types:\n1. character\n2. \n3. \n4. \nmodes: shrink, expand (default is expand)\nuse /merge [number] [mode] to merge two images')


@bot.command('ihelp')
async def ihelp(msg: Message):
    await msg.reply('flip left/right/up/down: flip image\nmerge [number]: merge two images\njoke: send a random joke\nping: pong\nihelp: show this message')


@bot.command('ping')
async def ping(msg: Message):
    await msg.reply('pong')


# on command joke, send a random joke from icanhazdadjoke.com
@bot.command('joke')
async def joke(msg: Message):
    headers = {'Accept': 'application/json'}
    r = requests.get('https://icanhazdadjoke.com/', headers=headers)
    await msg.reply(r.json()['joke'])


# bot run
bot.run()
