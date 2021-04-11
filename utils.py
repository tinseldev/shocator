import subprocess
import random
import re
import os
import time


def randomizer():
    with open('cities.txt', 'r') as f:
        citystr = random.choice(f.readlines())
        return citystr.replace('\n', '').replace(' ', '-').replace(
            '`', '').replace("'", '')


def downloader(city):
    process = subprocess.run(f'shodan download --limit -1 -- '
                             f'{city.lower()}-data.json.gz '
                             f'screenshot.label:webcam city:{city.lower()} '
                             f'-port:5900,5901,5910,3389,3388',
                             shell=True, capture_output=True, text=True).stdout
    try:
        res_count = re.split('Saved', process)[1]
        c = []
        for _ in res_count:
            if _.isdigit():
                c.append(_)
        res_count = [str(integer) for integer in c]
        a_string = "".join(res_count)
        res_count = int(a_string)
        if res_count == 0:
            os.system('rm -f *-data.json.gz')
    except IndexError:
        res_count = 0
    return res_count


def error_parser(error):
    try:
        seconds = re.split('in', error)[1]
        c = []
        for _ in seconds:
            if _.isdigit():
                c.append(_)
        seconds = [str(integer) for integer in c]
        a_string = "".join(seconds)[:-1]
        seconds = int(a_string)
    except IndexError:
        error = 'Parser error'
    return seconds


def jpg_poster(pbar, file, bot, id, country, city, show):
    success = False
    retry = 0
    ip = os.path.splitext(os.path.basename(file))[0]
    while not success:
        try:
            pbar.write('Trying to send a post...')
            with open(os.path.join('snapshots', file), 'rb') as f:
                bot.sendPhoto(chat_id=id, photo=f, caption=f"Location: "
                              f"{country}, {city}\n{ip if show else ''}",
                              disable_notification=True, timeout=250)
            success = True
            pbar.update(1)
            pbar.write('Post sended')
            time.sleep(4)
        except Exception as error:
            if retry > 4:
                pbar.write('Failed to send a post')
                break
            else:
                retry += 1
                error = str(error)
                pbar.write('Flood control exceeded')
                seconds = error_parser(error)
                pbar.write(f'Sleeping for {seconds} seconds...')
                time.sleep(seconds)


def gif_poster(pbar, file, bot, id, country, city, show):
    success = False
    retry = 0
    ip = os.path.splitext(os.path.basename(file))[0]
    while not success:
        try:
            pbar.write('Trying to send a post...')
            with open(os.path.join('snapshots', file), 'rb') as f:
                bot.sendAnimation(chat_id=id, animation=f,
                                  caption=f"Location: "
                                  f"{country}, {city}\n{ip if show else ''}",
                                  disable_notification=True, timeout=250)
            success = True
            pbar.update(1)
            pbar.write('Post sended')
            time.sleep(4)
        except Exception as error:
            if retry > 4:
                pbar.write('Failed to send a post')
                break
            else:
                retry += 1
                error = str(error)
                pbar.write('Flood control exceeded')
                seconds = error_parser(error)
                pbar.write(f'Sleeping for {seconds} seconds...')
                time.sleep(seconds)
