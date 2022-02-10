import sii
from basictypes import Reader


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('eeprom_file')
    parser.add_argument('--round-trip', metavar="OUTFILE",
                        help="Load SSI file and then write it back out to this file")
    args = parser.parse_args()

    print(args.eeprom_file)
    s = sii.from_file(args.eeprom_file)
    print(s)
    if args.round_trip:
        print('Writing to', args.round_trip)
        sii.to_file(s, args.round_trip)


if __name__ == '__main__':
    main()
