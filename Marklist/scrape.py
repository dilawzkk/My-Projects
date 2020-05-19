import requests
from bs4 import BeautifulSoup
import re
import csv
import yaml
import sys
from operator import add

# data = urllib.request.urlopen('http://exam.cusat.ac.in/erp5/cusat/Cusat-Home/home_oldresults#').read()
# soup = BeautifulSoup(data, 'html.parser')
# action = soup.find('form', id='myForm0121x56').get('action')
# print(action)
# input_data = {'month':'April', 'year':'2018', 'sem':'8','reg_type':'Regular',
#               'dn':'B.Tech', 'status1':'None'}
#
# r= requests.post(action, data = input_data)
# soup = BeautifulSoup(r.content, 'html.parser')
# action1 = soup.find_all('input')[2].get('formaction')

sub_total = []
failed_tot = []

def print_progressBar(cur_task, tot_task):
    n_bar = 50
    completion = cur_task/tot_task
    sys.stdout.write('\r')
    sys.stdout.write(f"[{'=' * int(n_bar * completion):{n_bar}s}] {int(100 * completion)}%  { 'extracting data'}")
    sys.stdout.flush()


def extract_header(table1, table2):
    row = list()
    for th in table1.find('tr').find_all('th'):
        th = th.get_text()
        row.append(th)
    for tr in table2.find_all('tr'):
        th = tr.find_all('td')[0].get_text()
        if 'CS' in th:
            if 'E' in th:
                th = th[:-2]
            row.append(th)
    row.remove("Degree")
    row.extend(['Total', 'GPA', 'RESULT'])
    return row


def extract_data(table1, table2, soup):
    global sub_total
    global failed_tot
    cur_fails = list()
    data = list()
    for td in table1.find('tr').find_all('td'):
        td = td.get_text()
        data.append(td)
    data.remove('B.Tech')
    trs = table2.find_all('tr')
    trs.pop(0)
    for tr in trs:
        td = tr.find_all('td')[2].get_text()
        data.append(td.strip())
        if 'F' in td.strip():
            cur_fails.append(1)
        else:
            cur_fails.append(0)
    if failed_tot:
        failed_tot = list(map(add, failed_tot, cur_fails))
    else:
        failed_tot = cur_fails

    cur_marks = [int(elem[:-3]) for elem in data[2:]]
    if sub_total:
        sub_total = list(map(add, sub_total, cur_marks))
    else:
        sub_total = cur_marks

    total = soup.body.find(text=re.compile('Total'))
    tot_marks = total.split(":")[1].strip()
    data.append(tot_marks)
    gpa_marks = soup.body.find(text=re.compile('GPA')).split(":")[1].strip()
    if gpa_marks:
        data.append(gpa_marks)
        data.append("PASSED")
    else:
        gpa_marks = 0
        data.append(gpa_marks)
        data.append("FAILED")
    # print("Marksheet data", data)
    # print("Total Subject Marks", sub_total)
    # print("Total Subject Fails", failed_tot)
    return data


try:
    with open(sys.argv[1], 'r') as yl:
        input_config = yaml.load(yl, Loader=yaml.FullLoader)
    output_file = open(input_config['output_file'], 'w')
except:
    print ("failed to read/open input/output file,\n\t pass correct input file if not passed "
           "\n\t close the output file")
    exit()

mwriter = csv.writer(output_file)

sem = input_config['semester']
month = input_config['month']
year = input_config['year']
marklist_url = 'http://exam.cusat.ac.in/erp5/cusat/CUSAT-RESULT/Result_Declaration/display_sup_result'
first = True

# print(input_config['registration_num_sets'])
reg_num_list = list()
for reg_num_set in input_config['registration_num_sets']:
    start = reg_num_set['start_num']
    stop = start + reg_num_set['set_len']
    reg_num_list.extend(range(start, stop))
reg_num_list.sort()
for reg_num in reg_num_list:
    input_data = {"regno": reg_num, "statuscheck": "failed", "deg_name": "B.Tech",
                  "semester": sem, "month": month, "year": year, "result_type": "Regular",
                  "date_time": "2020/03/26 12:38:40.456 GMT+0530", "myText": "ipadress"}
    result_pg = requests.post(marklist_url, data=input_data)
    soup = BeautifulSoup(result_pg.content, 'html.parser')
    table = soup.find_all('table')
    table1 = soup.find('table', attrs={"border": "3"})
    table2 = soup.find('table', attrs={"border": "2"})
    if first:
        header = extract_header(table1, table2)
        mwriter.writerow(header)
        first = False
    data = extract_data(table1, table2, soup)
    mwriter.writerow(data)
    print_progressBar(reg_num_list.index(reg_num), len(reg_num_list)-1)
mwriter.writerow(['Total', ""] + sub_total)
mwriter.writerow(['Subject Fails', ""] + failed_tot)
output_file.close()
print("\noutput file created with extracted data :)")
