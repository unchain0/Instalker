import utils.constants as const
from models.Instagram import Instagram


def main():
    ig = Instagram(users=const.TARGET_USERS)
    ig.log_in()  # Comment or uncomment this line if you have been blocked
    ig.download()


if __name__ == "__main__":
    main()
