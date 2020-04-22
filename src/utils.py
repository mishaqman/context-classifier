import csv
import io

def read_text_file(file):
    text = file.read()
    text = text.decode('utf-8', errors='ignore')
    text = text.replace('\r','')
    return text


def read_context_label_csv_file(file):
    retval = {}
    stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
    # stream = io.StringIO(unicode(file.read()), newline=None)
    infile = csv.reader(stream)
    # infile = list(csv.reader(open(file, mode = 'rb', encoding='utf8', errors='ignore'), delimiter = ',', quotechar = '"'))
    for row in infile:
        if row[0] not in retval:
            retval[row[0]] = set()
        retval[row[0]].add(row[1])
    return retval


def float_to_int(n,digits):
    return int(float(n*10**digits))/10**digits