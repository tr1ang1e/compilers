class Wrapper:
    def __init__(self, filename: str):
        self._wrapper = open(filename, mode="w")
        self.generate_beginning()

    def __del__(self):
        self.generate_ending()
        self._wrapper.close()

    @staticmethod
    def generate_beginning():
        pass

    @staticmethod
    def generate_ending():
        pass
