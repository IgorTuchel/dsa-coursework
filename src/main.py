import argparse
import sys

from yaspin import yaspin

from algorithms.inital_solution import solve_clarke_wright
from algorithms.optimised_solution import HGA_Algorithm
from generators.data_generator import generate_data_to_csv
from models.base import InputParams, OutputBase
from models.individual import HGA
from models.vrp import Customer
from utils.parser import create_models_from_csv


def main():

    argParser = argparse.ArgumentParser(
        description="Several proposed implementations of CVRP"
    )
    argParser.add_argument("name", help="Dataset name e.g sample_1 -> sample_1.csv")
    argParser.add_argument(
        "-a",
        "--algorithm",
        choices=["hga", "clarke_wright"],
        default="hga",
        help="Algorithm to use",
    )

    argParser.add_argument(
        "-g", "--generate", action="store_true", help="Generate a new dataset"
    )
    argParser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    argParser.add_argument(
        "-c",
        "--customers",
        type=int,
        default=500,
        help="Number of customers to be generated",
    )
    argParser.add_argument(
        "-w", "--weight", type=int, default=10, help="Maximum weight of a customer"
    )
    argParser.add_argument(
        "-s", "--size", type=int, default=250, help="Maximum grid size of the dataset"
    )

    args = argParser.parse_args()

    if args.generate:
        generate_data_to_csv(args.customers, args.weight, args.size, args.name)
        print(f"Generated Dataset: {args.name}.csv")
        sys.exit(0)

    if args.name:
        path = f"./data/{args.name}.csv"
        amount, max_size, max_weight, customers = create_models_from_csv(path)
        with yaspin(
            text=f"Solving CVRP for {args.name}.csv with {args.algorithm}", timer=True
        ).blue:
            inputParams = InputParams(
                customers=customers,
                depot=Customer(0, 0, 0, 0),
                capacity=250,
            )
            if args.algorithm == "clarke_wright":
                output = solve_clarke_wright(inputParams)
            else:
                hga = HGA(
                    minimum_population_size=10,
                    max_itterations_without_improvement=40,
                    population_scale=4,
                    max_local_search=10,
                    tournament_size=3,
                    input_params=inputParams,
                )
                output = HGA_Algorithm(hga)
            output.data_used = path
        print_formatted_output(output, args.verbose)


def print_formatted_output(output: OutputBase, verbose: bool = False) -> None:
    print()
    print("=== Summary ===")
    print(f"Total Distance: {output.total_distance}")
    print(f"Total Routes: {len(output.routes)}")
    print(f"Memory Usage: {output.memory_usage} MB")
    print(f"Time Taken: {output.time_taken:.3f}s")

    if not verbose:
        return

    print("=== Routes ===")
    for route in output.routes:
        print(route)

    print("=== Metadata ===")
    print(f"UUID: {output.uuid}")
    print(f"Data Used: {output.data_used}")

    print("=== Input Params ===")
    print(f"Customers: {output.input_params.customers}")
    print(f"Depot: {output.input_params.depot}")
    print(f"Capacity: {output.input_params.capacity}")

    print("== Additional Params ===")
    if isinstance(output.additional_params, HGA):
        print(
            f"Minimum Population Size: "
            f"{output.additional_params.minimum_population_size}"
        )
        print(
            f"Max Iterations Without Improvement: "
            f"{output.additional_params.max_itterations_without_improvement}"
        )
        print(f"Population Scale: {output.additional_params.population_scale}")
        print(f"Max Local Search: {output.additional_params.max_local_search}")
        print(f"Tournament Size: {output.additional_params.tournament_size}")

    print("=== Hardware Info ===")
    print(f"CPU: {output.hardware_info.cpu_brand}")
    print(f"CPU Cores: {output.hardware_info.cpu_cores}")
    print(f"CPU Bits: {output.hardware_info.cpu_bits}")
    print(f"CPU Architecture: {output.hardware_info.cpu_architecture}")
    print(f"CPU Version: {output.hardware_info.cpu_version}")
    print(f"CPU Hz: {output.hardware_info.hz_friendly}")
    print(f"Platform: {output.hardware_info.platform}")
    print(f"RAM (Virtual): {output.hardware_info.virtual_memory // 1024**3} GB")


if __name__ == "__main__":
    main()
