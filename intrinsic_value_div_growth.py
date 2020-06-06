from math import pow


class Div:
    def __init__(self, div_rate, div_growth_rate, current_price, logger):
        self.logger = logger
        self.div_rate = div_rate
        self.div_growth_rate = div_growth_rate
        self.current_price = current_price

    # https://pocketsense.com/analyze-stock-performance-6556532.html
    def calculate(self, no_of_years, rate_of_return):
        div_payout_by_current_price = self.div_rate / self.current_price
        self.logger.info(f"div_payout_by_current_price= {div_payout_by_current_price}")
        expected_growth_rate = div_payout_by_current_price + self.div_growth_rate / 100
        self.logger.info(f"expected_growth_rate= {expected_growth_rate}")
        next_years_ratio = 1 + expected_growth_rate
        self.logger.info(f"next_years_ratio= {next_years_ratio}")

        n_years_price = pow(next_years_ratio, no_of_years) * self.current_price
        self.logger.info(f"n_years_price= {n_years_price}")
        fair_price = self._calculate_price_for_next_n_years(no_of_years, n_years_price, rate_of_return)

        self.logger.info(f"fair_price_by_div_growth before rate of return = {fair_price}")
        fair_price = fair_price / (1 + rate_of_return/100)
        self.logger.info(f"fair_price_by_div_growth after rate of return = {fair_price}")

        return round(fair_price, 2)

    # https://www.fool.com/knowledge-center/how-to-calculate-future-expected-stock-price.aspx
    def calculate_by_formula(self, rate_of_return):
        next_anual_div = self.div_rate + self.div_growth_rate/100
        self.logger.info(f"next_annual_div= {next_anual_div}")
        self.logger.info(f"div_growth_rate= {self.div_growth_rate}")
        self.logger.info(f"rate_of_return= {rate_of_return}")
        req_rate_of_return = (rate_of_return/100 - self.div_growth_rate/100) * 100
        self.logger.info(f"req_rate_of_return= {req_rate_of_return}")

        fair_price = round((next_anual_div/req_rate_of_return) * 100, 2)

        self.logger.info(f"fair_price_by_formula= {fair_price}")

        return fair_price

    def _calculate_price_for_next_n_years(self, no_of_years, n_years_price, rate_of_return):
        prices = []
        prices.append(n_years_price)
        prev_year_fair_price = n_years_price

        for year in range(no_of_years-1):
            prev_year_fair_price = prev_year_fair_price / (1 + (rate_of_return / 100))
            prices.append(prev_year_fair_price)

        self.logger.debug(f"fair prices by div growth {prices}")

        return prev_year_fair_price





