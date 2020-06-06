

class EPS:
    def __init__(self, eps_growth_rate, eps_ttm, avg_pe_ratio, logger):
        self.logger = logger
        self.eps_growth_rate = eps_growth_rate
        self.eps_ttm = eps_ttm
        self.avg_pe_ratio = avg_pe_ratio

    # https://www.youtube.com/watch?v=nX2DcXOrtuo
    def calculate(self, no_of_years, rate_of_return):
        eps_list = self._calculate_eps_for_next_n_years(no_of_years)
        fair_price = self._calculate_price_for_next_n_years(eps_list, rate_of_return)
        self.logger.info(f"fair_price_by_eps= {fair_price}")

        return round(fair_price, 2)

    def _calculate_eps_for_next_n_years(self, n_years):

        eps_list = [n_years+1]
        eps_list[0] = self.eps_ttm
        for year in range(1, n_years):
            eps_list.append(eps_list[year-1] + (eps_list[year-1] * self.eps_growth_rate / 100))

        self.logger.debug(f"eps for next {n_years} {eps_list}")
        return eps_list

    def _calculate_price_for_next_n_years(self, eps_list, rate_of_return):
        prices = []
        is_it_n_th_year = True
        prev_year_fair_price = -1

        for eps in reversed(eps_list):
            if is_it_n_th_year:
                is_it_n_th_year = False
                prev_year_fair_price = eps*self.avg_pe_ratio
                prices.append(prev_year_fair_price)
            else:
                prev_year_fair_price = prev_year_fair_price / (1 + (rate_of_return/100))
                prices.append(prev_year_fair_price)

        self.logger.debug(f"fair prices by eps {prices}")

        return prev_year_fair_price





