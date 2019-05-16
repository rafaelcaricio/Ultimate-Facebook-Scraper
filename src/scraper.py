import calendar
import os
import os.path
import platform
import sys
import urllib.request
import time
import json
import math
import base64
import logging
try:
    import config as config_values
except ImportError:
    raise RuntimeError("Please create config.py based on config-sample.py")

from typing import List
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# -------------------------------------------------------------
# -------------------------------------------------------------

Image.MAX_IMAGE_PIXELS = None

# Global Variables

driver = None

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# whether to download photos or not
download_uploaded_photos = True 
download_friends_photos = True 

# whether to download the full image or its thumbnail (small size)
# if small size is True then it will be very quick else if its false then it will open each photo to download it
# and it will take much more time
friends_small_size = True 
photos_small_size = True 

total_scrolls = 5000
current_scrolls = 0
scroll_time = 5

old_height = 0

class Config:
    data_folder = 'data'


# -------------------------------------------------------------
# -------------------------------------------------------------

def get_facebook_images_url(img_links):
    urls = []

    for link in img_links:

        if link != "None":
            valid_url_found = False
            driver.get(link)

            try:
                while not valid_url_found:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "spotlight")))
                    element = driver.find_element_by_class_name("spotlight")
                    img_url = element.get_attribute('src')

                    if img_url.find('.gif') == -1:
                        valid_url_found = True
                        urls.append(img_url)

            except EC.StaleElementReferenceException:
                urls.append(driver.find_element_by_class_name("spotlight").get_attribute('src'))

            except:
                print("Exception (facebook_image_downloader):", sys.exc_info()[0])

        else:
            urls.append("None")

    return urls


# -------------------------------------------------------------
# -------------------------------------------------------------

# takes a url and downloads image from that url
def image_downloader(img_links, folder_name):
    img_names = []

    try:
        parent = os.getcwd()
        try:
            folder = os.path.join(os.getcwd(), folder_name)
            if not os.path.exists(folder):
                os.mkdir(folder)

            os.chdir(folder)
        except:
            print("Error in changing directory")

        for link in img_links:
            img_name = "None"

            if link != "None":
                img_name = (link.split('.jpg')[0]).split('/')[-1] + '.jpg'

                if img_name == "10354686_10150004552801856_220367501106153455_n.jpg":
                    img_name = "None"
                else:
                    try:
                        urllib.request.urlretrieve(link, img_name)
                    except:
                        img_name = "None"

            img_names.append(img_name)

        os.chdir(parent)
    except:
        print("Exception (image_downloader):", sys.exc_info()[0])

    return img_names


# -------------------------------------------------------------
# -------------------------------------------------------------

def check_height():
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height != old_height


# -------------------------------------------------------------
# -------------------------------------------------------------

# helper function: used to scroll the page
def scroll():
    global old_height
    current_scrolls = 0

    while True:
        try:
            if current_scrolls == total_scrolls:
                break

            old_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, scroll_time, 0.05).until(lambda driver: check_height())
            current_scrolls += 1

            if current_scrolls % 100 == 0:
                continue_answer_text = input("continue scrolling (Y/n): ")
                if continue_answer_text.lower().strip() not in ('', 'y', 'yes',):
                    break
        except TimeoutException:
            break
    return


# -------------------------------------------------------------
# -------------------------------------------------------------

# --Helper Functions for Posts

def get_status(x):
    status = ""
    try:
        #status = x.find_element_by_xpath(".//div[@class='_5wj-']").text
        status = x.find_element_by_css_selector("._5wj-").text
    except:
        #log.exception("selector ._5wj- not found")
        try:
            #status = x.find_element_by_xpath(".//div[@class='userContent']").text
            status = x.find_element_by_css_selector(".userContent").text
        except:
            log.exception("selector .userContent not found")
            pass
    return status


def get_div_links(x, tag):
    try:
        temp = x.find_element_by_css_selector("._3x-2")
        return temp.find_element_by_tag_name(tag)
    except:
        log.exception("selector ._3x-2 not found")
        return ""


def get_title_links(title):
    l = title.find_elements_by_tag_name('a')
    return l[-1].text, l[-1].get_attribute('href')


def get_title(x):
    title = ""
    try:
        title = x.find_element_by_xpath(".//span[@class='fwb fcg']")
    except:
        try:
            title = x.find_element_by_xpath(".//span[@class='fcg']")
        except:
            try:
                title = x.find_element_by_xpath(".//span[@class='fwn fcg']")
            except:
                pass
    finally:
        return title


def get_time(x):
    time = ""
    try:
        time = x.find_element_by_tag_name('abbr').get_attribute('title')
        date, hour, daytime = time.split()
        month, day, year = date.split('/')
        year = year.strip(',')
        time = "20{}-{:02d}-{:02d}T{}{}".format(year, int(month), int(day), hour, daytime)
    except:
        pass

    finally:
        return time


def fullpage_screenshot():
    global driver
    print("Starting chrome full page screenshot workaround ...")

    driver.execute_script("document.querySelector('._50ti').setAttribute('style', 'position: absolute !important;');")
    driver.execute_script("document.querySelector('.fixed_elem').setAttribute('style', 'position: absolute !important;');")

    total_width = driver.execute_script("return document.body.offsetWidth * window.devicePixelRatio")
    total_height = driver.execute_script("return document.body.parentNode.scrollHeight * window.devicePixelRatio")
    viewport_width = driver.execute_script("return window.innerWidth * window.devicePixelRatio")
    viewport_height = driver.execute_script("return window.innerHeight * window.devicePixelRatio")

    print("Total: ({0}, {1}), Viewport: ({2},{3})".format(total_width, total_height,viewport_width,viewport_height))
    rectangles = []

    i = 0
    while i < total_height:
        ii = 0
        top_height = i + viewport_height

        if top_height > total_height:
            top_height = total_height

        while ii < total_width:
            top_width = ii + viewport_width

            if top_width > total_width:
                top_width = total_width

            print("Appending rectangle ({0},{1},{2},{3})".format(ii, i, top_width, top_height))
            rectangles.append((ii, i, top_width,top_height))

            ii = ii + viewport_width

        i = i + viewport_height

    part = 0
    for rectangle in rectangles:
        driver.execute_script("window.scrollTo({0}, {1})".format(rectangle[0] / 2, rectangle[1] / 2))
        print("Scrolled To ({0},{1})".format(rectangle[0] / 2, rectangle[1] / 2))
        time.sleep(0.1)

        file_name = "part_{0}.png".format(part)
        print("Capturing {0} ...".format(file_name))

        driver.get_screenshot_as_file(os.path.abspath(file_name))

        if rectangle[1] + viewport_height > total_height:
            offset = (rectangle[0], total_height - viewport_height)
        else:
            offset = (rectangle[0], rectangle[1])

        print("Image for offset ({0}, {1})".format(offset[0],offset[1]))
        part = part + 1

    print("Finishing chrome full page screenshot workaround...")
    return True


def extract_and_write_posts(elements: List[WebElement], filename: str):
    global driver

    fullpage_screenshot()
    viewport_height = driver.execute_script("return window.innerHeight * window.devicePixelRatio")
    pixel_ratio = driver.execute_script("return window.devicePixelRatio")

    try:
        f = open(filename, "a", newline='\r\n')

        for x in elements:  # type: WebElement
            try:
                video_link = " "
                title = " "
                status = " "
                link = ""
                img = " "
                time = " "

                # time
                time = get_time(x)

                # title
                title = get_title(x)
                if title.text.find("shared a memory") != -1:
                    x = x.find_element_by_xpath(".//div[@class='_1dwg _1w_m']")
                    title = get_title(x)

                status = get_status(x)

                if title.text == driver.find_element_by_id("fb-timeline-cover-name").text:
                    if status == '':
                        temp = get_div_links(x, "img")
                        if temp == '':  # no image tag which means . it is not a life event
                            link = get_div_links(x, "a").get_attribute('href')
                            type = "status update without text"
                        else:
                            type = 'life event'
                            link = get_div_links(x, "a").get_attribute('href')
                            status = get_div_links(x, "a").text
                    else:
                        type = "status update"
                        if get_div_links(x, "a") != '':
                            link = get_div_links(x, "a").get_attribute('href')

                elif title.text.find(" shared ") != -1:

                    x1, link = get_title_links(title)
                    type = "shared " + x1

                elif title.text.find(" at ") != -1 or title.text.find(" in ") != -1:
                    if title.text.find(" at ") != -1:
                        x1, link = get_title_links(title)
                        type = "check in"
                    elif title.text.find(" in ") != 1:
                        status = get_div_links(x, "a").text

                elif title.text.find(" added ") != -1 and title.text.find("photo") != -1:
                    type = "added photo"
                    link = get_div_links(x, "a").get_attribute('href')

                elif title.text.find(" added ") != -1 and title.text.find("video") != -1:
                    type = "added video"
                    link = get_div_links(x, "a").get_attribute('href')

                else:
                    type = "others"

                if not isinstance(title, str):
                    title = title.text

                status = status.replace("\n", " ")
                title = title.replace("\n", " ")

                location = x.location
                size = x.size
                _x = location['x'] * pixel_ratio
                y = location['y'] * pixel_ratio
                w = size['width'] * pixel_ratio
                h = size['height'] * pixel_ratio
                width = _x + w
                height = y + h

                screenshot_filename = str(time) + '_' + base64.urlsafe_b64encode(str(time).encode()).decode('utf-8') + '.png'
                screenshot_filepath = os.path.abspath(screenshot_filename)

                #im = load_image_for_page_range(_x, height)
                # calculate where is _x (e.g. it is in part_234.png)
                start_part = math.floor(y * 1. / viewport_height)
                # do the same to figure where is height
                end_part = math.floor(height * 1. / viewport_height)
                # crop parts of the part_X.png images

                stitched_image = Image.new('RGB', (w, h))
                current_height = 0
                # post is present in more than one scrow viewport
                for part_idx in range(start_part, end_part + 1):
                    # height until current viewport
                    height_offset = viewport_height * part_idx

                    # calculate part of the post coordinates in the current viewport
                    top_x = _x
                    top_y = max(0, y - height_offset)
                    bottom_x = width
                    bottom_y = min(viewport_height, height - height_offset)

                    offset = (top_x, top_y, bottom_x, bottom_y)

                    source_img_path = os.path.abspath("part_{0}.png".format(part_idx))
                    source_img = Image.open(source_img_path)

                    log.info("crop dimensions from source \"%s\": top_x=%d top_y=%d bottom_x=%d bottom_y=%d" % (source_img_path,
                        offset[0], offset[1], offset[2], offset[3]))

                    post_source_img = source_img.crop(offset)
                    log.info("current_height = {}".format(current_height))
                    stitched_image.paste(post_source_img, (0, current_height))
                    # save height of the post already added to stitched image
                    # next loop we know where to paste the rest of the post image
                    current_height = current_height + (bottom_y - top_y)

                # save final image after all pices are gathered
                log.info("Saving screenshot at "+ screenshot_filepath)
                stitched_image.save(screenshot_filepath)

                line = json.dumps({
                    'time': str(time),
                    'type': str(type),
                    'title': str(title),
                    'status': str(status),
                    'link': str(link),
                    'screenshot_file': screenshot_filename
                }) + '\n'

                try:
                    f.writelines(line)
                except:
                    print('Posts: Could not map encoded characters')
            except:
                log.exception("something happened")
        f.close()
    except:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    return


# -------------------------------------------------------------
# -------------------------------------------------------------


def save_to_file(name, elements, status, current_section):
    """helper function used to save links to files"""

    # status 0 = dealing with friends list
    # status 1 = dealing with photos
    # status 2 = dealing with videos
    # status 3 = dealing with about section
    # status 4 = dealing with posts

    try:

        f = None  # file pointer

        if status != 4:
            f = open(name, 'a', encoding='utf-8', newline='\n')

        results = []
        img_names = []

        # dealing with Friends
        if status == 0:
            results = [x.get_attribute('href') for x in elements]
            results = [create_original_link(x) for x in results]

            try:
                if download_friends_photos:

                    if friends_small_size:
                        img_links = [x.find_element_by_css_selector('img').get_attribute('src') for x in elements]
                    else:
                        links = []
                        for friend in results:
                            driver.get(friend)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "profilePicThumb")))
                            l = driver.find_element_by_class_name("profilePicThumb").get_attribute('href')
                            links.append(l)

                        for i in range(len(links)):
                            if links[i].find('picture/view') != -1:
                                links[i] = "None"

                        img_links = get_facebook_images_url(links)

                    folder_names = ["Friend's Photos", "Following's Photos", "Follower's Photos", "Work Friends Photos",
                                    "College Friends Photos", "Current City Friends Photos", "Hometown Friends Photos"]
                    print("Downloading " + folder_names[current_section])

                    img_names = image_downloader(img_links, folder_names[current_section])
            except:
                print("Exception (Images)", str(status), "Status =", current_section, sys.exc_info()[0])

        # dealing with Photos
        elif status == 1:
            results = [x.get_attribute('href') for x in elements]
            results.pop(0)

            try:
                if download_uploaded_photos:
                    if photos_small_size:
                        background_img_links = driver.find_elements_by_xpath("//*[contains(@id, 'pic_')]/div/i")
                        background_img_links = [x.get_attribute('style') for x in background_img_links]
                        background_img_links = [((x.split('(')[1]).split(')')[0]).strip('"') for x in
                                                background_img_links]
                    else:
                        background_img_links = get_facebook_images_url(results)

                    folder_names = ["Uploaded Photos", "Tagged Photos"]
                    print("Downloading " + folder_names[current_section])

                    img_names = image_downloader(background_img_links, folder_names[current_section])
            except:
                print("Exception (Images)", str(status), "Status =", current_section, sys.exc_info()[0])

        # dealing with Videos
        elif status == 2:
            results = elements[0].find_elements_by_css_selector('li')
            results = [x.find_element_by_css_selector('a').get_attribute('href') for x in results]

            try:
                if results[0][0] == '/':
                    results = [r.pop(0) for r in results]
                    results = [("https://en-gb.facebook.com/" + x) for x in results]
            except:
                pass

        # dealing with About Section
        elif status == 3:
            results = elements[0].text
            f.writelines(results)

        # dealing with Posts
        elif status == 4:
            extract_and_write_posts(elements, name)
            return

        if (status == 0) or (status == 1):
            for i in range(len(results)):
                f.writelines(results[i])
                f.write(',')
                f.writelines(elements[i].find_element_by_tag_name("img").get_attribute("aria-label"))
                f.write(',')
                try:
                    f.writelines(img_names[i])
                except:
                    f.writelines("None")
                f.write('\n')

        elif status == 2:
            for x in results:
                f.writelines(x + "\n")

        f.close()

    except:
        log.exception("save_to_file")
        print("Exception (save_to_file)", "Status =", str(status), sys.exc_info()[0])

    return


# ----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def scrap_data(id: str, scan_list: List[str], section: List[str], elements_path: List[str], save_status: int, file_names: List[str]) -> None:
    """Given some parameters, this function can scrap friends/photos/videos/about/posts(statuses) of a profile"""
    page = []

    if save_status == 4:
        page.append(id)

    for i in range(len(section)):
        page.append(id + section[i])

    for i in range(len(scan_list)):
        try:
            driver.get(page[i])

            if (save_status == 0) or (save_status == 1) or (
                    save_status == 2):  # Only run this for friends, photos and videos

                # the bar which contains all the sections
                sections_bar = driver.find_element_by_xpath("//*[@class='_3cz'][1]/div[2]/div[1]")

                if sections_bar.text.find(scan_list[i]) == -1:
                    continue

            if save_status != 3:
                scroll()

            data = driver.find_elements_by_xpath(elements_path[i])

            save_to_file(file_names[i], data, save_status, i)

        except:
            print("Exception (scrap_data)", str(i), "Status =", str(save_status), sys.exc_info()[0])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def create_original_link(url: str) -> str:
    if url.find(".php") != -1:
        original_link = "https://en-gb.facebook.com/" + ((url.split("="))[1])

        if original_link.find("&") != -1:
            original_link = original_link.split("&")[0]

    elif url.find("fnr_t") != -1:
        original_link = "https://en-gb.facebook.com/" + ((url.split("/"))[-1].split("?")[0])
    elif url.find("_tab") != -1:
        original_link = "https://en-gb.facebook.com/" + (url.split("?")[0]).split("/")[-1]
    else:
        original_link = url

    return original_link


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def scrap_profile(ids: List[str], config: Config) -> None:
    folder = os.path.join(os.getcwd(), config.data_folder)

    if not os.path.exists(folder):
        os.mkdir(folder)

    os.chdir(folder)

    # execute for all profiles given in input.txt file
    for id in ids:

        driver.get(id)
        url = driver.current_url
        id = create_original_link(url)

        print("\nScraping:", id)

        try:
            target_dir = os.path.join(folder, id.split('/')[-1])
            while os.path.exists(target_dir):
                input("A folder with the same profile name already exists. Kindly remove that folder first and press Return.")
            os.mkdir(target_dir)
            os.chdir(target_dir)
        except:
            print("Some error occurred in creating the profile directory.")
            continue

        # ----------------------------------------------------------------------------
        print("----------------------------------------")
        print("Friends..")
        # setting parameters for scrap_data() to scrap friends
        scan_list = ["All", "Mutual Friends", "Following", "Followers", "Work", "College", "Current City", "Hometown"]
        section = ["/friends", "/friends_mutual", "/following", "/followers", "/friends_work", "/friends_college", "/friends_current_city",
                   "/friends_hometown"]
        elements_path = ["//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a",
        				 "//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a",
                         "//*[contains(@class,'_3i9')][1]/div/div/ul/li[1]/div[2]/div/div/div/div/div[2]/ul/li/div/a",
                         "//*[contains(@class,'fbProfileBrowserListItem')]/div/a",
                         "//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a",
                         "//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a",
                         "//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a",
                         "//*[contains(@id,'pagelet_timeline_medley_friends')][1]/div[2]/div/ul/li/div/a"]
        file_names = ["all-friends.txt", "mutual.txt", "following.txt", "followers.txt", "work-friends.txt", "college-friends.txt",
                      "current-city-friends.txt", "hometown-friends.txt"]
        save_status = 0

        scrap_data(id, scan_list, section, elements_path, save_status, file_names)
        print("Friends Done")


        # ----------------------------------------------------------------------------  
        
        print("----------------------------------------")
        print("Photos..")
        print("Scraping Links..")
        # setting parameters for scrap_data() to scrap photos
        scan_list = ["'s Photos", "Photos of"]
        section = ["/photos_all", "/photos_of"]
        elements_path = ["//*[contains(@id, 'pic_')]"] * 2
        file_names = ["uploaded-photos.txt", "tagged-photos.txt"]
        save_status = 1

        scrap_data(id, scan_list, section, elements_path, save_status, file_names)
        print("Photos Done")

        # ----------------------------------------------------------------------------

        print("----------------------------------------")
        print("Videos:")
        # setting parameters for scrap_data() to scrap videos
        scan_list = ["'s Videos", "Videos of"]
        section = ["/videos_by", "/videos_of"]
        elements_path = ["//*[contains(@id, 'pagelet_timeline_app_collection_')]/ul"] * 2
        file_names = ["uploaded-videos.txt", "tagged-videos.txt"]
        save_status = 2

        scrap_data(id, scan_list, section, elements_path, save_status, file_names)
        print("Videos Done")
        # ----------------------------------------------------------------------------

        print("----------------------------------------")
        print("About:")
        # setting parameters for scrap_data() to scrap the about section
        scan_list = [None] * 7
        section = ["/about?section=overview", "/about?section=education", "/about?section=living",
                   "/about?section=contact-info", "/about?section=relationship", "/about?section=bio",
                   "/about?section=year-overviews"]
        elements_path = ["//*[contains(@id, 'pagelet_timeline_app_collection_')]/ul/li/div/div[2]/div/div"] * 7
        file_names = ["overview.txt", "work-and-education.txt", "places-lived.txt", "contact-and-basic-info.txt",
                      "family-and-relationships.txt", "details-about.txt", "life-events.txt"]
        save_status = 3

        scrap_data(id, scan_list, section, elements_path, save_status, file_names)
        print("About Section Done")

        # ----------------------------------------------------------------------------
        print("----------------------------------------")
        print("Posts:")
        # setting parameters for scrap_data() to scrap posts
        scan_list = [None]
        section = []
        elements_path = ['//div[@class="_5pcb _4b0l _2q8l"]']

        file_names = ["posts.txt"]
        save_status = 4

        scrap_data(id, scan_list, section, elements_path, save_status, file_names)
        print("Posts(Statuses) Done")
        print("----------------------------------------")
    # ----------------------------------------------------------------------------
        
    print("\nProcess Completed.")

    return


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def safe_find_element_by_id(driver, elem_id):
    try:
        return driver.find_element_by_id(elem_id)
    except NoSuchElementException:
        return None

def login(email: str, password: str) -> None:
    """ Logging into our own profile """

    try:
        global driver

        options = Options()

        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")

        try:
            platform_ = platform.system().lower()
            if platform_ in ['linux', 'darwin']:
                driver = webdriver.Chrome(executable_path="chromedriver", options=options)
            else:
                driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
        except:
            print("Kindly replace the Chrome Web Driver with the latest one from "
                  "http://chromedriver.chromium.org/downloads"
                  "\nYour OS: {}".format(platform_)
                 )
            exit(1)

        driver.get("https://en-gb.facebook.com")
        driver.maximize_window()

        # filling the form
        driver.find_element_by_name('email').send_keys(email)
        driver.find_element_by_name('pass').send_keys(password)

        # clicking on login button
        driver.find_element_by_id('loginbutton').click()

        # multi factor authentication
        mfa_code_input = safe_find_element_by_id(driver, 'approvals_code')
        if mfa_code_input is None:
            return
        mfa_code_input.send_keys(input("MFA code: "))
        driver.find_element_by_id('checkpointSubmitButton').click()

        # there are so many screens asking you to verify things. Just skip them all
        while safe_find_element_by_id(driver, 'checkpointSubmitButton') is not None:
            dont_save_browser_radio = safe_find_element_by_id(driver, 'u_0_3')
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id('checkpointSubmitButton').click()

    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def main():
    config = Config()

    ids: List[str] = ["https://en-gb.facebook.com/" + line.split("/")[-1] for line in open("input.txt", newline='\n')]

    if len(ids) > 0:
        print("\nStarting Scraping...")

        login(config_values.email, config_values.password)
        scrap_profile(ids, config)
        driver.close()
    else:
        print("Input file is empty..")


# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

if __name__ == '__main__':
    # get things rolling
    main()
