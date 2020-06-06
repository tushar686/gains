from math import pow


class DCFIntrinsicValue:
    def __init__(self, avg_fcf, fcf_growth_rate, shares_outstanding, logger):
        self.logger = logger
        self.avg_fcf = avg_fcf
        self.fcf_growth_rate = fcf_growth_rate
        self.shares_outstanding = shares_outstanding

        self.logger.info(f'avg_fcf= {self.avg_fcf}')
        self.logger.info(f'fcf_growth_rate= {self.fcf_growth_rate}')
        self.logger.info(f'shares_outstanding= {self.shares_outstanding}')
        

    def calculate_intrinsic_value(self, discount_rate):
        intrinsic_value = 0
        long_term_growth_rate = 3

        fcf_list = self._calculate_fcf_for_next_n_years(10, self.avg_fcf)
        df_list = self._calculate_dfcf_for_next_n_years(11, discount_rate)
        dfcf_list, sum_dfcf = self._calculate_dfcf(fcf_list, df_list , 10)

        perpetuity_value = (fcf_list[len(fcf_list)-1] * (1 + long_term_growth_rate/100)) / ((discount_rate - long_term_growth_rate) / 100)
        self.logger.info(f"perpetuity_value {perpetuity_value}")

        present_value = perpetuity_value / pow(1+discount_rate/100, 10)
        self.logger.info(f"perpetuity_value {present_value}")

        net_valuation = sum_dfcf + present_value
        self.logger.info(f"net_valuation {net_valuation}")

        intrinsic_value = round(net_valuation / self.shares_outstanding, 2)
        self.logger.info(f"intrinsic_value {intrinsic_value}")
        
        return intrinsic_value

    def _calculate_fcf_for_next_n_years(self, n_years, avg_fcf):

        fcf_list = [n_years+2]
        fcf_list[0] = avg_fcf
        for year in range(1, n_years+1):
            fcf_list.append(fcf_list[year-1] + (fcf_list[year-1] * self.fcf_growth_rate / 100))

        self.logger.debug(f"fcf_list {fcf_list}")
        return fcf_list

    def _calculate_dfcf_for_next_n_years(self, n_years, discount_rate):
        df_list = [n_years+1]
        df_list[0] = discount_rate
        for year in range(1, n_years):
            df_list.append( round(pow(1 + discount_rate/100, year), 2))

        self.logger.debug(f"df_list {df_list}")
        return df_list

    def _calculate_dfcf(self, fcf_list, df_list, n_years):    
        dfcf_list = [n_years+2]
        for year in range(1, n_years+1):
            dfcf_list.append( round(fcf_list[year] / df_list[year], 2))

        self.logger.debug(f"dfcf_list {dfcf_list}")
        sum_dfcf = sum(dfcf_list[1:len(dfcf_list)])
        self.logger.debug(f'sum_dfcf= {sum_dfcf}')

        return df_list, sum_dfcf
