from pip import main
from os import getcwd

with open("requirements.txt") as f:
    for package in f.read().split("\n"):
        main(["install", "--target", getcwd(), package])