from pngchr import TileSet
import sys


def main():
    infile = sys.argv[1]
    outfile = sys.argv[2]
    TileSet(infile).convert_to_chr(outfile)


if __name__ == '__main__':
    main()