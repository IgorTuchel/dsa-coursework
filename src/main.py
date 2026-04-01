import streamlit as st

from data_generator import generate_data_to_csv
from inital_solution import clarke_wright_algo
from parser import create_models_from_csv
from model import Route, Customer

def main():
    print("Hello from dsa-coursework!")
    generate_data_to_csv(500, 9, 250, "sample_3")
    customers = create_models_from_csv("./data/sample_3.csv")
    pairs = clarke_wright_algo(Customer(0,0,0,0), customers)
    
    for route in pairs:
        print(route)
if __name__ == "__main__":
    main()
