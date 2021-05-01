#!/usr/bin/env python3


import arrow
import os
import shutil
import glob
import tqdm
import base64
import shodan
import shodan.helpers as helpers
import time
import utils
import telegram


# Settings
############################################################
SHODAN_API_KEY = 'KOllTMXB4soCYaVyh7IJhENkr3ZZelfd'

BOT_TOKEN = '1499789509:AAFo2WS2cam2U9IMvH8zFtWhnH4ktVh5B4Q'

ROOM_ID = '-1001146754568'

SNAPS_MIN = 7  # The minimum number of snapshots to create a time-lapse

SHOW_IP = False  # Set "True" to show the IP in the post
############################################################


bot = telegram.Bot(token=BOT_TOKEN)

while True:
    ip = ''
    country = ''
    city = ''
    res_count = 0
    print('Looking for a random city...')
    while res_count == 0:
        city = utils.randomizer()
        res_count = utils.downloader(city)
        if res_count > 0:
            print(f'{city} selected.')
            print(f'{res_count} results retrieved from JSON')

    # GIFs are stored in the local "snapshots" directory
    try:
        os.makedirs('snapshots/tmp')
    except OSError:
        pass

    # Setup the Shodan API object
    api = shodan.Shodan(SHODAN_API_KEY)
    # Show a progress indicator
    BAR_FORMAT = '{desc}{percentage:3.0f}%[{bar}] {n_fmt}/{total_fmt} '
    '[{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    pbar = tqdm.tqdm(total=res_count, ascii=True, bar_format=BAR_FORMAT)
    pbar.set_description(desc='Сollecting snapshots from the JSON')
    # Loop over all of the Shodan data files the user provided
    for banner in helpers.iterate_files(f'{city.lower()}-data.json.gz'):
        # See whether the current banner has a screenshot,
        # if it does then lets lookup more information about this IP
        has_screenshot = helpers.get_screenshot(banner)
        if has_screenshot:
            try:
                ip = helpers.get_ip(banner)
                pbar.write(f'Looking up {ip}')
                host = api.host(ip, history=True)
                country = host['country_name']
                city = host['city']

                # Store all the historical screenshots for this IP
                screenshots = []
                for tmp_banner in host['data']:
                    # Try to extract the image from the banner data
                    screenshot = helpers.get_screenshot(tmp_banner)
                    if screenshot:
                        # Sort the images by the time they were
                        # collected so the GIF will loop based on
                        # the local time regardless of which day the
                        # banner was taken.
                        timestamp = arrow.get(banner['timestamp']).time()
                        sort_key = timestamp.hour

                        # Add the screenshot to the list of screenshots
                        # which we'll use to create the timelapse
                        screenshots.append((
                            sort_key,
                            str.encode(screenshot['data'])
                        ))

                # Extract the screenshots and turn them into a GIF if
                # we've got more than a few images
                if len(screenshots) >= SNAPS_MIN:
                    # screenshots is a list where each item is a tuple of:
                    # (sort key, screenshot in base64 encoding)
                    #
                    # Lets sort that list based on the sort key and
                    # then use Python's enumerate
                    # to generate sequential numbers for
                    # the temporary image filenames
                    for (i, screenshot) in enumerate(sorted(screenshots,
                                                     key=lambda x: x[0],
                                                     reverse=True)):
                        # Create a temporary image file
                        open(f'snapshots/tmp/gif-image-{i}.jpg', 'wb').write(
                            base64.decodebytes(screenshot[1]))

                    # Create the actual GIF using the
                    # ImageMagick "convert" command
                    # The resulting GIFs are stored in the local
                    # "snapshots" directory
                    os.system(f'convert -layers OptimizePlus -delay 5x10 '
                              f'snapshots/tmp/gif-image-*.jpg '
                              f'-loop 0 +dither -colors 256 -depth 8 '
                              f'snapshots/{ip}.gif')
                    # Clean up the temporary files
                    files = glob.glob('snapshots/tmp/gif-image-*.jpg')
                    for f in files:
                        os.remove(f)
                    pbar.update(1)
                    pbar.write(f'GIF created for {ip}')
                else:
                    open(f'snapshots/{ip}.jpg', 'wb').write(
                        base64.decodebytes(screenshots[0][1]))
                    pbar.update(1)
                    pbar.write(f'JPG created for {ip}')
                    time.sleep(4)
            except Exception as e:
                pbar.update(1)
                pbar.write(repr(e))
    pbar.close()
    dir = 'snapshots'
    fcount = 0
    for path in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, path)):
            fcount += 1
    pbar = tqdm.tqdm(total=fcount, ascii=True, bar_format=BAR_FORMAT)
    pbar.set_description(desc='Sending snapnshots to the telegram channel')
    for file in os.listdir(dir):
        if file.endswith('.jpg'):
            utils.jpg_poster(pbar, file, bot, ROOM_ID, country, city, SHOW_IP)
        elif file.endswith('.gif'):
            utils.gif_poster(pbar, file, bot, ROOM_ID, country, city, SHOW_IP)
        else:
            continue
    pbar.close()
    shutil.rmtree('snapshots')
