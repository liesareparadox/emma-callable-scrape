from time import sleep

import PIL.Image

import LogModule
import pandas as pd
import pytesseract as pt
import requests
import csv
from PIL import Image, ImageFilter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common import exceptions

# Set to True to Enable Logging for testing and maintenance
write_logs = True

if write_logs:
    logger = LogModule.enable_logger('MSRB_Scraper')
    logger.info('Logging Enabled')

# set to true to disable browser gui
headless = False

chromedriver_file_location = '/Users/oblivion/PycharmProjects/muuni/bin/chromedriver'
emma_site_url = 'https://emma.msrb.org/TradeData/Search'


def headless_browser():
    if headless:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        return options
    return None


class ChromeWebDriver:
    def __init__(self):
        self.chromedriver_file = chromedriver_file_location
        self.driver = webdriver.Chrome(executable_path=self.chromedriver_file, options=headless_browser())
        self.site_address = emma_site_url

    def go_to_emma_and_accept_disclaimer(self):
        logger.info(f'Opening page "{self.site_address}"')
        self.driver.get(self.site_address)
        butt = self.driver.find_elements_by_xpath('//*[@id="ctl00_mainContentArea_disclaimerContent_yesButton"]')
        butt[0].click()
        sleep(2)

    def specify_callable_yes(self):
        select = Select(self.driver.find_element_by_id('callableOptionsList'))
        select.select_by_value("Y")

    def specify_tax_exempt(self):
        select = Select(self.driver.find_element_by_id('taxableOptionsList'))
        select.select_by_value("N")

    def set_trade_yields(self, minimum, maximum):
        """
        self, minimum value, maximum value)
        must be integer
        """
        self.driver.find_element_by_xpath('//*[@id="tradeYieldFrom"]').send_keys(f'{minimum}')
        self.driver.find_element_by_xpath('//*[@id="tradeYieldTo"]').send_keys(f'{maximum}')
        sleep(.2)

    def click_on_state_dropdown(self):
        self.driver.find_element_by_xpath('//*[@id="searchCriteria"]/ul[2]/li[2]/button').click()
        sleep(.2)

    def get_state_list(self):
        """
        Creates a dictionary of available state values and their index
        :return: dictionary of state: index value pairs
        """
        state_list = {}
        self.click_on_state_dropdown()

        for index in range(0, 57):
            state = self.driver.find_element_by_xpath(f'//*[@id="ui-multiselect-state-option-{index}"]').get_attribute(
                'title')
            state_list.update({state: index})
        return state_list

    def click_on_state(self, state_index):
        """
        This will check and uncheck options in the state dropdown
        :param state_index: 0 - 57
        :return: a check on the specified state index
        """
        self.driver.find_element_by_xpath(f'//*[@id="ui-multiselect-state-option-{state_index}"]').click()
        sleep(.2)

    def specify_search_date(self, start, end):
        """
        Dates must be in mm/dd/yyyy format
        """
        self.driver.find_element_by_xpath('//*[@id="tradeDateFrom"]').send_keys(f'{start}')
        self.driver.find_element_by_xpath('//*[@id="tradeDateTo"]').send_keys(f'{end}')
        sleep(.2)

    def run_search(self):
        self.driver.find_element_by_id('searchButton').click()
        sleep(3)

    def click_display_results_by_100(self):
        """
        selects 100 in the display results dropdown
        """
        display = self.driver.find_element_by_name('lvSearchResults_length')
        Select(display).select_by_value('100')


class DataScraper:
    def __init__(self, driver):
        self.driver = driver
        self.max_n = None
        self.page_search_iterations = None
        self.doc_table = None
        self.translated_image = None

    def __get_number_of_iterations_for_this_search(self):
        try:
            self.page_search_iterations = int(
                self.driver.find_element_by_xpath('//*[@id="lvSearchResults_paginate"]/span/a[6]'
                                                  ).get_attribute('text'))
        except exceptions.NoSuchElementException:
            self.page_search_iterations = 1
        logger.info(f'Number of pages in search: {self.page_search_iterations}')

    def create_document_table(self):
        self.doc_table = pd.DataFrame(columns=['Trade Date/Time',
                                               'CUSIP *',
                                               'Security Description *',
                                               'Coupon(%)',
                                               'MaturityDate',
                                               'Price (%)',
                                               'Yield (%)',
                                               'Calculation Date & Price (%)',
                                               'TradeAmount($)',
                                               'Trade Type',
                                               'SpecialCondition'
                                               ])

    def __capture_cusips_image(self, index):
        self.image = self.driver.find_element_by_xpath(f'//*[@id="lvSearchResults"]/tbody/tr[{index}]/td[2]/ul/li[1]/a')
        image_source = self.image.getAttribute("src")
        url = self.image.current_url()

        image = Image.new()

    def __translate_cusips_from_image(self):
        self.translated_cusips = pt.image_to_string(self.image)

    def add_cusips_to_table(self, table, iterations):
        for cusips in range(1, iterations):
            self.__capture_cusips_image(cusips)
            self.__translate_cusips_from_image()
            table.update(['CUSIP *'][cusips], self.translated_image)

    def copy_data_and_iterate_through_pages(self):

        self.__get_number_of_iterations_for_this_search()

        for pages in range(1, self.page_search_iterations + 1):
            html = self.driver.page_source
            table = pd.read_html(html)[0]
            # cusips_iteration_end_point = len(table)
            # self.add_cusips_to_table(table, cusips_iteration_end_point)
            self.doc_table = self.doc_table.append(table, ignore_index=True, sort=False)
            sleep(1)

            if pages != self.page_search_iterations:
                self.__continue_to_next_page()

    def __continue_to_next_page(self):
        # click to next page and run through the loop again.
        self.driver.find_element_by_id('lvSearchResults_next').click()
        sleep(2)

    def write_csv_file(self):
        self.doc_table.to_csv("emma_test.csv", index=False)


if __name__ == '__main__':
    pass
