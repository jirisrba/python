import re
import sys

def read_patterns(file_name):
    regexp = ''
    with open(file_name, 'r') as patterns_file:
        for line in patterns_file:
            line = line.rstrip('\r\n')
            if not re.match('(^\s*#.*)|(^$)', line):
                regexp_elems = line.split(' ')
                if len(regexp_elems) > 1 :
                    regexp = regexp + '|(.*{}\s+.*{}((\s|;)+.*))'.format(regexp_elems[0], regexp_elems[1])
                else:
                    regexp = regexp + '|(.*{}((\s|;)+.*))'.format(regexp_elems[0])
    
    if len(regexp) > 1:
        regexp = regexp[1:]
    
    return regexp

def filter_sql(file_name, regexp):
    regexp_program = re.compile(regexp, re.IGNORECASE)
    comments_program = re.compile('(^\s*--.*)|(^\s*//.*)')
    
    with open(file_name, 'r') as sql_file:
        for line in sql_file:
            line = line.rstrip('\r\n')
            if not comments_program.match(line):
                if regexp_program.match(line):
                    raise Exception('SQL Security: {}'.format(line))

if __name__ == '__main__':    
    patts = read_patterns('patterns.txt')
    filter_sql(sys.argv[1], patts)