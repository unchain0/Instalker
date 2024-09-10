import utils.constants as const
from models.Instagram import Instagram


def main() -> None:
    ig = Instagram(users=const.TARGET_USERS)
    print(ig)
    ig.download()


if __name__ == "__main__":
    main()
