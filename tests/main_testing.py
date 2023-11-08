import logging

if __name__ == "__main__":
    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s -> "
    FMT += "%(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)
