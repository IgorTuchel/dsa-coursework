import json
import random
import uuid

from algorithms.optimised_solution import HGA_Algorithm
from generators.result_generator import save_result
from models.individual import HGA

DEFAULT_HGA = HGA(
    minimum_population_size=10,
    max_itterations_without_improvement=100,
    population_scale=4,
    max_local_search=10,
    tournament_size=3,
    rand_seed=40,
)


class BatchRunGenerator:
    def __init__(
        self,
        data_set_path,
        amount,
        algorithms,
        path_name,
        input_params,
        hga_params=None,
    ):
        self.data_set_path = data_set_path
        self.amount = amount
        self.algorithms = algorithms
        self.path_name = path_name
        self.input_params = input_params
        self.current_index = 0
        self.hga_params = hga_params
        self.batch_uuid = uuid.uuid4().hex
        self.outfiles = {}

    def generate(self):
        total_runs = len(self.algorithms) * self.amount
        completed = 0

        for algorithm in self.algorithms:
            name = algorithm.__name__
            self.outfiles[name] = []

            for _ in range(self.amount):
                if algorithm is HGA_Algorithm:
                    new_rand = random.randint(0, 10000)
                    hga = self.hga_params or DEFAULT_HGA
                    hga.rand_seed = new_rand
                    output = algorithm(hga, self.input_params)
                else:
                    output = algorithm(self.input_params)

                file_name = f"{self.batch_uuid}_{output.uuid}_{self.path_name}.json"
                output.data_used = self.path_name
                path = f"./runs/{file_name}"
                save_result(output, path)

                self.current_index += 1
                completed += 1
                self.outfiles[name].append(output.uuid)

                yield {
                    "completed": completed,
                    "total": total_runs,
                    "algorithm": name,
                    "file_name": file_name,
                }

        self.current_index = 0
        self._generate_batch_output()

    def _generate_batch_output(self):
        batch_output = {
            "batch_uuid": self.batch_uuid,
            "data_set_path": self.data_set_path,
            "path_name": self.path_name,
            "amount": self.amount,
            "algorithms": list(self.outfiles.keys()),
            "outputs": self.outfiles,
        }

        batch_file = f"./runs/{self.batch_uuid}_batch_{self.path_name}_batch.json"
        with open(batch_file, "w") as f:
            json.dump(batch_output, f, indent=2, default=str)

        return batch_output
