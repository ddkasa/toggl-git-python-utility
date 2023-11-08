import logging

APP_NAME = "Python, Git & TGGL Tracker Utility"



if __name__ == "__main__":
    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s -> "
    FMT += "%(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)

    logging.info(APP_NAME.upper())