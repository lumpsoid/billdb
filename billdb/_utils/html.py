import re

def build_html_table(table_header, data):
    # Generate HTML table dynamically from the list of tuples
    table_content = '<table border="1">'

    table_content += '<tr>'
    for name in table_header:
        table_content += '<th>{}</th>'.format(name)
    table_content += '</tr>'

    for row in data:
        table_content += '<tr>'
        for item in row:
            table_content += '<td>{}</td>'.format(item)
        table_content += '</tr>'
    table_content += '</table>'
    return table_content

def build_html_list(data):
    # Generate HTML list dynamically from the Python list
    list_content = '<ul>'
    for item in data:
        if item is None:
            print(item)
        if re.match(r'http', item):
            list_content += '<li><a href="{}">Link</a></li>'.format(item)
            continue
        list_content += '<li>{}</li>'.format(item)
    # Add a list item with an anchor element at the end of the list
    list_content += '</ul>'
    return list_content
