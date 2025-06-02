"""
Custom exceptions to raise during the exeuction of this app's code.
"""


class PdfGenFailed(Exception):
    """
    Generating a PDF failed for some reason.
    """

    ...


class PdfSaveFail(Exception):
    """
    Something weng wring while saving PDF data.
    """

    ...


class GsheetsReadErr(Exception):
    """
    Reading data from google sheets API failed.
    """

    ...


class GsheetsWriteErr(Exception):
    """
    Writing data to google sheets using their API failed.
    """

    ...


class ClientDoesNotExist(Exception):
    """
    An operation was attempted for a client that doesn't exist in the current configuration.
    """

    def __init__(self, clientname: str, *args, **kwargs) -> None:
        self.clientname = clientname
        super().__init__(clientname, *args, **kwargs)


class SenderProfileDoesNotExist(Exception):
    """
    The sender profile doesn't exist.
    """

    def __init__(self, profilename: str, *args, **kwargs) -> None:
        self.profilename = profilename
        super().__init__(profilename, *args, **kwargs)
