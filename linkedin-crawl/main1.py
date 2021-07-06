from argparse import ArgumentParser
from crawljobs import CrawlJobs
import configparser


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

    # Crawling LinkedIn jobs listings
    cj = CrawlJobs(chromedriver)  # Initializing chromedriver
    cj.login(homepage, username, password)  # Login to LinkedIn
    cj.open_jobs()  # Open jobs section/page
    cj.search_jobs(keywords, location)  # Search jobs based on keywords and location provided
    cj.add_filter("Experience Level", experience)  # Add filter for Experience Level
    cj.add_filter("Job Type", jobtypes)  # Add filter for Job Types
    scraped_data = cj.scrape_jobs(pages)    # Scrape jobs from first {pages} pages

    # Setting up file name and location
    folder_path, file_path = cj.file_setup()

    # Creating dataframe from the scraped data after handling duplicates from the previously saved xlsx's
    dframe = cj.create_dataframe(scraped_data, folder_path)

    # Save the final draft to an excel document and close the driver
    cj.save_to_excel(dframe, file_path)
    cj.close_driver()
