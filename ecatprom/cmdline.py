from . import sii
from . import gui


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='View and edit SII PROM contents')
    parser.add_argument('eeprom_file', nargs='?')
    parser.add_argument('--no-gui', action='store_true',
                        help='Just print the contents to the terminal')
    args = parser.parse_args()

    if args.no_gui:
        if args.eeprom_file:
            print(args.eeprom_file)
            s = sii.from_file(args.eeprom_file)
            print(s)

    else:
        gui.main(args.eeprom_file)


if __name__ == '__main__':
    main()
