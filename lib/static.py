def static(varname, value):
    """
    Decorator shortcut to adding a static variable to a function
    """
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate
