from lxml import html

import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import logging


class Raw():
    """
        //requests
        page = requests.get('')
        tree = html.fromstring(page.content)
        print(tree.xpath(''))

        //with phantomJS
            driver = webdriver.PhantomJS()
            driver.get(f'https://www.zacks.com/stock/chart/plugfundamental/peg-ratio-ttm')
            print(driver.find_element_by_xpath(''))
            print(driver.find_element_by_class_name(''))
        //with chrome
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(options=options)
        //screenshot
            driver.save_screenshot("screenshot.png")    


        import importlib
        importlib.reload(raw)

        import logging
        import raw
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level='DEBUG')
        logger = logging.getLogger('gains')
        ticker = 'MSFT'
        raw_data = raw.Raw(ticker, logger)

    """

    def __init__(self, ticker, logger):
        self.ticker = ticker
        self.logger = logger
        # disable requests logging
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        logging.getLogger('selenium').setLevel(logging.CRITICAL)

        self.current_price = self.pb = 100

        self.finviz_quote()

        self.yahoo_finance_analysis()

        self.gurufocus_term_pettm()
        self.gurufocus_stock_dcf()
        self.gurufocus_stock_summary()
        # todo:re-understand what these two things are
        # self.ret = round(((1 / self.pe) * 100), 2)
        # self.margin = round(((1 / self.pb) * 100), 2)
        self.book_value = round(self.current_price/self.pb, 2)

        # treasury.gov
        self.get_latest_treasury_rate()

        # macrotrends
        self.macrotrends_fcf()

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

    # h52wk_drop, l52wk_up, eps_ttm, peg, mcap, income, rsi, shares outstanding
    def finviz_quote(self):
        self.logger.debug(f'__________________________________________')
        driver = webdriver.PhantomJS()
        driver.get(f'https://finviz.com/quote.ashx?t={self.ticker}')
        snapshot_table_ele = driver.find_element_by_class_name('snapshot-table2')
        
        self.current_price = self._get_float_value('current_price', snapshot_table_ele.find_element_by_xpath('tbody/tr[11]/td[12]/b').text)
        self.eps_ttm = self._get_float_value('eps_ttm', snapshot_table_ele.find_element_by_xpath('tbody/tr[1]/td[6]/b').text)
        self.peg = self._get_float_value('peg', snapshot_table_ele.find_element_by_xpath('tbody/tr[3]/td[4]/b').text)
        self.income = snapshot_table_ele.find_element_by_xpath('tbody/tr[3]/td[2]/b').text
        
        self.mkt_cap = snapshot_table_ele.find_element_by_xpath('tbody/tr[2]/td[2]/b').text
        self.rsi = snapshot_table_ele.find_element_by_xpath('tbody/tr[9]/td[10]/b').text
        self.perf_yr = snapshot_table_ele.find_element_by_xpath('tbody/tr[5]/td[12]/b').text
        self.perf_ytd = snapshot_table_ele.find_element_by_xpath('tbody/tr[6]/td[12]/b').text
        self.logger.debug(f'perf_yr= {self.perf_yr}, perf_ytd = {self.perf_ytd}, rsi={self.rsi}, mkt_cap={self.mkt_cap}')

        self.gross_margin = snapshot_table_ele.find_element_by_xpath('tbody/tr[8]/td[8]/b').text
        self.op_margin = snapshot_table_ele.find_element_by_xpath('tbody/tr[9]/td[8]/b').text
        self.profit_margin = snapshot_table_ele.find_element_by_xpath('tbody/tr[10]/td[8]/b').text
        self.emp = snapshot_table_ele.find_element_by_xpath('tbody/tr[9]/td[2]/b').text
        self.short_days_to_cover = snapshot_table_ele.find_element_by_xpath('tbody/tr[4]/td[10]/b').text
        self.logger.debug(f'gross_margin= {self.gross_margin}, op_margin = {self.op_margin}, profit_margin={self.profit_margin}, emp={self.emp}, short_days_to_cover={self.short_days_to_cover}')

        self.institutaion_ownership = snapshot_table_ele.find_element_by_xpath('tbody/tr[1]/td[8]/b').text
        self.institutaion_trans = snapshot_table_ele.find_element_by_xpath('tbody/tr[2]/td[8]/b').text
        self.insider_ownership = snapshot_table_ele.find_element_by_xpath('tbody/tr[3]/td[8]/b').text
        self.insider_trans = snapshot_table_ele.find_element_by_xpath('tbody/tr[4]/td[8]/b').text
        self.roe = snapshot_table_ele.find_element_by_xpath('tbody/tr[6]/td[8]/b').text
        self.logger.debug(f'institutaion_ownership= {self.institutaion_ownership}, institutaion_trans = {self.institutaion_trans}, insider_ownership={self.insider_ownership}, insider_trans={self.insider_trans}, roe={self.roe}')


        self.range_52wk = snapshot_table_ele.find_element_by_xpath('tbody/tr[6]/td[10]/b').text
        self.drop_from_52wkh = snapshot_table_ele.find_element_by_xpath('tbody/tr[7]/td[10]/b').text
        self.up_from_52wkl = snapshot_table_ele.find_element_by_xpath('tbody/tr[8]/td[10]/b').text
        self.logger.debug(f'52wk range= {self.range_52wk} drop from high = {self.drop_from_52wkh}, up from low={self.up_from_52wkl}')

        self.forward_div_rate = 0
        forward_div_rate = snapshot_table_ele.find_element_by_xpath('tbody/tr[7]/td[2]/b').text
        if forward_div_rate is not '-':
            self.forward_div_rate = self._get_float_value('forward_div_rate', forward_div_rate)        

        shares_outstanding = snapshot_table_ele.find_element_by_xpath('tbody/tr[1]/td[10]/b').text
        self.logger.debug(f'shares_outstanding= {shares_outstanding}')
        self.shares_outstanding = 1
        if shares_outstanding:
            if shares_outstanding.find('M') > 0:
                shares_outstanding = shares_outstanding.replace('M', '')
            if shares_outstanding.find('B') > 0:
                shares_outstanding = shares_outstanding.replace('B', '')    
                shares_outstanding = self._get_float_value('shares_outstanding', shares_outstanding) * 10.00
                shares_outstanding = self._get_float_value('shares_outstanding', shares_outstanding)                
                self.shares_outstanding = shares_outstanding
            self.logger.debug(f'shares_outstanding= {shares_outstanding}')    
        

    # get_analyst_estimates_growth_rate_and_avg_forward_eps_growth
    def yahoo_finance_analysis(self):
        self.logger.debug(f'__________________________________________')
        driver = webdriver.PhantomJS()
        driver.get(f'https://finance.yahoo.com/quote/{self.ticker}/analysis?p={self.ticker}')

        self.sales_growth_c_q = self._get_float_value('sales_growth_c_q', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[2]/span').text)
                                                                   
        self.sales_growth_n_q = self._get_float_value('sales_growth_n_q', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[3]/span').text)
        self.sales_growth_c_y = self._get_float_value('sales_growth_c_y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[4]/span').text)
        self.sales_growth_n_y = self._get_float_value('sales_growth_n_y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[5]/span').text)
        
        self.growth_c_q = self._get_float_value('growth_c_q', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[1]/td[2]').text)
        self.growth_n_q = self._get_float_value('growth_n_q', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[2]/td[2]').text)
        self.growth_c_y = self._get_float_value('growth_c_y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[3]/td[2]').text)
        self.growth_n_y = self._get_float_value('growth_n_y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[4]/td[2]').text)
        self.growth_n_5y = self._get_float_value('growth_n_5y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]').text)
        self.growth_p_5y = self._get_float_value('growth_p_5y', driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[6]/td[2]').text)

        # this is dup but float val required for fair price by eps calculation
        growth_next_5_yrs = driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]')
        if not growth_next_5_yrs:
            growth_next_5_yrs = ['0']
            self.growth_next_5_yrs = self._get_float_value('growth_next_5_yrs', growth_next_5_yrs)
        else:
            self.growth_next_5_yrs = self._get_float_value('growth_next_5_yrs', growth_next_5_yrs.text)

        # "earningsEstimate":{"avg":{"raw":9.81
        avg_forward_eps = driver.find_element_by_xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[5]/span')
        self.avg_forward_eps = self._get_float_value('avg_forward_eps', avg_forward_eps.text)

    # avg pe
    def gurufocus_term_pettm(self):
        self.logger.debug(f'__________________________________________')
        avg_pe_ratio = 0
        url = f'https://www.gurufocus.com/term/pettm/{self.ticker}/PE-Ratio/{self.ticker}'
        self.logger.debug(url)
        page = requests.get(url)
        tree = html.fromstring(page.content)
        pe = tree.xpath('//*[@id="pettm_tools"]/strong/text()')
        self.logger.debug(f"pe string {pe}")
        if len(pe) > 1:
            pe_past_str = pe[0]
            pe_ratio_current = pe[1]
            self.logger.debug(f"pe_past_str {pe_past_str}")
            pe_past_list = pe_past_str.split(' ')
            self.logger.debug(f"pe_past_list {pe_past_list}")
            pe_ratio_high = pe_past_list[5]
            pe_ratio_med = pe_past_list[3]
            pe_ratio_low = pe_past_list[1]

            self.logger.debug(f"pe_ratio_current {pe_ratio_current}")
            self.logger.debug(f"pe_ratio_low {pe_ratio_low}")
            self.logger.debug(f"pe_ratio_med {pe_ratio_med}")
            self.logger.debug(f"pe_ratio_high {pe_ratio_high}")

            avg_pe_ratio = (self._get_float_value('pe_ratio_low', pe_ratio_low) + self._get_float_value('pe_ratio_high', pe_ratio_high) 
                            + self._get_float_value('pe_ratio_med', pe_ratio_med)) / 3

            # if p/e high is way to high use current p/e ratio
            if self._get_float_value('pe_ratio_high', pe_ratio_high) > self._get_float_value('pe_ratio_low', pe_ratio_low) \
                    + self._get_float_value('pe_ratio_med', pe_ratio_med) + 50:
                self.logger.debug(f"high p/e {pe_ratio_high} is too high so using current {pe_ratio_current}")
                if self._get_float_value('pe_ratio_med', pe_ratio_med) > self._get_float_value('pe_ratio_current', pe_ratio_current):
                    self.logger.debug(f"med p/e {pe_ratio_med} is also too high so discarding it")
                    avg_pe_ratio = (self._get_float_value('pe_ratio_low', pe_ratio_low) + self._get_float_value('pe_ratio_current', pe_ratio_current) ) / 2
                else:
                    avg_pe_ratio = (self._get_float_value('pe_ratio_low', pe_ratio_low) + self._get_float_value('pe_ratio_current', pe_ratio_current) + self._get_float_value('pe_ratio_med', pe_ratio_med)) / 3

            self.logger.debug(f"avg_ratio {avg_pe_ratio}")
        self.avg_pe_ratio = avg_pe_ratio

    # avg_book_value, avg_op_income # ebit = oprating income
    def gurufocus_stock_dcf(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://www.gurufocus.com/stock/{self.ticker}/dcf')
        cnt = str(page.content)
        
        avg_book_value_growth = self._get_gurufocus_dcf_data(cnt, "book_growth_10y:")
        self.logger.debug(f"10y avg_book_value_growth: {avg_book_value_growth}")
        if avg_book_value_growth == 'a' or avg_book_value_growth == '$':
            avg_book_value_growth = self._get_gurufocus_dcf_data(cnt, "book_growth_5y:")
            self.logger.debug(f"5y avg_book_value_growth: {avg_book_value_growth}")

        avg_ebit_growth = self._get_gurufocus_dcf_data(cnt, "ebit_growth_10y:")
        self.logger.debug(f"10y avg_ebit_growth: {avg_ebit_growth}")
        if avg_ebit_growth == 'a':
            avg_ebit_growth = self._get_gurufocus_dcf_data(cnt, "ebit_growth_5y:")
            self.logger.debug(f"5y avg_ebit_growth: {avg_ebit_growth}")
            if avg_ebit_growth == 'aY':
                avg_ebit_growth = self._get_gurufocus_dcf_data(cnt, "ebitda_growth_10y:")
                self.logger.debug(f"10y avg_ebitda_growth: {avg_ebit_growth}")
                if avg_ebit_growth == 'a':
                    avg_ebit_growth = self._get_gurufocus_dcf_data(cnt, "ebitda_growth_5y:")
                    self.logger.debug(f"5y avg_ebitda_growth: {avg_ebit_growth}")

        self.logger.debug(f"avg_ebit_growth: {avg_ebit_growth}")
        self.avg_book_value = self._get_float_value('avg_book_value', avg_book_value_growth)
        self.avg_op_income = self._get_float_value('avg_op_income', avg_ebit_growth)

    def _get_gurufocus_dcf_data(self, cnt, var_token):    
        var_token_start = cnt.find(var_token)
        if var_token_start > 0:
            val_start = cnt.find(":", var_token_start)
            val_end = cnt.find(",", var_token_start)
            return cnt[val_start + 1:val_end]
        return '0'

    # div_3_yr_avg_growth_rate, price-to-op
    def gurufocus_stock_summary(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://www.gurufocus.com/stock/{self.ticker}/summary')
        tree = html.fromstring(page.content)

        div_growth_3_yr_avg = tree.xpath('//*[@id="dividend"]/div/table[2]/tbody/tr[3]/td[2]/span[2]/text()')

        self.div_avg_growth = self._get_float_value('div_avg_growth', div_growth_3_yr_avg)
        
        price_to_op_cash_flow = tree.xpath('//*[@id="ratios"]/div/table[2]/tbody/tr[8]/td[2]/span[2]/text()')
        self.price_to_op_cash_flow = self._get_float_value('price_to_op_cash_flow', price_to_op_cash_flow)

        ev = tree.xpath('//*[@id="stock-header"]/div/div[1]/div/div[3]/div[8]/text()')
        self.ev = ev

        self.pe = 0.1
        self.cur_ratio = 0
        self.fwd_pe = 0.1
        self.pb = 0.1
        self.ps = 0.1
        self.ev_to_sales = 0.1
        self.ev_to_ebitda = 0.1
        self.price_to_op_cash_flow = 0.1
        tbody = tree.xpath('//*[@id="ratios"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="ratios"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="ratios"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/span[2]/text()')
            key = key[0].replace('\n', '')
            # self.logger.debug(f"key={key}, val={val}")
            if key == 'PE Ratio':
                self.pe = self._get_float_value('pe', val)
            if key == 'Forward PE Ratio':
                self.fwd_pe = self._get_float_value('fwd_pe', val)
            if key == 'PB Ratio':
                self.pb = self._get_float_value('pb', val)
            if key == 'PS Ratio':
                self.ps = self._get_float_value('ps', val)
            if key == 'Price-to-Operating-Cash-Flow':
                self.price_to_op_cash_flow = self._get_float_value('price_to_op_cash_flow', val)
            if key == 'Current Ratio':
                self.cur_ratio = self._get_float_value('cur_ratio', val)
            if key == 'EV-to-Revenue':
                self.ev_to_sales = self._get_float_value('ev_to_sales', val)
            if key == 'EV-to-EBITDA':
                self.ev_to_ebitda = self._get_float_value('ev_to_ebitda', val)


                
        self.dbt_to_equity = 0
        tbody = tree.xpath('//*[@id="financial-strength"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="financial-strength"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="financial-strength"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/span[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'Debt-to-Equity':
                self.dbt_to_equity = self._get_float_value('dbt_to_equity', val)
        
    
        self.rev_growth_3yr = 0
        tbody = tree.xpath('//*[@id="profitability"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="profitability"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="profitability"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/span[2]/text()')
            key = key[0].replace('\n', '')
            if key == '3-Year Revenue Growth Rate':
                self.rev_growth_3yr = self._get_float_value('rev_growth_3yr', val)

        self.div_yield = 0
        self.div_payout_ratio = 0
        tbody = tree.xpath('//*[@id="dividend"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="dividend"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="dividend"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/span[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'Dividend Yield %':
                self.div_yield = self._get_float_value('div_yield', val)
            if key == 'Dividend Payout Ratio':
                self.div_payout_ratio = round(self._get_float_value('val', val) * 100, 2)

    def get_latest_treasury_rate(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get('https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield')
        tree = html.fromstring(page.content)

        latest_rate = tree.xpath('//*[@id="t-content-main-content"]/div/table/tr/td/div/table/tr[last()]/td[11]/text()')
        self.latest_treasury_rate = self._get_float_value('latest_treasury_rate', latest_rate)

    def macrotrends_fcf(self):
        # self.logger.debug(f'__________________________________________')
        # fcf_sum = 0
        
        # try:
        #     page = requests.get(f'https://www.macrotrends.net/stocks/charts/{self.ticker}/microsoft/free-cash-flow')
        #     tree = html.fromstring(page.content)
        # except TooManyRedirects:
        #     pass

        # for i in range(1, 11):
        #     fcf = tree.xpath(f'//*[@id="style-1"]/div[1]/table/tbody/tr[{i}]/td[2]/text()')
        #     fcf_val = self._get_float_value('fcf_val', fcf)
        #     fcf_sum = fcf_sum + fcf_val
        
        # fcf_avg = round(fcf_sum / 10, 2)
        # self.logger.debug(f"fcf_avg {fcf_avg}")

        # find other source to calculate........

        self.avg_fcf_of_last_10_years = 100

    def _get_page_for_exchanges(self, url, anchor):
        # nasdaq_url = f'https://www.marketbeat.com/stocks/{exchange}/{self.ticker}'
        page = None
        for exchange in self.exchanges:
            exchanged_url = url.replace('exchange', exchange)
            page = requests.get(f'{exchanged_url}/{anchor}')
            if exchanged_url in page.url:
                return page
        
        return page




