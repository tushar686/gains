from lxml import html
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Raw():
    """
        //requests
        page = requests.get('')
        tree = html.fromstring(page.content)
        print(tree.xpath(x))

        //selenium
        //phantom
            driver = webdriver.PhantomJS()
            driver.get(f'https://www.zacks.com/stock/chart/plugfundamental/peg-ratio-ttm')
            ele = driver.find_element_by_xpath('//*[@id="stock_comp_desc"]/p')
        //chrome
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(options=options)


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
        self.logger.debug(f"getting raw data for {self.ticker}")

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        # self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.PhantomJS()
        self.exchanges = ['NASDAQ', 'NYSE']


        self.yahoo_finance_quote()
        self.yahoo_finance_key_statistics()
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

        # marketbeat
        self.marketbeat_profile()
        self.marketbeat_inst()
        self.marketbeat_insider()
        self.marketbeat_short()

    def _get_float_value(self, val):
        self.logger.debug(f"get_float i/p: {val}")
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
        self.logger.debug(f"get_float o/p: {val}")
        try:
            return float(val)
        except ValueError as e:
            self.logger.error(e)
            return 0.0

    # h52wk_drop, l52wk_up, eps_ttm
    def yahoo_finance_quote(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}')
        tree = html.fromstring(page.content)
  
        current_price = tree.xpath('//*[@id="quote-header-info"]/div[3]/div[1]/div/span[1]/text()')
        self.logger.debug(f"current price{current_price}")
        current_price = self._get_float_value(current_price)
        self.current_price = current_price
        h52wk_drop = 1.0
        l52wk_up = 1.0
        eps_ttm = 1.0
        
        h_l_list = [1, 1]
        h_l = tree.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[6]/td[2]/text()')
        self.logger.debug(f'52_wk_h_l_str= {h_l}')
        if not h_l:
            h_l = ['N', 'N']
        self.logger.debug(f'52_wk_h_l_str= {h_l[0].split(" ")}')
        h_l_list = h_l[0].split(" ")

        if 'N' not in h_l_list[0] and 'N' not in h_l_list[2]:
            l = self._get_float_value(h_l_list[0])
            h = self._get_float_value(h_l_list[2])

            self.logger.debug(f'52_wk_h= {h}')
            self.logger.debug(f'52_wk_l= {l}')
            if h != 0:
                h52wk_drop = (100 - (current_price / h * 100))
                self.logger.debug(f'h52wk drop = {h52wk_drop}')
            if l != 0:
                l52wk_up = ((current_price / l * 100) - 100)    
                self.logger.debug(f'l52wk up = {l52wk_up}')
        self.h52wk_drop = round(h52wk_drop, 2)
        self.l52wk_up = round(l52wk_up, 2)

        eps_ttm = tree.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[4]/td[2]/span/text()')
        self.logger.debug(f"eps ttm {eps_ttm}")
        if not eps_ttm or 'N/A' in eps_ttm[0]:
            eps_ttm = 0
        else:
            eps_ttm = self._get_float_value(eps_ttm)
        self.logger.debug(f'eps_ttm up = {eps_ttm}')
        self.eps_ttm = eps_ttm

        mkt_cap = tree.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[1]/td[2]/span/text()')
        self.logger.debug(f"mkt cap {mkt_cap}")
        self.mkt_cap = mkt_cap


    def yahoo_finance_key_statistics(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}/key-statistics')
        tree = html.fromstring(page.content)

        sma_50d = tree.xpath('//*[@id="Col1-0-KeyStatistics-Proxy"]/section/div[3]/div[2]/div/div[1]/div/div/table/tbody/tr[6]/td[2]/text()')
        sma_200d = tree.xpath('//*[@id="Col1-0-KeyStatistics-Proxy"]/section/div[3]/div[2]/div/div[1]/div/div/table/tbody/tr[7]/td[2]/text()')
        self.sma_50d = self._get_float_value(sma_50d)
        self.sma_200d = self._get_float_value(sma_200d)
        peg = tree.xpath('//*[@id="Col1-0-KeyStatistics-Proxy"]/section/div[3]/div[1]/div[2]/div/div[1]/div[1]/table/tbody/tr[5]/td[2]/text()')
        self.peg = self._get_float_value(peg)
        self.logger.debug(f'yf peg {self.peg}')

        shares_outstanding = tree.xpath('//*[@data-test="qsp-statistics"]/div[3]/div[2]/div/div[2]/div/div/table/tbody/tr[3]/td[2]/text()')

        self.logger.debug(f'shares_outstanding= {shares_outstanding}')

        if shares_outstanding:
            shares_outstanding = shares_outstanding[0]
            if shares_outstanding.find('M') > 0:
                shares_outstanding = shares_outstanding.replace('M', '')
            if shares_outstanding.find('B') > 0:
                shares_outstanding = shares_outstanding.replace('B', '')    
                shares_outstanding = self._get_float_value(shares_outstanding) * 10.00
        shares_outstanding = self._get_float_value(shares_outstanding)                
        self.logger.debug(f'shares_outstanding= {shares_outstanding}')

        forward_div_rate = 0
        cnt = str(page.content)
        start = cnt.find('"dividendRate":{"raw":')
        end = cnt.find(',', start)
        if start > 0:
            div_rate_str = cnt[start:end]
            self.logger.debug(f'div_rate_str= {div_rate_str}')
            val_idx = div_rate_str.rindex(':')
            forward_div_rate_str = div_rate_str[val_idx+1:]
            self.logger.debug(f'forward_div_rate_str= {forward_div_rate_str}')
            forward_div_rate = self._get_float_value(forward_div_rate_str)

        self.forward_div_rate = forward_div_rate 
        self.shares_outstanding = shares_outstanding

    # get_analyst_estimates_growth_rate_and_avg_forward_eps_growth
    def yahoo_finance_analysis(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}/analysis?p={self.ticker}')
        tree = html.fromstring(page.content)

        self.sales_growth_c_q = self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[2]/span/text()'))
        self.sales_growth_n_q = self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[3]/span/text()'))
        self.sales_growth_c_y = self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[4]/span/text()'))
        self.sales_growth_n_y = self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[6]/td[5]/span/text()'))
        
        self.growth_c_q =  self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[1]/td[2]/text()'))
        self.growth_n_q =  self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[2]/td[2]/text()'))
        self.growth_c_y =  self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[3]/td[2]/text()'))
        self.growth_n_y =  self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[4]/td[2]/text()'))
        self.growth_n_5y = self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]/text()'))
        self.growth_p_5y = self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[6]/td[2]/text()'))

        # this is dup but float val required for fair price by eps calculation
        growth_next_5_yrs = tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]/text()')
        if not growth_next_5_yrs:
            growth_next_5_yrs = ['0']
        self.logger.debug(f"growth estimates: Next 5 Years (per annum) {growth_next_5_yrs[0]}")
        self.growth_next_5_yrs = self._get_float_value(growth_next_5_yrs)

        # "earningsEstimate":{"avg":{"raw":9.81
        avg_forward_eps = tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[5]/span/text()')
        self.logger.debug(f"avg eps estimates for next year {avg_forward_eps}")
        self.avg_forward_eps = self._get_float_value(avg_forward_eps)

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

            avg_pe_ratio = (self._get_float_value(pe_ratio_low) + self._get_float_value(
                pe_ratio_high) + self._get_float_value(pe_ratio_med)) / 3

            # if p/e high is way to high use current p/e ratio
            if self._get_float_value(pe_ratio_high) > self._get_float_value(pe_ratio_low) \
                    + self._get_float_value(pe_ratio_med) + 50:
                self.logger.debug(f"high p/e {pe_ratio_high} is too high so using current {pe_ratio_current}")
                if self._get_float_value(pe_ratio_med) > self._get_float_value(pe_ratio_current):
                    self.logger.debug(f"med p/e {pe_ratio_med} is also too high so discarding it")
                    avg_pe_ratio = (self._get_float_value(pe_ratio_low) + self._get_float_value(pe_ratio_current) ) / 2
                else:
                    avg_pe_ratio = (self._get_float_value(pe_ratio_low) + self._get_float_value(pe_ratio_current) + self._get_float_value(pe_ratio_med)) / 3

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
        self.avg_book_value = self._get_float_value(avg_book_value_growth)
        self.avg_op_income = self._get_float_value(avg_ebit_growth)

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

        div_growth_3_yr_avg = tree.xpath('//*[@id="dividend"]/div/table[2]/tbody/tr[3]/td[2]/text()')
        self.logger.debug(f"div_growth_3_yr_avg: {div_growth_3_yr_avg}")

        self.div_avg_growth = self._get_float_value(div_growth_3_yr_avg)
        
        price_to_op_cash_flow = tree.xpath('//*[@id="ratios"]/div/table[2]/tbody/tr[8]/td[2]/text()')
        self.logger.debug(f"price_to_op_cash_flow {price_to_op_cash_flow}")
        self.price_to_op_cash_flow = self._get_float_value(price_to_op_cash_flow)

        ev = tree.xpath('//*[@id="stock-header"]/div/div[1]/div/div[3]/div[8]/text()')
        self.logger.debug(f'ev= {ev}')
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
            val = tree.xpath(f'//*[@id="ratios"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'PE Ratio':
                self.pe = self._get_float_value(val)
            if key == 'Forward PE Ratio':
                self.fwd_pe = self._get_float_value(val)
            if key == 'PB Ratio':
                self.pb = self._get_float_value(val)
            if key == 'PS Ratio':
                self.ps = self._get_float_value(val)
            if key == 'Price-to-Operating-Cash-Flow':
                self.price_to_op_cash_flow = self._get_float_value(val)
            if key == 'Current Ratio':
                self.cur_ratio = self._get_float_value(val)
            if key == 'EV-to-Revenue':
                self.ev_to_sales = self._get_float_value(val)
            if key == 'EV-to-EBITDA':
                self.ev_to_ebitda = self._get_float_value(val)


                
        self.dbt_to_equity = 0
        tbody = tree.xpath('//*[@id="financial-strength"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="financial-strength"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="financial-strength"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'Debt-to-Equity':
                self.dbt_to_equity = self._get_float_value(val)
        
        self.op_margin = 0
        self.rev_growth_3yr = 0
        tbody = tree.xpath('//*[@id="profitability"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="profitability"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="profitability"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'Operating Margin %':
                self.op_margin = self._get_float_value(val)                
            if key == '3-Year Revenue Growth Rate':
                self.rev_growth_3yr = self._get_float_value(val)

        self.div_yield = 0
        self.div_payout_ratio = 0
        tbody = tree.xpath('//*[@id="dividend"]/div/table[2]/tbody/tr')
        for tr_idx in range(len(tbody)):
            key = tree.xpath(f'//*[@id="dividend"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[1]/a/text()')
            val = tree.xpath(f'//*[@id="dividend"]/div/table[2]/tbody/tr[{tr_idx+1}]/td[2]/text()')
            key = key[0].replace('\n', '')
            if key == 'Dividend Yield %':
                self.div_yield = self._get_float_value(val)
            if key == 'Dividend Payout Ratio':
                self.div_payout_ratio = self._get_float_value(val) * 100

    def get_latest_treasury_rate(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get('https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield')
        tree = html.fromstring(page.content)

        latest_rate = tree.xpath('//*[@id="t-content-main-content"]/div/table/tr/td/div/table/tr[last()]/td[11]/text()')
        self.logger.debug(f"latest treasury rates {latest_rate}")
        self.latest_treasury_rate = self._get_float_value(latest_rate)

    def macrotrends_fcf(self):
        self.logger.debug(f'__________________________________________')
        fcf_sum = 0
        
        try:
            page = requests.get(f'https://www.macrotrends.net/stocks/charts/{self.ticker}/microsoft/free-cash-flow')
            tree = html.fromstring(page.content)
        except TooManyRedirects:
            pass

        for i in range(1, 11):
            fcf = tree.xpath(f'//*[@id="style-1"]/div[1]/table/tbody/tr[{i}]/td[2]/text()')
            self.logger.debug(f"yr{i}_fcf= {fcf}")
            fcf_val = self._get_float_value(fcf)
            fcf_sum = fcf_sum + fcf_val
        
        fcf_avg = round(fcf_sum / 10, 2)
        self.logger.info(f"fcf_avg {fcf_avg}")

        self.avg_fcf_of_last_10_years = fcf_avg

    def marketbeat_profile(self):
        self.logger.debug(f'__________________________________________')
        emp = 0
        
        page = requests.get(f'https://www.marketbeat.com/stocks/NASDAQ/{self.ticker}/')

        tree = html.fromstring(page.content)

        emp = tree.xpath('//*[@id="cphPrimaryContent_tabCompanyProfile"]/div[2]/div[2]/ul[1]/li[11]/strong/text()')
        self.logger.debug(f"# employees {emp}")
        self.emp = self._get_float_value(emp)
        
        roe = tree.xpath('//*[@id="cphPrimaryContent_tabCompanyProfile"]/div[2]/div[2]/ul[3]/li[4]/strong/text()')
        self.logger.debug(f"roe {roe}")
        self.roe = self._get_float_value(roe)

        if self.peg == 0 or self.peg == 0.0 or self.peg == 0.1:
            peg = tree.xpath('//*[@id="cphPrimaryContent_tabCompanyProfile"]/div[2]/div[2]/ul[5]/li[3]/strong/text()')
            self.logger.debug(f"peg {peg}")
            self.peg = self._get_float_value(peg)



    def marketbeat_inst(self):
        self.logger.debug(f'__________________________________________')
        institutaion_ownership = 0
        
        page = self._get_page_for_exchanges(f'https://www.marketbeat.com/stocks/exchange/{self.ticker}', 'institutional-ownership/')     

        tree = html.fromstring(page.content)
        institutaion_ownership = tree.xpath('//*[@id="cphPrimaryContent_tabInstitutionalOwnership"]/div[1]/text()')
        self.logger.debug(f"institutaion_ownership {institutaion_ownership}")
        self.institutaion_ownership = self._get_float_value(institutaion_ownership)

    def marketbeat_insider(self):
        self.logger.debug(f'__________________________________________')
        insider_ownership = 0
        
        page = self._get_page_for_exchanges(f'https://www.marketbeat.com/stocks/exchange/{self.ticker}', 'insider-trades/')     
        
        tree = html.fromstring(page.content)
        insider_ownership = tree.xpath('//*[@id="cphPrimaryContent_tabInsiderTrades"]/div[1]/table/tr[1]/td[2]/text()')
        self.logger.debug(f"insider_ownership {insider_ownership}")
        self.insider_ownership = self._get_float_value(insider_ownership)        

    def marketbeat_short(self):
        self.logger.debug(f'__________________________________________')
        short_days_to_cover = 0
        
        page = self._get_page_for_exchanges(f'https://www.marketbeat.com/stocks/exchange/{self.ticker}', 'short-interest/')     
        
        tree = html.fromstring(page.content)
        short_days_to_cover = tree.xpath('//*[@id="cphPrimaryContent_tabShortInterest"]/div[1]/div[1]/table/tbody/tr[5]/td/text()')
        self.logger.debug(f"short_days_to_cover {short_days_to_cover}")
        self.short_days_to_cover = self._get_float_value(short_days_to_cover)        

    def _get_page_for_exchanges(self, url, anchor):
        # nasdaq_url = f'https://www.marketbeat.com/stocks/{exchange}/{self.ticker}'
        page = None
        for exchange in self.exchanges:
            exchanged_url = url.replace('exchange', exchange)
            page = requests.get(f'{exchanged_url}/{anchor}')
            if exchanged_url in page.url:
                return page
        
        return page




