from sii import Sii
from promtypes import Reader

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('eeprom_file')
    args = parser.parse_args()

    f = open(args.eeprom_file, 'rb')
    print(args.eeprom_file)
    print('Info Structure')
    d = Sii()
    d.take(Reader(f))
    print(d)

if __name__ == '__main__':
    main()