from math import pow


class BuffetBookIntrinsicValue:
    def __init__(self, forward_div_rate, current_book_val, book_val_growth, avg_forward_eps, years, logger):
        self.logger = logger
        self.forward_div_rate = forward_div_rate
        self.current_book_val = current_book_val
        self.book_val_growth = book_val_growth
        self.avg_forward_eps = avg_forward_eps
        self.years = years
        self.logger.info(f'forward_div_rate={forward_div_rate}')
        self.logger.info(f'current book_val={self.current_book_val}')
        self.logger.info(f'book_val_growth={self.book_val_growth}')
        self.logger.info(f'avg_forward_eps={avg_forward_eps}')
        self.logger.info(f'years={years}')

        if self.book_val_growth >20:
            self.logger.info(f'avg book value={self.book_val_growth} is too big, making div rate growth as 0 and assigning forward_div_rate = avg forward eps growth {self.avg_forward_eps}')
            self.book_val_growth = 0
            self.forward_div_rate = self.avg_forward_eps

    def calculate_intrinsic_value(self, rate):
#         coupon = div_rate = 2.04
#         par = current book val 14.92
#         year = 10
#         r = treasure rate .66
#         bvc = avg book growth = 9.8


# perc=(1+bvc/100);
# base=Math.pow(perc,year);
# parr=par*base;
# r=r/100;
# extra=Math.pow((1+r),year);
# c=coupon*(1-(1/extra))/r+parr/extra;  

        self.logger.debug(f'rate= {rate}')
        perc = (1 + self.book_val_growth / 100)
        self.logger.debug(f'perc= {perc}')
        base = pow(perc, self.years)
        self.logger.debug(f'base= {base}')
        parr = self.current_book_val * base
        self.logger.debug(f'parr= {parr}')
        r = rate / 100
        self.logger.debug(f'r= {r}')
        extra = pow((1 + r), self.years)
        self.logger.debug(f'extra= {extra}')
        self.logger.debug(f'1/extra= {1/extra}')
        self.logger.debug(f'(1-(1/extra)) {(1-(1/extra))}')
        self.logger.debug(f'(1-(1/extra))/r+parr/extra {(1-(1/extra))/r+parr/extra}')
        self.logger.debug(f'self.forward_div_rate {self.forward_div_rate}')
        self.logger.debug(f'self.forward_div_rate*(1-(1/extra))/r+parr/extra {self.forward_div_rate * (1-(1/extra))/r+parr/extra}')

        intrinsic_value = self.forward_div_rate * (1-(1/extra))/r+parr/extra
        self.logger.info(f'intrinsic_value= {intrinsic_value}')
        intrinsic_value = round(intrinsic_value, 2)
        self.logger.debug(f"intrinsic value= {intrinsic_value}")

        return intrinsic_value
