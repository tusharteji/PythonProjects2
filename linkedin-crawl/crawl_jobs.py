from argparse import ArgumentParser
import configparser
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, WebDriverException


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
    sleep(1)
    driver.find_element_by_xpath('//*[@id="session_key"]').send_keys(user)
    driver.find_element_by_xpath('//*[@id="session_password"]').send_keys(pwd)
    driver.find_element_by_xpath('//*[@id="main-content"]/section[1]/div[2]/form/button').click()
    sleep(1)
    try:
        # Checking if the login page has loaded
        driver.find_element_by_xpath('//*[@id="ember26"]')
    except NoSuchElementException:
        # Handling 'Remember me on this browser' page
        driver.find_element_by_xpath('//*[@id="remember-me-prompt__form-secondary"]/button').click()
        sleep(1)
        try:
            driver.find_element_by_xpath('//*[@id="ember26"]')
        except NoSuchElementException:
            raise Exception("Unable to log into Linkedin Account!")


def open_jobs(driver):
    driver.find_element_by_xpath('//*[@id="ember26"]').click()
    sleep(2)


def search_jobs(driver, kws, loc):
    driver.find_element_by_xpath('//input[starts-with(@id, "jobs-search-box-keyword")]').send_keys(kws)
    sleep(1)
    driver.find_element_by_xpath('//input[starts-with(@id, "jobs-search-box-location")]').send_keys(loc + Keys.RETURN)
    sleep(2)


def add_experience_filter(driver, exp_levels):
    drop_down = driver.find_element_by_xpath('//button[contains(@aria-label, "Experience Level filter")]/li-icon')
    drop_down.click()
    for level in exp_levels:
        try:
            element = driver.find_element_by_xpath(f'//input[@aria-label = "Filter by {level}"]')
            driver.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            element = driver.find_element_by_xpath(f'//input[@aria-label = "Filter by {level}"]')
            driver.execute_script("arguments[0].click();", element)
        sleep(2)
    drop_down = driver.find_element_by_xpath('//button[contains(@aria-label, "Experience Level filter")]/li-icon')
    drop_down.click()
    sleep(2)


def add_job_type_filter(driver, job_types):
    drop_down = driver.find_element_by_xpath('//button[contains(@aria-label, "Job Type filter")]/li-icon')
    drop_down.click()
    for jobtype in job_types:
        try:
            element = driver.find_element_by_xpath(f'//input[@aria-label = "Filter by {jobtype}"]')
            driver.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            element = driver.find_element_by_xpath(f'//input[@aria-label = "Filter by {jobtype}"]')
            driver.execute_script("arguments[0].click();", element)
        sleep(2)
    drop_down = driver.find_element_by_xpath('//button[contains(@aria-label, "Job Type filter")]/li-icon')
    drop_down.click()
    sleep(2)


def scrape_jobs(driver):
    jobs = driver.find_element_by_xpath('//ul[contains(@class, "jobs-search-results")]')
    print(jobs)
    for i, job in enumerate(jobs):
        job.find_element_by_xpath(f'.//li[{i+1}]/div/div/div[1]/div[2]/div[1]/a').click()


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

    # Parsing config.ini file
    linkedin, chrome = parse_config()
    homepage = linkedin["homepage"]
    username = linkedin["username"]
    password = linkedin["password"]
    chromedriver = chrome["location"]

    # Initiating the chrome driver
    cdriver = iniitialize_driver(chromedriver)

    # Login to LinkedIn
    login(cdriver, homepage, username, password)

    # Open jobs page
    open_jobs(cdriver)

    # Search jobs
    search_jobs(cdriver, keywords, location)
    add_experience_filter(cdriver, experience)
    add_job_type_filter(cdriver, jobtypes)

    # Scrape jobs
    scrape_jobs(cdriver)

    # Close driver
    cdriver.close()

