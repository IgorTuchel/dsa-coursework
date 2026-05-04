import os
import random
from typing import Generator


def generate_data_to_csv(
    amount: int, max_weight: int, max_size: int, name: str
) -> None:
    if os.path.exists(f"../data/{name}.csv"):
        raise FileExistsError(
            f"File name {name}.csv already exists at ../data/{name}.csv"
        )

    with open(f"./data/{name}.csv", "w") as f:
        f.write(f"amount={amount}\n")
        f.write(f"max_size={max_size}\n")
        f.write(f"max_weight={max_weight}\n")
        f.write("node,pos_x,pos_y,weight\n")
        for entry in _generate_data(amount, max_weight, max_size):
            e = ",".join(entry) + "\n"
            f.write(e)


def _generate_data(
    amount: int, max_weight: int, max_size: int
) -> Generator[list[str], None, None]:
    for cur_id in range(1, amount + 1):
        pos_x = str(random.randint(-max_size, max_size))
        pos_y = str(random.randint(-max_size, max_size))
        weight = str(random.randint(0, max_weight))
        yield [str(cur_id), pos_x, pos_y, weight]
