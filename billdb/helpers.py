from time import strptime

def is_valid_time(time_string):
    '''
    Check if string is in right format YYYY-MM-DD
    '''
    try:
        strptime(time_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False
