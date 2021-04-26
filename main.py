import logging
from time import sleep
import time

from WebscraperFuntion import DataScraper
from WebscraperFuntion import ChromeWebDriver

if __name__ == '__main__':
    start_date = '03/01/2021'
    end_date = '03/02/2021'
    trade_yield_min = 0
    trade_yield_max = 6

    # Go to Emma site setup initial search parameters and create the state iterable list
    muni_search = ChromeWebDriver()

    muni_search.go_to_emma_and_accept_disclaimer()

    muni_search.specify_callable_yes()

    muni_search.specify_tax_exempt()

    muni_search.set_trade_yields(trade_yield_min, trade_yield_max)

    muni_search.specify_search_date(start_date, end_date)

    states = muni_search.get_state_list()

    muni_search.click_on_state(states['AK'])

    muni_search.run_search()

    muni_search.click_display_results_by_100()

    # setup data scraper
    data_scraper = DataScraper(muni_search.driver)

    data_scraper.create_document_table()

    data_scraper.copy_data_and_iterate_through_pages()

    data_scraper.write_csv_file()

    data_scraper.driver.close()
