
def get_integration_time(filename):
    """get_integration_time
    Calculate the integration time based on values in the header

    :return: integration time
    """
    headers = get_header_values(filename)

    ipbc = float(headers['IPBCdivisor'])
    ict = float(headers['ICTdivisor'])
    return ((ipbc * ict) / 33000000) + 0.00356


def write_final(file_to_write, wavelengths, values):
    with open(file_to_write, 'w') as f:
        for ii in range(0, len(wavelengths)):
            f.write('%3.3f %3.5f\n' % (wavelengths[ii], values[ii]))


def get_header_values(filename):
    """get_header_values
    open the response file and read the header values into a dictionary
    """
    headers = {}

    with open(filename, "r") as infile:
        for line in infile:
            if ">>>>Begin" in line:
                return headers
            else:
                toks = line.rsplit(':')
                if len(toks) > 1:
                    key = toks[0].lstrip('"')
                    value = toks[1].rstrip('"\n')
                    headers[key] = value

    return headers

