from jinja2 import Environment, FileSystemLoader
import os

def get_integration_time(filename):
    """get_integration_time
    Calculate the integration time based on values in the header

    :return: integration time
    """
    headers = get_header_values(filename)

    try:
        ipbc = float(headers['IPBCdivisor'])
        ict = float(headers['ICTdivisor'])
        return ((ipbc * ict) / 33000000) + 0.00356
    except KeyError:
        print('Header not formatted correctly in file {}. Unable to calculate exposure time.'.format(filename))
        return None


def write_final(file_to_write, wavelengths, values, header=None):
    with open(file_to_write, 'w') as f:
        if header is not None:
            [f.write(header[ii]) for ii in range(0, len(header))]
        [f.write("   {:3.3f}      {:>10f}                \r\n".format(wavelengths[ii], values[ii])) for ii in range(0, len(wavelengths))]


def write_label(label_path, is_rad):
    template_loader = FileSystemLoader(searchpath="/Users/osheacm1/Documents/SAA/PDART/")
    template_env = Environment(loader=template_loader)
    if is_rad:
        template_file = "rad_template.xml"
    else:
        template_file = "ref_template.xml"
    template = template_env.get_template(template_file)

    path, filename = os.path.split(label_path)
    filename_no_ext = os.path.splitext(filename)[0]

    with open(label_path, 'w') as f:
        context = {
            "filename": filename_no_ext,
            "filename_ext": filename,
            "psv_filename": "psv_filename",
            "creation_date": "2020.02.04", # TODO get todays date
            "observation_start": "1900.02.04Z", # TODO get start and stop dates
            "observation_stop": "1280918Z"
        }
        f.write(template.render(context))



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

