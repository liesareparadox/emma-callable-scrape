import glob
import re
import time
import urllib
from time import sleep

import PyPDF2
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from pikepdf import Pdf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

import LogModule

# Set to True to Enable Logging for testing and maintenance
write_logs = True

if write_logs:
    logger = LogModule.enable_logger('MSRB_Scraper')
    logger.info('Logging Enabled')

# set to true to disable browser gui
headless = False


def headless_browser():
    if headless:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        return options
    return None


class ChromeWebDriver:
    def __init__(self):
        self.chromedriver_file = '/Users/oblivion/PycharmProjects/muuni/bin/chromedriver'
        self.driver = webdriver.Chrome(executable_path=self.chromedriver_file, options=headless_browser())
        self.site_address = 'https://emma.msrb.org/Search/Search.aspx'
        self.state_list = []

    def go_to_emma_and_accept_disclaimer(self):
        logger.info(f'Opening page "{self.site_address}"')
        self.driver.get(self.site_address)
        butt = self.driver.find_elements_by_xpath('//*[@id="ctl00_mainContentArea_disclaimerContent_yesButton"]')
        butt[0].click()
        sleep(2)

    def specify_callable_yes(self):
        """
        accepts a list of purposes
        """
        select = Select(self.driver.find_element_by_id('callableDropDownList'))
        select.select_by_value("Y")

    def get_state_list(self):
        states_dropdown = self.driver.find_element_by_id("stateDropdownList")
        selector = Select(states_dropdown)

        element = WebDriverWait(self.driver, 10).until(ec.element_to_be_selected(selector.options[0]))

        all_states = selector.options
        for states in range(1, len(all_states)):
            self.state_list.append(all_states[states].text)

    def specify_state(self, state):
        self.driver.find_element_by_xpath('//*[@id="stateDropdownList"]').click()
        # select = Select(self.driver.find_element_by_id('stateDropdownList'))
        # select.select_by_value(state)

    def specify_search_date(self, start, end):
        """
        Dates must be in mm/dd/yyyy format
        """
        self.driver.find_element_by_xpath('//*[@id="datedDateFrom"]').send_keys(f'{start}')
        self.driver.find_element_by_xpath('//*[@id="datedDateTo"]').send_keys(f'{end}')

    def run_search(self):
        self.driver.find_element_by_xpath('//*[@id="runSearchButton"]').click()

    def change_view_to_be_by_issuers(self):
        self.driver.find_element_by_xpath('//*[@id="issuesTab"]').click()

    def select_purpose_of_muni_bond(self, purpose_of_muni_bond):
        select = Select(self.driver.find_element_by_name('lvIssues_length'))
        select.select_by_visible_text(purpose_of_muni_bond)
        self.driver.find_element_by_xpath('/html/body/form/div[10]/div/div/div[2]/button').click()


# now that we have the page the way we want it to look, we can look through all the pages for bond names issuer names
# and links
class DataScraper(ChromeWebDriver):
    def __init__(self):
        super().__init__()
        self.max_n = None
        self.page_search_iterations = None
        self.doc_table = None

    def setup_data_scraper(self):
        self.max_n = int(self.driver.find_element_by_id('lvIssues_info').text.split(' ')[5].replace(',', ''))
        self.page_search_iterations = int(np.ceil(self.max_n / 100))

    def __create_document_table(self):
        self.doc_table = pd.DataFrame(columns=['Issuer Name', 'Description', 'State', 'Dated Date', 'link'])

        # num of pages to go through.

    def __iterate_through_pages(self):
        for pages in range(0, self.page_search_iterations):
            html = self.driver.page_source
            table = pd.read_html(html)[4]
            soup = BeautifulSoup(html, 'html.parser')

            # look for the link to bond issue page.
            table['link'] = [item.get('href') for item in soup.find_all("a", href=re.compile("IssueView"))]

            self.doc_table.append(table, ignore_index=True)
            time.sleep(5)

    def __continue_to_next_page(self):
        # click to next page and run through the loop again.
        self.driver.find_element_by_xpath(
            '/html/body/form/div[9]/div[3]/div[2]/div[2]/div[6]/div[3]/div/div/div[5]/a[3]').click()

    def __create_bond_id(self):
        self.doc_table['ID'] = [link.split('/')[-1] for link in self.doc_table['link']]

    def go_through_list_of_links_and_download_the_pdfs(self):
        for i in range(6, len(self.doc_table)):
            link = self.doc_table['link'][i]
            name = self.doc_table['ID'][i]
            url = link.replace('..', 'https://emma.msrb.org')

            try:
                self.driver.get(url)
                time.sleep(2)
                self.driver.find_element_by_xpath('//*[@id="ui-id-4"]').click()
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                pdf_link = [item.get('href') for item in soup.find_all("a", href=re.compile(".pdf"))][0]
                urllib.request.urlretrieve('https://emma.msrb.org' + pdf_link, f'{name}.pdf')

                time.sleep(5)
            except Exception as e:
                # print name if error occurs.
                logger.warn(e)
                print(name)


def get_list_of_downloaded_pdfs():
    txt_files = []
    for file in glob.glob("*.pdf"):
        txt_files.append(file.replace('\\', '/'))
    return txt_files


def decrypt_pdfs(txt_files):
    for file in txt_files:
        try:
            new_pdf = Pdf.new()
            with Pdf.open(file) as pdf:
                pdf.save('E:/Users/atag3/Documents/Project_Data/Pull2/decrypted/' + file.split('/')[-1])
        except Exception:
            print(file)


def create_list_decrypted_pdfs():
    txt_files = []
    for file in glob.glob("E:/Users/atag3/Documents/Project_Data/Pull2/decrypted/*.pdf"):
        txt_files.append(file.replace('\\', '/'))


def read_pdf_files(txt_files):
    go_text = {}
    for file in txt_files:
        try:
            # open allows you to read the file.
            pdf_file_obj = open(file, 'rb')
            # The pdfReader variable is a readable object that will be parsed.
            pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

            # Discerning the number of pages will allow us to parse through all the pages.
            num_pages = pdf_reader.numPages
            count = 0
            text = ""
            # The while loop will read each page.
            while count < num_pages:
                page_obj = pdf_reader.getPage(count)
                count += 1
                text += page_obj.extractText()
            # This if statement exists to check if the above library returned words. It's done because PyPDF2 cannot read
            # scanned files.
            if text != "":
                text = text
            # If the above returns as False, we run the OCR library textract to #convert scanned/image based PDF files
            # into text.
            else:
                # this might be able to help with document scans but I was running into issues and it only helped with a
                # few documents. text = textract.process(fileurl, method='tesseract', language='eng')
                continue
            # Now we have a text variable that contains all the text derived from

            go_text[file] = {'doc': text}
        except Exception:
            print(file)


if __name__ == '__main__':
    pass
