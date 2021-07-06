from argparse import ArgumentParser
import configparser
import mysql.connector
from os import listdir, mkdir, path
import pandas as pd
from re import search
from time import sleep, strftime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Constants
WAIT = 3    # Seconds


def parse_config():
    config = configparser.ConfigParser()
    config.read("conf.ini")
    return config["linkedInAccount"], config["chromedriver"]


def parse_args():
    parser = ArgumentParser(description="LinkedIn Job Search Attributes")
    parser.add_argument('-k', '--keywords', default='Python Developer')
    parser.add_argument('-l', '--location', default='United States')
    parser.add_argument('-e', '--experience', action='append')
    parser.add_argument('-j', '--jobtypes', action='append')
    parser.add_argument('-p', '--pages', type=int, default=10)
    arguments = parser.parse_args()
    return arguments


def iniitialize_driver(driver_loc):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException:
        driver = webdriver.Chrome(executable_path=driver_loc, options=options)
    return driver


def login(driver, home, user, pwd):
    driver.get(home)
    sleep(WAIT - 2)
    driver.find_element_by_xpath('//*[@id="session_key"]').send_keys(user)
    driver.find_element_by_xpath('//*[@id="session_password"]').send_keys(pwd)
    driver.find_element_by_xpath('//*[@id="main-content"]/section[1]/div[2]/form/button').click()
    sleep(WAIT - 2)
    try:
        # Checking if the login page has loaded
        driver.find_element_by_xpath('//a[contains(@href, "jobs")]')
    except NoSuchElementException:
        # Handling 'Remember me on this browser' page
        driver.find_element_by_xpath('//*[@id="remember-me-prompt__form-secondary"]/button').click()
        sleep(WAIT - 2)
        try:
            driver.find_element_by_xpath('//*[@id="ember26"]')
        except NoSuchElementException:
            raise Exception("Unable to log into Linkedin Account!")


def open_jobs(driver):
    driver.find_element_by_xpath('//a[contains(@href, "jobs")]').click()
    sleep(WAIT - 1)


def search_jobs(driver, kws, loc):
    kw_xpath = '//input[starts-with(@id, "jobs-search-box-keyword")]'
    kw_element = WebDriverWait(driver, WAIT + 2).until(EC.presence_of_element_located((By.XPATH, kw_xpath)))
    kw_element.send_keys(kws)
    sleep(WAIT - 2)
    loc_xpath = '//input[starts-with(@id, "jobs-search-box-location")]'
    kw_element = WebDriverWait(driver, WAIT + 2).until(EC.presence_of_element_located((By.XPATH, loc_xpath)))
    kw_element.send_keys(loc + Keys.RETURN)
    sleep(WAIT - 1)


def add_filter(driver, filter_type, filter_values):
    drop_down_xpath = f'//button[contains(@aria-label, "{filter_type} filter")]/li-icon'
    drop_down = WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.XPATH, drop_down_xpath)))
    drop_down.click()
    for filter_value in filter_values:
        sleep(WAIT - 1)
        element = driver.find_element_by_xpath(f'//span[text() = "{filter_value}"]')
        sleep(WAIT - 1)
        element.click()
    drop_down = driver.find_element_by_xpath(drop_down_xpath)
    drop_down.click()
    sleep(WAIT)


def scroll_down_to_load_entire_page(driver):
    div_query_selector = 'document.querySelector("body > div.application-outlet > div.authentication-outlet > ' \
                         'div.job-search-ext > div > div > section.jobs-search__left-rail > div > div")'
    scroll_height = driver.execute_script(f'return {div_query_selector}.scrollHeight')
    for halt in range(700, scroll_height, 700):
        driver.execute_script(f'{div_query_selector}.scrollTo(0, {halt})')
        sleep(WAIT - 2)
    driver.execute_script(f'{div_query_selector}.scrollTo(0, 0)')


def go_to_page(driver, page):
    if page != 1:
        element = driver.find_element_by_xpath(f'//button[@aria-label = "Page {page}"]')
        element.click()
    sleep(WAIT + 1)


def scrape_jobs(driver, total_pages):
    scrape_data = []
    for page in range(1, total_pages + 1):
        go_to_page(driver, page)
        scroll_down_to_load_entire_page(driver)
        jobs = driver.find_elements_by_xpath('//a[contains(@class, "job-card-list__title") and @tabindex = "0"]')
        for job in jobs:
            driver.execute_script("arguments[0].scrollIntoView();", job)
            driver.execute_script("arguments[0].click();", job)
            sleep(WAIT)
            # Collecting information
            title = driver.find_element_by_xpath('.//a[contains(@href, "jobs") and @class="ember-view"]/h2').text
            title_link = driver.find_element_by_xpath('.//a[contains(@href, "jobs") and '
                                                      '@class="ember-view"]').get_attribute("href")
            job_id = search(r'/jobs/view/(\d+)/', title_link).groups()[0]
            company = driver.find_element_by_xpath('.//div[@class="mt2"]/span[1]/span[1]/'
                                                   'a[contains(@href, "company")]').text
            try:
                experience_level = driver.find_element_by_xpath('.//div[@class = "mt5 mb2"]/div[1]/span').text
                experience_level = experience_level.split("·")[-1].strip() if "·" in experience_level else ""
            except NoSuchElementException:
                experience_level = ""
            try:
                industry = driver.find_element_by_xpath('.//div[@class = "mt5 mb2"]/div[2]/span').text
                industry = industry.split("·")[-1].strip() if "·" in industry else ""
            except NoSuchElementException:
                industry = ""
            try:
                apply_button = driver.find_element_by_xpath('.//button[contains(@class, "jobs-apply-button")]/span')
                apply = "Yes" if apply_button.text == "Apply now" else "No"
            except NoSuchElementException:
                try:
                    apply = driver.find_element_by_xpath('.//div[contains(@class, "artdeco-inline-feedback")]/'
                                                         'span[@class = "artdeco-inline-feedback__message"]').text
                except NoSuchElementException:
                    continue
            scrape_data.append(
                {
                    "Job ID": job_id,
                    "Title": f'=HYPERLINK("{title_link}", "{title}")',
                    "Company": company,
                    "Experience Level": experience_level,
                    "Industry": industry,
                    "Easy Apply": apply,
                    "Applied?": 'Yes' if 'applied' in apply.lower() else 'No'
                }
            )
    return scrape_data


def remove_duplicates(df, directory):
    previous_dfs = pd.DataFrame()
    old_files = listdir(directory)
    for file in old_files:
        if file.endswith('.xlsx'):
            df_temp = pd.read_excel(path.join(directory, file))
            previous_dfs = previous_dfs.append(df_temp, ignore_index=True)
    if previous_dfs.empty:
        return df
    previous_dfs = previous_dfs.applymap(str)
    df = df.applymap(str)
    condition = df['Job ID'].isin(previous_dfs['Job ID'])
    df.drop(df[condition].index, inplace=True)
    df.reset_index()
    return df


def create_dataframe(data, folder):
    df = pd.DataFrame(data)
    df["Title"] = df["Title"].apply(lambda x: x)
    df_final = remove_duplicates(df, folder)
    return df_final


def file_setup():
    datetime_stmp = strftime("%Y%m%d-%H%M%S")
    curr_dir = path.dirname(path.abspath(__file__))
    directory = path.join(curr_dir, "Jobs")
    if not path.exists(directory):
        mkdir(directory)
    file_with_full_path = path.join(directory, f"LinkedIn-Jobs-{datetime_stmp}.xlsx")
    return directory, file_with_full_path


def save_to_excel(df, file):
    with pd.ExcelWriter(file, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)


if __name__ == "__main__":
    # Parsing command line arguments
    args = parse_args()
    keywords = args.keywords
    location = args.location
    if args.experience:
        experience = args.experience
    else:
        experience = ['Entry level', 'Associate']
    if args.jobtypes:
        jobtypes = args.jobtypes
    else:
        jobtypes = ["Full-time"]
    pages = args.pages

    # Parsing config.ini file
    linkedin, chrome = parse_config()
    homepage, username, password = linkedin["homepage"], linkedin["username"], linkedin["password"]
    chromedriver = chrome["location"]

    # Initiating the chrome driver
    cdriver = iniitialize_driver(chromedriver)

    # Login to LinkedIn
    login(cdriver, homepage, username, password)

    # Open jobs page
    open_jobs(cdriver)

    # Search jobs
    search_jobs(cdriver, keywords, location)

    # Add experience filter
    add_filter(cdriver, "Experience Level", experience)

    # Add job type filter
    add_filter(cdriver, "Job Type", jobtypes)

    # Scrape jobs
    scraped_data = scrape_jobs(cdriver, pages)

    # File and Folder setup
    folder_path, file_path = file_setup()

    # Create Dataframe
    dframe = create_dataframe(scraped_data, folder_path)

    # Save to Excel
    save_to_excel(dframe, file_path)

    # Close driver
    cdriver.close()
