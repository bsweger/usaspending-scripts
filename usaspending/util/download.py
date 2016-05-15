import requests, zipfile, os

def download_file(url, filepath):
    '''stream file from url and write to specified location'''
    r = requests.get(url, stream=True)
    if not r.status_code == requests.codes.ok:
        return (False, r.status_code)
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    return (True, filepath)

def unzip_file(zipfilepath, dir):
    '''extract zip to specified directory and clean up extracted filenames'''
    filenames = []
    with zipfile.ZipFile(zipfilepath) as z:
        for name in z.namelist():
            z.extract(name, dir)
            filenames.append(name)
    #remove legacy path junk from unzipped filenames
    for name in filenames:
        newname = name[name.find('\\')+1:]
        os.rename(os.path.join(dir, name), os.path.join(dir, newname))
