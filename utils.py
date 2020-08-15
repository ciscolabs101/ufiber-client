def pythonize(json):
    '''
    Helper function to process JSON structures with invalid Python data types
    Replaces - to _
    Replaces true/false to proper bools
    '''
    # Replace - for _
    cleaned_data = {}
    for key, value in json.items():
        cleaned_data[key.replace('-', '_')] = value
    # Replace 'bool' values
    for key, value in cleaned_data.items():
        if value == 'true':
            cleaned_data[key] = True
        if value == 'false':
            cleaned_data[key] = False
    return cleaned_data
