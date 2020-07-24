from lxml import html
import requests

class Raw():
    """
        page = requests.get('')
        tree = html.fromstring(page.content)
        print(tree.xpath(x))
    """
    AVG_KEYS = ['avg_eps_c_q', 'avg_eps_n_q', 'avg_eps_c_y', 'avg_eps_n_y', 'avg_rev_c_q', 'avg_rev_n_q', 'avg_rev_c_y', 'avg_rev_n_y', 'growth_c_q', 'growth_n_q', 'growth_c_y', 'growth_n_y', 'growth_n_5y', 'growth_p_5y']

    def __init__(self, ticker, logger):
        self.ticker = ticker
        self.logger = logger
        self.logger.debug(f"getting raw data for {self.ticker}")

        # yahoo/quote
        self.current_price, self.h52wk_drop, self.eps_ttm = self.get_current_price_52wk_drop_eps_ttm()
        # yahoo/key-statistics
        self.pe, self.pb, self.forward_div_rate, self.shares_outstanding = self.get_current_pe_pb_forward_div_rate_shares_outstanding()
        self.ret = round(((1 / self.pe) * 100), 2)
        self.margin = round(((1 / self.pb) * 100), 2)
        self.book_value = round(self.current_price/self.pb, 2)
        # yahoo/analysis
        self.analyst_growth_rate_estimates, self.avg_forward_eps, self.growth = self.get_analyst_estimates_growth_rate_and_avg_forward_eps_growth()

        # gurufocus/PE-Ratio
        self.avg_pe_ratio = self.get_avg_pe_ratio()
        # gurufocus/dcf
        self.avg_book_value, self.avg_op_income = self.get_avg_book_ebit_value() # ebit = oprating income
        # gurufocus/summary
        self.div_avg_growth = self.get_div_3_yr_avg_growth_rate()

        # treasury.gov
        self.latest_treasury_rate = self.get_latest_treasury_rate()

        # https://www.macrotrends.net/stocks/charts/MSFT/microsoft/free-cash-flow
        self.avg_fcf_of_last_10_years = self.get_avg_fcf_of_last_10_years()

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

    def get_current_price_52wk_drop_eps_ttm(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}?p={self.ticker}')
        tree = html.fromstring(page.content)

        current_price = tree.xpath('//*[@id="quote-header-info"]/div[3]/div/span[1]/text()')
        self.logger.debug(f"current price{current_price}")
        current_price = self._get_float_value(current_price)

        h52wk_drop = 1.0
        eps_ttm = 1.0
        try:
            h_l_list = [1, 1]
            h_l = tree.xpath('//*[@id="quote-summary"]/div[1]/table/tbody/tr[6]/td[2]/text()')
            self.logger.debug(f'52_wk_h_l_str= {h_l}')
            self.logger.debug(f'52_wk_h_l_str= {h_l[0].split(" ")}')
            h_l_list = h_l[0].split(" ")

            if 'N' not in h_l_list[0] and 'N' not in h_l_list[2]:
                l = self._get_float_value(h_l_list[0])
                h = self._get_float_value(h_l_list[2])

                self.logger.debug(f'52_wk_h: {h}')
                self.logger.debug(f'52_wk_l= {l}')
                if h != 0:
                    h52wk_drop = (100 - (current_price / h * 100))
                self.logger.debug(f'h52wk drop = {h52wk_drop}')

            eps_ttm = tree.xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[4]/td[2]/span/text()')
            self.logger.debug(f"eps ttm {eps_ttm}")
            if 'N/A' in eps_ttm[0]:
                eps_ttm = 0
            else:
                eps_ttm = self._get_float_value(eps_ttm)
        except:
            self.logger.error("error calculating 52wk drop or eps")            

        return current_price, h52wk_drop, eps_ttm

    def get_current_pe_pb_forward_div_rate_shares_outstanding(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}/key-statistics')
        tree = html.fromstring(page.content)

        pb = tree.xpath('//*[@data-test="qsp-statistics"]/div[3]/div[1]/div[2]/div/div[1]/div[1]/table/tbody/tr[7]/td[2]/text()')
        pe = tree.xpath('//*[@data-test="qsp-statistics"]/div[3]/div[1]/div[2]/div/div[1]/div[1]/table/tbody/tr[3]/td[2]/text()')
        shares_outstanding = tree.xpath('//*[@data-test="qsp-statistics"]/div[3]/div[2]/div/div[2]/div/div/table/tbody/tr[3]/td[2]/text()')

        self.logger.debug(f'pb= {pb}')
        self.logger.debug(f'pe= {pe}')
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

        pe = self._get_float_value(pe)
        pb = self._get_float_value(pb)

        if pe == 0:
            pe = 1
        if pb == 0:
            pb = 1

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

        return pe, pb, forward_div_rate, shares_outstanding

    def get_analyst_estimates_growth_rate_and_avg_forward_eps_growth(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://finance.yahoo.com/quote/{self.ticker}/analysis?p={self.ticker}')
        tree = html.fromstring(page.content)

        growth = {'avg_eps_c_q':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[2]/span/text()')),
                  'avg_eps_n_q':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[3]/span/text()')),
                  'avg_eps_c_y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[4]/span/text()')),
                  'avg_eps_n_y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[5]/span/text()')),
                  'avg_rev_c_q':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[2]/td[2]/span/text()')),
                  'avg_rev_n_q':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[2]/td[3]/span/text()')),
                  'avg_rev_c_y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[2]/td[4]/span/text()')),
                  'avg_rev_n_y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[2]/tbody/tr[2]/td[5]/span/text()')),
                  'growth_c_q': self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[1]/td[2]/text()')),
                  'growth_n_q': self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[2]/td[2]/text()')),
                  'growth_c_y': self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[3]/td[2]/text()')),
                  'growth_n_y': self._get_float_value(tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[4]/td[2]/text()')),
                  'growth_n_5y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]/text()')),
                  'growth_p_5y':self._get_float_value( tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[6]/td[2]/text()'))
                  }

        growth_next_5_yrs = tree.xpath('//*[@data-test="qsp-analyst"]/table[6]/tbody/tr[5]/td[2]/text()')
        if not growth_next_5_yrs:
            growth_next_5_yrs = ['0']
        self.logger.debug(f"growth estimates: Next 5 Years (per annum) {growth_next_5_yrs[0]}")

        # "earningsEstimate":{"avg":{"raw":9.81
        avg_eps = tree.xpath('//*[@data-test="qsp-analyst"]/table[1]/tbody/tr[2]/td[5]/span/text()')
        self.logger.debug(f"avg eps estimates for next year {avg_eps}")

        return self._get_float_value(growth_next_5_yrs), self._get_float_value(avg_eps),  growth

    def get_avg_pe_ratio(self):
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

        return avg_pe_ratio

    def get_avg_book_ebit_value(self):
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
        return self._get_float_value(avg_book_value_growth), self._get_float_value(avg_ebit_growth)

    def _get_gurufocus_dcf_data(self, cnt, var_token):    
        var_token_start = cnt.find(var_token)
        if var_token_start > 0:
            val_start = cnt.find(":", var_token_start)
            val_end = cnt.find(",", var_token_start)
            return cnt[val_start + 1:val_end]
        return '0'


    def get_div_3_yr_avg_growth_rate(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://www.gurufocus.com/stock/{self.ticker}/summary')
        tree = html.fromstring(page.content)

        div_growth_3_yr_avg = tree.xpath('//*[@id="dividend"]/div/table[2]/tbody/tr[3]/td[2]/text()')
        self.logger.debug(f"div_growth_3_yr_avg: {div_growth_3_yr_avg}")

        return self._get_float_value(div_growth_3_yr_avg)

    def get_latest_treasury_rate(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get('https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield')
        tree = html.fromstring(page.content)

        latest_rate = tree.xpath('//*[@id="t-content-main-content"]/div/table/tr/td/div/table/tr[last()]/td[11]/text()')
        self.logger.debug(f"latest treasury rates {latest_rate}")

        return self._get_float_value(latest_rate)

    def get_avg_fcf_of_last_10_years(self):
        self.logger.debug(f'__________________________________________')
        page = requests.get(f'https://www.macrotrends.net/stocks/charts/{self.ticker}/microsoft/free-cash-flow')
        tree = html.fromstring(page.content)

        fcf_sum = 0

        for i in range(1, 11):
            fcf = tree.xpath(f'//*[@id="style-1"]/div[1]/table/tbody/tr[{i}]/td[2]/text()')
            self.logger.debug(f"yr{i}_fcf= {fcf}")
            fcf_val = self._get_float_value(fcf)
            fcf_sum = fcf_sum + fcf_val
        
        fcf_avg = round(fcf_sum / 10, 2)
        self.logger.info(f"fcf_avg {fcf_avg}")

        return fcf_avg
        



