
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
            [f.write('"' + header[ii].rstrip('\n') + '"\n') for ii in range(0, len(header))]
        [f.write('%3.3f %3.5f\n' % (wavelengths[ii], values[ii])) for ii in range(0, len(wavelengths))]


def write_label(original_label, new_label, is_rad):
    if is_rad:
        file_type = "RAD"
    else:
        file_type = "REF"

    original_id = ""
    with open(original_label, 'r') as og:
        with open(new_label, 'w') as new_file:
            for i, line in enumerate(og):
                if i == 10:
                    if is_rad:
                        new_line = line.replace("PSV", file_type)
                    else:
                        continue  # skip the 11th line which describes a header since there is no header for REF
                elif i == 11 or i == 17:
                    new_line = line.replace("PSV", file_type)
                    if i == 11:
                        new_line = new_line.replace("30)", "1)")
                elif i == 39:
                    parts = line.split("=")
                    original_id = parts[1].strip()
                    new_line = line.replace("PSV", file_type)
                elif i == 43:
                    parts = line.split("=")
                    new_line = parts[0] + "= " + original_id + "\n"
                # skip 310 through 320 for REF.  For RAD, replace PSV with RAD
                elif 309 < i < 321:
                    if is_rad:
                        new_line = line.replace("PSV", file_type)
                    else:
                        continue
                elif i == 326:
                    new_line = line.replace("1", "2")
                elif i == 327:
                    new_line = line.replace("44", "88")  #TODO how many bytes now?
                elif i == 329:
                    new_line = line.replace("PSV", file_type)
                elif i == 331:
                    if is_rad:
                        units_string = "calibrated to units of radiance (W/m^2/sr/um)\""
                    else:
                        units_string = "calibrated to units of relative reflectance\""
                    new_line = line.replace("in DN units. Companion wavelength file is CCAM_DEFAULT_WAVE.TAB.\"",
                                            units_string)
                elif 332 < i < 346:
                    continue
                else:
                    new_line = line

                new_file.write(new_line)

            if is_rad:
                unit = "RADIANCE"
                description = "Calibrated Radiance"
            else:
                unit = "RELATIVE REFLECTANCE"
                description = "Relative Reflectance"
            # write the last chunk about the columns
            final_string = "" \
"  OBJECT                          = COLUMN 1\n\
    NAME                         = \"WAVELENGTH\"\n\
    DATA_TYPE                    = ASCII_REAL\n\
    START_BYTE                   = 1\n\
    BYTES                        = 42\n\
    UNIT                         = \"WAVELENGTH\" \n\
    DESCRIPTION                  = \"Wavelengths from CCAM_DEFAULT_WAVE.TAB\" \n\
  END_OBJECT                     = COLUMN \n\
 \n\
  OBJECT                          = COLUMN 2 \n\
    NAME                          = \"CHANNEL_INTENSITY\" \n\
    DATA_TYPE                     = ASCII_REAL \n\
    START_BYTE                    = 1 \n\
    BYTES                         = 42 \n\
    UNIT                          = \"" + unit + "\"\n\
    DESCRIPTION                   = \"" + description + "\" \n\
  END_OBJECT                      = COLUMN \n\
 \n\
 END_OBJECT                        = TABLE \n\
 \n\
END"
            new_file.write(final_string)


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

