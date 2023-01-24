#!/home/qq/Applications/miniconda3/bin/python

bill_text = 'testtesttest'
timestamp = '20220101'
input_values = []
tag_input = input(f'{bill_text}\nTag for this bill?\n>')
# tag_input = input(f'One more?\n1-yes 0-no\n>')
while tag_input != '0':
    input_values.append((timestamp,tag_input,))
    tag_input = input('One more? (0 = exit)\n>')
print(input_values)