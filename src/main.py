import sys
import time
from data_generator import generate_data_to_csv
from inital_solution import clarke_wright_algo
from parser import create_models_from_csv
from model import Customer
import argparse


def main():
    argParser = argparse.ArgumentParser(description="Several proposed implementations of COVR")
    argParser.add_argument("name", help="Dataset name e.g sample_1 -> sample_1.csv")
    argParser.add_argument("-g","--generate", action="store_true",help="Generate a new dataset")
    argParser.add_argument("-c","--customers", type=int, default=500)
    argParser.add_argument("-w","--weight", type=int, default=10)
    argParser.add_argument("-s","--size", type=int, default=250)
    
    args = argParser.parse_args()
    
    if args.generate:
        generate_data_to_csv(args.customers, args.weight, args.size, args.name)
        print(f"Generated Dataset: {args.name}.csv")
        sys.exit(0)

    if args.name:
        path = f"./data/{args.name}.csv"
        customers = create_models_from_csv(path)
        start = time.perf_counter()
        routes = clarke_wright_algo(Customer(0,0,0,0), customers)
        elapsed = time.perf_counter() - start
        for route in routes:
            print(route)
        print(f"Evaluated {len(customers)} customer nodes. Generated {len(routes)} routes. Time elapsed {elapsed:.2f}s")

if __name__ == "__main__":
    main()
