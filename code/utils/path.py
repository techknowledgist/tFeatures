import os, sys, errno, stat, subprocess, gzip, codecs


def read_only(filename):
    """Set permissions on filename to read only."""
    os.chmod(filename, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def make_writable(filename):
    """Make filename writable by owner."""
    os.chmod(filename, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def open_input_file(filename):
    """First checks whether there is a gzipped version of filename, if so, it
    returns a StreamReader instance. Otherwise, filename is a regular
    uncompressed file and a file object is returned."""
    # TODO: generalize this over reading and writing (or create two methods)
    # print "[file.py in open_input_file] filename: %s" % filename
    if os.path.exists(filename + '.gz'):
        # print "file.py: in if, filename: %s" % (filename + '.gz')
        gzipfile = gzip.open(filename + '.gz', 'rb')
        reader = codecs.getreader('utf-8')
        return reader(gzipfile)
    elif os.path.exists(filename):
        # fallback case, possibly needed for older runs
        return codecs.open(filename, encoding='utf-8')
    else: 
        print "[file.py open_input_file] file does not exist: %s" % filename


def open_output_file(fname, compress=True):
    """Return a StreamWriter instance on the gzip file object if compress is
    True, otherwise return a file object."""
    if compress:
        if fname.endswith('.gz'):
            gzipfile = gzip.open(fname, 'wb')
        else:
            gzipfile = gzip.open(fname + '.gz', 'wb')
        writer = codecs.getwriter('utf-8')
        return writer(gzipfile)
    else:
        return codecs.open(fname, 'w', encoding='utf-8')


def ensure_path(path, verbose=False):
    """Make sure path exists."""
    try:
        os.makedirs(path)
        if verbose:
            print "[ensure_path] created %s" % path
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_file_specifications(filename, start=0, limit=500):
    """Return a list with n=limit file specifications from filename, starting
    from line n=start. This function will return less than n=limit files if
    their were less than n=limit lines left in filename, it will return an empty
    list if start is larger than the number of lines in the file."""
    current_count = start
    fh = open(filename)
    line_number = 0
    while line_number < current_count:
        fh.readline(),
        line_number += 1
    lines_read = 0
    fspecs = []
    while lines_read < limit:
        line = fh.readline().strip()
        if line == '':
            break
        fspec = FileSpec(line)
        fspecs.append(fspec)
        lines_read += 1
    fh.close()
    return fspecs


def get_file_paths(source_path):
    """Return a list with all filenames in source_path."""
    file_paths = []
    for (root, dirs, files) in os.walk(source_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def create_file(filename, content=None):
    """Create a file with name filename and write content to it if any was given."""
    fh = open(filename, 'w')
    if content is not None:
        fh.write(content)
    fh.close()


# CHECK: used in batch
def XXXfilename_generator(path, filelist):
    """Creates generator on the filelist, yielding the concatenation of the path
    and a path in filelist."""
    fh = open(filelist)
    for line in fh:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        fspec = FileSpec(line)
        yield os.path.join(path, 'files', fspec.target)
    fh.close()


def compress(*fnames):
    """Compress all filenames fname in *fnames using gzip. Checks first if the
    file was already compressed."""
    for fname in fnames:
        if fname.endswith(".gz"):
            continue
        if os.path.exists(fname + '.gz'):
            continue
        subprocess.call(['gzip', fname])


def uncompress(*fnames):
    """Uncompress all files fname in *fnames using gunzip. The fname argument
    does not include the .gz extension, it is added by this function. If a file
    fname already exists, the function will not attempt to uncompress."""
    for fname in fnames:
        if not os.path.exists(fname):
            subprocess.call(['gunzip', fname + '.gz'])


class FileSpec(object):

    """A FileSpec is created from a line from a file that specifies the
    sources. Such a file has two mandatory columns: year and source_file. These
    fill the year and source instance variables in the FileSpec. The target
    instance variable is by default the same as the source, but can be overruled
    if there is a third column in the file. Example input lines:

       1980    /data/patents/xml/us/1980/12.xml   1980/12.xml
       1980    /data/patents/xml/us/1980/13.xml   1980/13.xml
       1980    /data/patents/xml/us/1980/14.xml
       0000    /data/patents/xml/us/1980/15.xml

    FileSpec can also be created from a line with just one field, in that case
    the year and source are set to None and the target to the only field. This
    is typically used for files that simply list filenames for testing or
    training.
    """

    def __init__(self, line):
        fields = line.strip().split("\t")
        if len(fields) > 1:
            self.year = fields[0]
            self.source = fields[1]
            self.target = fields[2] if len(fields) > 2 else fields[1]
        else:
            self.year = None
            self.source = None
            self.target = fields[0]
        self._strip_slashes()

    def __str__(self):
        return "<%s %s %s>" % (self.year, self.source, self.target)

    def _strip_slashes(self):
        if self.target.startswith(os.sep):
            self.target = self.target[1:]