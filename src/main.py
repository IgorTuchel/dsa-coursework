import argparse
import sys
import time

from yaspin import yaspin

from algorithms.inital_solution import clarke_wright_algo
from generators.data_generator import generate_data_to_csv
from models.model import Customer
from utils.parser import create_models_from_csv


def main():
    argParser = argparse.ArgumentParser(
        description="Several proposed implementations of CVRP"
    )
    argParser.add_argument("name", help="Dataset name e.g sample_1 -> sample_1.csv")
    argParser.add_argument(
        "-g", "--generate", action="store_true", help="Generate a new dataset"
    )
    argParser.add_argument("-c", "--customers", type=int, default=500)
    argParser.add_argument("-w", "--weight", type=int, default=10)
    argParser.add_argument("-s", "--size", type=int, default=250)

    args = argParser.parse_args()

    if args.generate:
        generate_data_to_csv(args.customers, args.weight, args.size, args.name)
        print(f"Generated Dataset: {args.name}.csv")
        sys.exit(0)

    if args.name:
        path = f"./data/{args.name}.csv"
        customers = create_models_from_csv(path)
        start = time.perf_counter()
        with yaspin(text=f"Solving CVRP for {args.name}.csv", timer=True).blue:
            routes = clarke_wright_algo(Customer(0, 0, 0, 0), customers)
        elapsed = time.perf_counter() - start
        for route in routes:
            print(route)
        print(
            f"Evaluated {len(customers)} customer nodes. Generated {len(routes)} routes. Time elapsed {elapsed:.2f}s"
        )


if __name__ == "__main__":
    main()
