from lxml import html

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import logging

class RawSmall():

    def __init__(self, ticker, logger):
        self.ticker = ticker
        self.logger = logger
        # disable requests logging
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        logging.getLogger('selenium').setLevel(logging.CRITICAL)

        self.finviz_quote()

    # h52wk_drop, l52wk_up, eps_ttm, peg, mcap, income, rsi, shares outstanding
    def finviz_quote(self):
        self.logger.debug(f'__________________________________________')
        driver = webdriver.PhantomJS()
        driver.get(f'https://finviz.com/quote.ashx?t={self.ticker}')
        snapshot_table_ele = driver.find_element_by_class_name('snapshot-table2')
        
        self.current_price = self._get_float_value('current_price', snapshot_table_ele.find_element_by_xpath('tbody/tr[11]/td[12]/b').text)


    def _get_float_value(self, key, val):
        self.logger.debug(f'{key} = {val}')
        if isinstance(val, list):
            if len(val) == 0:
                self.logger.debug(f"empty list returning 0: {val}")
                return 0.1
            val = val[0]
        if type(val) is float:
            return val
        val = val.replace("%", "")
        val = val.replace("B", "")
        val = val.replace("M", "")
        val = val.replace("'", "")
        val = val.replace("\nCurrent: ", "")
        val = val.replace(",", "")
        val = val.replace("$", "")
        # self.logger.debug(f"o/p = {val}")
        try:
            return float(val)
        except ValueError as e:
            self.logger.debug(e)
            return 0.0        
