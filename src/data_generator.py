import random
import os


def generate_data_to_csv(amount: int, max_weight: int, max_size:int, name:str):
    if os.path.exists(f"../data/{name}.csv"):
        raise FileExistsError(f"File name {name}.csv already exists at ../data/{name}.csv")

    with open(f"./data/{name}.csv", "w") as f:
        f.write("node,pos_x,pos_y,weight\n")
        for cur_id in range(1, amount+1):
            pos_x = random.randint(-max_size, max_size)
            pos_y = random.randint(-max_size, max_size)
            weight = random.randint(0, max_weight)
            entry = ",".join([str(cur_id), str(pos_x), str(pos_y), str(weight)]) + "\n"
            f.write(entry)



