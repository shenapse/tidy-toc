import abc


class _Input(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def prompt(self, msg: str = "") -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_input(self):
        raise NotImplementedError
