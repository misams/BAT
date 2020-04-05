# define user exceptions
class Error(Exception):
    """ Base class for other exceptions """
    pass

class InputCofError(Error):
    """ Error exception for invalid Bolt-CoF input in input file """
    pass

class InputCheckParameterMissing(Error):
    """ during check of processed input file a required parameter is missing - check input file """
    pass