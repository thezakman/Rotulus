import argparse
import time
from database import insert_record


def parse_cli():
    parser = argparse.ArgumentParser(
        description='Insert data in Rotulus database')
    parser.add_argument('-f', '--file',
                        metavar='File',
                        required=True,
                        help='One or more files containing email address, password, ...',
                        type=argparse.FileType('rb'),
                        nargs='+')
    parser.add_argument('-s', '--spliter',
                        metavar='Line spliter',
                        required=True,
                        help='Character to split line')

    return parser.parse_args()


def write_errors(errors):
    f_name = "errors_{}.txt".format(time.strftime("%Y%m%d%H%M%S"))
    with open(f_name, "bw") as file:
        for error in errors:
            try:
                file.write(error.encode())
            except:
                try:
                    file.write(error)
                except:
                    print(error)


def main(args):
    errors = []
    ok = 0
    nok = 0
    for file in args.file:
        for line in file:
            try:
                line = line.decode()
            except:
                errors.append(line)
                nok += 1
                continue
            if args.spliter in line:
                try:
                    data = line.split(args.spliter)
                except:
                    errors.append(line)
                    nok += 1
                    continue
                if len(data) == 2:
                    if '@' in data[0]:
                        username = data[0].split('@')[0]
                        domain = data[0].split('@')[1]
                        password = data[1]
                        ok += 1
                    else:
                        errors.append(line)
                        nok += 1
                else:
                    errors.append(line)
                    nok += 1
            else:
                errors.append(line)
                nok += 1
    write_errors(errors)
    print("[+] SUCCESS={} ERROR={}".format(ok, nok))


if __name__ == "__main__":
    main(parse_cli())
