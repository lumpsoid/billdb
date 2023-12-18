from time import strptime

def is_valid_time(time_string):
    '''
    Check if string is in right format YYYY-MM-DD
    '''
    if time_string is None:
        raise ValueError('time_string is None')
    try:
        strptime(time_string, '%Y-%m-%d')
        return True
    except ValueError:
        raise
        return False
