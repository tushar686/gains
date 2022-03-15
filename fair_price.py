from intrinsic_value_eps_growth import EPS
from intrinsic_value_div_growth import Div
from intrinsic_value_bfbk import BuffetBookIntrinsicValue
from intrinsic_value_dcf import DCFIntrinsicValue

def calculate_fair_price(rd, logger):
    fair_eps_by_eps_growth = EPS(eps_growth_rate=rd.growth_next_5_yrs,
                                eps_ttm=rd.eps_ttm, avg_pe_ratio=rd.avg_pe_ratio, logger=logger)
    fair_price_by_eps = fair_eps_by_eps_growth.calculate(no_of_years=10, rate_of_return=15)
    logger.warning(f"fair_price_by_eps= {fair_price_by_eps}")

    fair_price_by_div = Div(div_rate=rd.forward_div_rate, div_growth_rate=rd.div_avg_growth,
                            current_price=rd.current_price, logger=logger)
    fair_price_by_div_growth = fair_price_by_div.calculate(no_of_years=10, rate_of_return=20)
    logger.warning(f"fair_price_by_div_growth= {fair_price_by_div_growth}")
    fair_price_by_div_formula = fair_price_by_div.calculate_by_formula(rate_of_return=15)
    logger.warning(f"fair_price_by_div_formula= {fair_price_by_div_formula}")

    buffet_book_intrinsic_value = BuffetBookIntrinsicValue(rd.forward_div_rate, rd.book_value, rd.avg_book_value, rd.avg_forward_eps, 10, logger)
    bb_intrinsic_value_by_treasury_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(rd.latest_treasury_rate)
    logger.warning(f"bb_intrinsic_value_by_treasury_rate= {bb_intrinsic_value_by_treasury_rate}")
    bb_intrinsic_value_by_exp_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(10)
    logger.warning(f"bb_intrinsic_value_by_exp_rate= {bb_intrinsic_value_by_exp_rate}")
    dcf = DCFIntrinsicValue(rd.avg_fcf_of_last_10_years, rd.avg_op_income, rd.shares_outstanding, logger)
    intrinsic_value_by_dcf = dcf.calculate_intrinsic_value(10)
    logger.warning(f"intrinsic_value_by_dcf= {intrinsic_value_by_dcf}")

