import logging
import time

from WebscraperFuntion import DataScraper

if __name__ == '__main__':
    state = 'AK'
    bond_purpose = '100'
    start_date = '03/01/2021'
    end_date = '04/01/2021'

    muni_search = DataScraper()

    muni_search.go_to_emma_and_accept_disclaimer()

    muni_search.specify_callable_yes()

    muni_search.specify_search_date(start_date, end_date)

    muni_search.run_search()

    muni_search.change_view_to_be_by_issuers()

    muni_search.select_purpose_of_muni_bond(bond_purpose)

    time.sleep(0)

    muni_search.driver.close()
