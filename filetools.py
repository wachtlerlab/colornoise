def readparam(lines, paramname):
    for line in lines:
        if line.startswith(paramname):
            return float(line.split('=')[-1].strip())