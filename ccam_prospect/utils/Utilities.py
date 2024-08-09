from jinja2 import Environment, FileSystemLoader
import os
from datetime import date
from ccam_prospect.utils.CustomExceptions import NonStandardHeaderException
from pds4_tools import pds4_read

def get_integration_time(filename):
    """get_integration_time
    Calculate the integration time based on values in the header

    :param: filename the name of the file to read
    :return: integration time
    """
    headers = get_header_values(filename)

    try:
        ipbc = float(headers['IPBCdivisor'])
        ict = float(headers['ICTdivisor'])
        return ((ipbc * ict) / 33000000) + 0.00356
    except KeyError:
        raise NonStandardHeaderException
        return None


def write_final(file_to_write, wavelengths, values, header=None):
    """write_final
    given the file to write to, the wavelengths, and the values, write them to file in a 2-column table

    :param: file_to_write the path to the final file
    :param: wavelenghts the values of the wavelengths, the first column
    :param: values the calibrated values, the second column
    """
    with open(file_to_write, 'w') as f:
        if header is not None:
            [f.write(header[ii].replace("\n", "\r\n")) for ii in range(0, len(header))]
        n = len(wavelengths)
        [f.write("{:10.3f}{:20f}            \r\n".format(wavelengths[ii], values[ii])) for ii in range(0, n)]


def get_context(label_path, psv_label):
    """get_context
    given the old label, get some values and create a context to fill in the PDS4 label template

    :param: label_path the path to the new label
    :param: psv_label the path to the old label for the PSV file
    :return: the context for creating the new label from template
    """
    # get filename with and without extension
    path, filename = os.path.split(label_path)
    filename_no_ext = os.path.splitext(filename)[0]
    filename_no_ext = filename_no_ext.lower()

    # get today's date as creation date
    today = date.today()
    creation_date = today.strftime("%Y-%m-%d")

    # get observation start time
    start_time = "UNK" # just in case

    # psv data file name = psv label name but with .tab
    path, psv_label_name = os.path.split(psv_label)
    psv_label_type = os.path.splitext(psv_label_name)[1]
    if psv_label_type.lower() == "lbl":
        psv_filename = psv_label_name.replace("LBL", "TAB")
        psv_filename = psv_filename.replace("lbl", "tab")

        with open(psv_label) as psv:
            for i, line in enumerate(psv):
                line_parts = line.split("=")
                if line_parts[0].strip() == "START_TIME":
                    start_time = line_parts[1].strip()
                if i > 56:
                    break

    elif psv_label_type.lower() == "xml":
        psv_filename = psv_label_name.replace("XML", "TAB")
        psv_filename = psv_filename.replace("xml", "tab")

        structures = pds4_read(psv_label)
        label = structures.label
        obs_area = label.find("Observation_Area")
        time = obs_area.find('Time_Coordinates')
        start_time = time.findtext('start_date_time')
    else:
        psv_filename = "UNK" # TODO this should never happen?

    context = {
        "filename": filename_no_ext,
        "psv_filename": psv_filename,
        "creation_date": creation_date,
        "observation_start": start_time
    }
    return context


def write_label(label_path, psv_label, is_rad):
    """write_label
    given the path to the new label and some information from the psv label,
    write a PDS4 label from the provided template
    """
    # get context to fill in template
    context = get_context(label_path, psv_label)

    # set up template environment and choose the appropriate template
    my_path = os.path.abspath(os.path.dirname(__file__))
    templates = os.path.join(my_path, "../templates")
    template_loader = FileSystemLoader(searchpath=templates)
    template_env = Environment(loader=template_loader)
    if is_rad:
        template_file = "rad_template.xml"
    else:
        template_file = "ref_template.xml"
    template = template_env.get_template(template_file)

    # write the label
    with open(label_path, 'w') as label:
        label.write(template.render(context))


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
                parts = line.rsplit(':')
                if len(parts) > 1:
                    key = parts[0].lstrip('"')
                    value = parts[1].rstrip('"\n')
                    headers[key] = value

    return headers

