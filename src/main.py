import argparse
import random
import sys

from yaspin import yaspin

from algorithms.ai_generated_solution import solve_cvrp
from algorithms.inital_solution import solve_clarke_wright
from algorithms.optimised_solution import HGA_Algorithm
from generators.batch_generator import BatchRunGenerator
from generators.data_generator import generate_data_to_csv
from generators.result_generator import save_result
from models.base import InputParams
from models.individual import HGA
from models.output import Output
from models.vrp import Customer
from utils.parser import create_models_from_csv, parse_run

DEFAULT_HGA = HGA(
    minimum_population_size=10,
    max_itterations_without_improvement=50,
    population_scale=4,
    max_local_search=10,
    tournament_size=5,
    rand_seed=1,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CVRP CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a new dataset")
    generate_parser.add_argument("name", help="Dataset name, e.g. sample_1")
    generate_parser.add_argument(
        "-c", "--customers", type=int, default=500, help="Number of customers"
    )
    generate_parser.add_argument(
        "-w", "--weight", type=int, default=10, help="Maximum customer weight"
    )
    generate_parser.add_argument(
        "-s", "--size", type=int, default=250, help="Maximum grid size"
    )

    run_parser = subparsers.add_parser("run", help="Run a dataset with an algorithm")
    run_parser.add_argument("name", help="Dataset name, e.g. sample_1")
    run_parser.add_argument(
        "-a",
        "--algorithm",
        nargs="+",
        choices=["hga", "clarke_wright", "nearest_neighbor"],
        default="hga",
        help="Algorithm to use",
    )
    run_parser.add_argument(
        "-b",
        "--batch",
        type=int,
        default=0,
        help="Run batch mode with N runs (0 = single run)",
    )
    run_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    run_parser.add_argument(
        "--capacity", type=int, default=250, help="Vehicle capacity"
    )
    run_parser.add_argument(
        "--min-pop", type=int, default=DEFAULT_HGA.minimum_population_size
    )
    run_parser.add_argument(
        "--max-no-improve",
        type=int,
        default=DEFAULT_HGA.max_itterations_without_improvement,
    )
    run_parser.add_argument(
        "--pop-scale", type=int, default=DEFAULT_HGA.population_scale
    )
    run_parser.add_argument(
        "--max-local-search", type=int, default=DEFAULT_HGA.max_local_search
    )
    run_parser.add_argument(
        "--tournament-size", type=int, default=DEFAULT_HGA.tournament_size
    )
    run_parser.add_argument("--seed", type=int, default=None)

    show_parser = subparsers.add_parser("show", help="Show a dataset or saved run")
    show_parser.add_argument(
        "type",
        choices=["dataset", "run"],
        help="What to show: dataset or run",
    )
    show_parser.add_argument(
        "name",
        help="Dataset name (e.g. sample_1) or run file name/uuid",
    )
    show_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    return parser


def dataset_path(name: str) -> str:
    return f"./data/{name}.csv"


def runs_path(name: str) -> str:
    if name.endswith(".json"):
        return f"./runs/{name}"
    return f"./runs/{name}.json"


def load_dataset(name: str, capacity: int = 250) -> InputParams:
    path = dataset_path(name)
    _, _, _, customers = create_models_from_csv(path)
    return InputParams(
        customers=customers,
        depot=Customer(0, 0, 0, 0),
        capacity=capacity,
    )


def build_hga_from_args(args) -> HGA:
    seed = args.seed if args.seed is not None else random.randint(0, 10000)
    return HGA(
        minimum_population_size=args.min_pop,
        max_itterations_without_improvement=args.max_no_improve,
        population_scale=args.pop_scale,
        max_local_search=args.max_local_search,
        tournament_size=args.tournament_size,
        rand_seed=seed,
    )


def handle_generate(args) -> None:
    generate_data_to_csv(args.customers, args.weight, args.size, args.name)
    print(f"Generated dataset: {args.name}.csv")


def show_dataset(name: str) -> None:
    path = dataset_path(name)
    amount, max_size, max_weight, customers = create_models_from_csv(path)

    print("*** DATASET SUMMARY")
    print(f"Name: {name}.csv")
    print(f"Customers: {amount}")
    print(f"Max Size: {max_size}")
    print(f"Max Weight: {max_weight}")
    print()

    print("*** CUSTOMERS")
    for customer in customers:
        print(customer)


def show_run(name: str, verbose: bool = False) -> None:
    path = runs_path(name)
    output = parse_run(path)
    print_formatted_output(output, verbose=verbose)


def handle_show(args) -> None:
    if args.type == "dataset":
        show_dataset(args.name)
    elif args.type == "run":
        show_run(args.name, args.verbose)


def run_single(args) -> Output:
    input_params = load_dataset(args.name, args.capacity)
    path = dataset_path(args.name)

    with yaspin(
        text=f"Solving CVRP for {args.name}.csv with {args.algorithm}",
        timer=True,
    ).blue:
        algo = args.algorithm[0]
        if algo == "clarke_wright":
            output = solve_clarke_wright(input_params)
        elif algo == "nearest_neighbor":
            print("HIT")
            output = solve_cvrp(input_params)
        else:
            hga = build_hga_from_args(args)
            output = HGA_Algorithm(hga, input_params)

    output.data_used = path
    return output


def run_batch(args) -> None:
    input_params = load_dataset(args.name, args.capacity)
    path = dataset_path(args.name)

    algorithms = []
    hga_params = None

    for algo in args.algorithm:
        if algo == "hga":
            algorithms.append(HGA_Algorithm)
            hga_params = build_hga_from_args(args)
        elif algo == "clarke_wright":
            algorithms.append(solve_clarke_wright)
        elif algo == "nearest_neighbor":
            algorithms.append(solve_cvrp)

    generator = BatchRunGenerator(
        data_set_path=path,
        amount=args.batch,
        algorithms=algorithms,
        path_name=args.name,
        input_params=input_params,
        hga_params=hga_params,
    )

    with yaspin(
        text=f"Starting batch run... Total of {args.batch * len(algorithms)} runs",
        timer=True,
    ).blue as spinner:
        for progress in generator.generate():
            spinner.text = (
                f"Progress {progress['completed']}/{progress['total']} | "
                f"Current Algorithm: {progress['algorithm']} | "
                f"Last File: {progress['file_name']} | "
                f"Time Elapsed: "
            )

    print(
        f"Batch run complete! Total of {args.batch * len(algorithms)} runs completed."
    )


def handle_run(args) -> None:
    if args.batch > 0:
        run_batch(args)
        return

    output = run_single(args)
    print_formatted_output(output, args.verbose)
    save_result(output, f"./runs/{output.uuid}.json")


def print_formatted_output(output: Output, verbose: bool = False) -> None:
    print("*** SUMMARY")
    print(f"Output path: ./runs/{output.uuid}.json")
    print(f"Algorithm: {output.algorithm_used}")
    print(f"Total Distance: {output.total_distance}")
    print(f"Total Routes: {len(output.routes)}")
    print(f"Memory Usage: {output.memory_usage} MB")
    print(f"Time Taken: {output.time_taken:.3f}s")

    if not verbose:
        return

    print("*** ROUTES")
    for route in output.routes:
        print(route)

    print("*** METADATA")
    print(f"UUID: {output.uuid}")
    print(f"Data Used: {output.data_used}")

    print("*** INPUT PARAMS")
    print(
        f"Customers: {len(output.input_params.customers) if output.input_params else 0}"
    )
    print(f"Depot: {output.input_params.depot if output.input_params else None}")
    print(f"Capacity: {output.input_params.capacity if output.input_params else None}")

    print("*** ADDITIONAL PARAMS")
    if hasattr(output, "additional_params") and isinstance(
        output.additional_params, HGA
    ):
        print(
            f"Minimum Population Size: {output.additional_params.minimum_population_size}"
        )
        print(
            f"Max Iterations Without Improvement: "
            f"{output.additional_params.max_itterations_without_improvement}"
        )
        print(f"Population Scale: {output.additional_params.population_scale}")
        print(f"Max Local Search: {output.additional_params.max_local_search}")
        print(f"Tournament Size: {output.additional_params.tournament_size}")
        print(f"Random Seed: {output.additional_params.rand_seed}")

    print("*** HARDWARE INFO")
    print(f"CPU: {output.hardware_info.cpu_brand}")
    print(f"CPU Cores: {output.hardware_info.cpu_cores}")
    print(f"CPU Bits: {output.hardware_info.cpu_bits}")
    print(f"CPU Architecture: {output.hardware_info.cpu_architecture}")
    print(f"CPU Version: {output.hardware_info.cpu_version}")
    print(f"CPU Hz: {output.hardware_info.hz_friendly}")
    print(f"Platform: {output.hardware_info.platform}")
    print(f"RAM (Virtual): {output.hardware_info.virtual_memory // 1024**3} GB")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        handle_generate(args)
    elif args.command == "run":
        handle_run(args)
    elif args.command == "show":
        handle_show(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
