import os

class Fstab(file):

    class Entry(object):

        def __init__(self, device, mountpoint, filesystem,
                     options, d=0, p=0):
            self.device = device
            self.mountpoint = mountpoint
            self.filesystem = filesystem

            if not options:
                options = "defaults"

            self.options = options
            self.d = d
            self.p = p

        def __str__(self):
            return "{} {} {} {} {} {}".format(self.device,
                                              self.mountpoint,
                                              self.filesystem,
                                              self.options,
                                              self.d,
                                              self.p)

    _path = os.path.join(os.path.sep, 'etc', 'fstab')

    def __init__(self):
        file.__init__(self, self._path, 'r')

    @property
    def entries(self):
        for line in self.readlines():
            if not line.startswith("#"):
                try:
                    (dev, mp, fs, options, d, p) = line.split(" ")
                    yield Fstab.Entry(dev, mp, fs, options, d=d, p=p)
                except ValueError:
                    pass

    def get_entry_by_attr(self, attr, value):
        for entry in self.entries:
            e_attr = getattr(entry, attr)
            if e_attr == value:
                return entry
        return None
