from models import Instagram


def main() -> None:
    ig = Instagram()
    print(ig)
    ig.download()


if __name__ == "__main__":
    main()
