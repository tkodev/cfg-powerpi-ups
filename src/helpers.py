import os


def clamp(value, minval, maxval):
    result = sorted((minval, value, maxval))[1]
    return result


def env_var(key, isFloat):
    var_operator = float if isFloat else int
    result = var_operator(os.environ.get(key))
    return result
