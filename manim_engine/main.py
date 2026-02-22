import sys
from app.application import ManimEngineApp


def main():
    app = ManimEngineApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
