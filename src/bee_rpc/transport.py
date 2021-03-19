from bee_util.data.map import Map


class Address():

    def __init__(self, url: str = None, options: Map = {}):
        self.url = url
        self.options = options
