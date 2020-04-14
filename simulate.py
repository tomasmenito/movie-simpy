"""
Movies line

- wants to wait at most 10 minutes

"""
import logging
import random
import statistics
from dataclasses import dataclass
from datetime import timedelta
from itertools import groupby, product

import simpy

logging.basicConfig(level=logging.DEBUG)


class Theater:
    def __init__(self, env, num_cashiers, num_servers, num_ushers):
        self.env = env
        self.cashier = simpy.Resource(env, num_cashiers)
        self.server = simpy.Resource(env, num_servers)
        self.usher = simpy.Resource(env, num_ushers)

    def purchase_ticket(self, moviegoer):
        yield self.env.timeout(random.randint(1, 3))

    def check_ticket(self, moviegoer):
        yield self.env.timeout(3 / 60)

    def sell_food(self, moviegoer):
        yield self.env.timeout(random.randint(1, 5))


def go_to_movies(env, moviegoer, theater, wait_times):
    # Moviegoer arrives at the theater
    arrival_time = env.now

    with theater.cashier.request() as request:
        yield request
        yield env.process(theater.purchase_ticket(moviegoer))

    with theater.usher.request() as request:
        yield request
        yield env.process(theater.check_ticket(moviegoer))

    if random.choice([True, False]):
        with theater.server.request() as request:
            yield request
            yield env.process(theater.sell_food(moviegoer))

    # Moviegoer heads into the theater
    wait_times.append(env.now - arrival_time)


def run_theater(env, num_cashiers, num_servers, num_ushers, wait_times):
    theater = Theater(env, num_cashiers, num_servers, num_ushers)

    for moviegoer in range(3):
        env.process(go_to_movies(env, moviegoer, theater, wait_times))

    for _ in range(27):
        yield env.timeout(0.20)  # Wait a bit before generating new moviegoer

        # Almost done!...
        moviegoer += 1
        env.process(go_to_movies(env, moviegoer, theater, wait_times))

    return wait_times


def calculate_wait_time(wait_times):
    # print([round(t) for t in wait_times])
    average_wait = statistics.mean(wait_times)
    # Pretty print the results
    return timedelta(minutes=average_wait)


def run_simulation(num_cashiers, num_servers, num_ushers):
    wait_times = []
    # Run the simulation
    env = simpy.Environment()
    env.process(
        run_theater(env, num_cashiers, num_servers, num_ushers, wait_times)
    )
    env.run()
    return wait_times


def calculate_average_wait_time_for_config(
    num_cashiers, num_servers, num_ushers, num_simulations
):
    all_wait_times = []
    for _ in range(num_simulations):
        all_wait_times += run_simulation(num_cashiers, num_servers, num_ushers)

    return calculate_wait_time(all_wait_times).total_seconds()


def generate_employee_config(max_employees):
    num_places = 3
    return (
        config
        for config in product(range(1, max_employees + 1), repeat=num_places)
        if sum(config) <= max_employees
    )


def main():
    # Setup
    random.seed(42)

    # Run simulation
    average_time_by_employee_config = []

    max_employees = 10
    num_simulations = 10

    for num_cashiers, num_servers, num_ushers in generate_employee_config(
        max_employees
    ):
        average_time = calculate_average_wait_time_for_config(
            num_cashiers, num_servers, num_ushers, num_simulations,
        )
        average_time_by_employee_config.append(
            EmployeeConfig(num_cashiers, num_servers, num_ushers, average_time)
        )

    def total_employees_key(e):
        return e.total_employees

    average_time_by_employee_config.sort(key=total_employees_key)
    for k, g in groupby(average_time_by_employee_config, total_employees_key):
        if True:
            g = list(g)
            for group_item in g:
                logging.debug(group_item)
        best_config = min(g, key=lambda e: e.average_time)
        logging.info(f"For {k} employees, best config is {best_config}\n")


@dataclass
class EmployeeConfig:
    num_cashiers: int
    num_servers: int
    num_ushers: int

    average_time: float

    @property
    def total_employees(self):
        return sum((self.num_cashiers, self.num_servers, self.num_ushers))


if __name__ == "__main__":
    main()
