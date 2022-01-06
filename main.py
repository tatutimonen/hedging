import concurrent.futures
import itertools as it
import threading
import click
from hedger import Hedger
from options_data import OptionsData

#-------------------------------------------------------------------------
# Entry point.

@click.command(no_args_is_help=True)
@click.option("--portfolio-size", "-pfs", multiple=True, type=click.IntRange(min=1, max=5),
              help="Size of the portfolio to be hedged.")
@click.option("--schedule", "-sch", multiple=True, type=click.IntRange(min=1, max=10),
              help="Hedging schedule to consider (in days).")
@click.option("--hedge-type", "-ht", multiple=True, type=click.Choice(["delta", "delta-vega"], case_sensitive=True))
def execute_cmdline(portfolio_size, schedule, hedge_type):
    """A CLI application to evaluate delta and delta-vega hedging performance on portfolios of
       at-the-money call options on S&P 100 during the trading year of 2010."""

    portfolio_size = sorted(set(portfolio_size))
    schedule = sorted(set(schedule))
    hedge_type = sorted(map(lambda x: x.replace("-", "_"), set(hedge_type)))

    data = OptionsData()
    sheets = data.get_sheet_names()

    task_params = it.product(hedge_type, sheets, portfolio_size, schedule)
    results = []
    lock = threading.Lock()
    print("Performing hedging in parallel...")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        stats_futures = [executor.submit(getattr(Hedger, f"{ht}_hedge"), data, sheet, pfs, sch) for ht, sheet, pfs, sch in task_params]
        for stats in concurrent.futures.as_completed(stats_futures):
            lock.acquire()
            results.append(stats.result())
            lock.release()

    for result in results:
        print(result)

#-------------------------------------------------------------------------

if __name__ == "__main__":
    execute_cmdline()
    
#-------------------------------------------------------------------------
