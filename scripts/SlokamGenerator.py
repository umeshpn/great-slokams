#!/usr/bin/python3

from indexkeygenerator import IndexKeyGenerator

import datetime
import os
import re
import sys

slokam_re = re.compile('^\\\\begin\{slokam\}\{(.+)\}\{(.+)\}\{(.+)\}(.*)')
slokam_end_re = re.compile('^\\\\end\{slokam\}(.*)')
letter_re = re.compile('^\\\\Letter\{([^}]+)\}\{([^}]+)\}(.*)')
book_re = re.compile('^\\\\Book\{([^}]+)\}(.*)')
topic_re = re.compile('^\\\\Topic\{([^}]+)\}(.*)')
line_re = re.compile('\\\\\\\\\s*$')

var_re = re.compile('\\\\(\S+)')
people_re = re.compile('^\\\\newcommand\{\\\\(\S+)\}\{(.+)\}')
meter_re = re.compile('^\\\\newcommand\{\\\\(\S+)\}\{\\\\Vruththam\{(.+)\}\}')

char_map = {
    "\u0d30\u0d4d\u200d" : "\u0d7c",
    "\u0d32\u0d4d\u200d" : "\u0d7d",
    "\u0d28\u0d4d\u200d" : "\u0d7b",
    "\u0d23\u0d4d\u200d" : "\u0d7a",
    "\u0d33\u0d4d\u200d" : "\u0d7e",
    "\u0d4c" : "\u0d57",
    "\u0d7b\u0d4d\u0d31" : "\u0d28\u0d4d\u0d31",
    "\\prash{}" : "\u0d3d" 
}

months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class SlokamGenerator:
    """Generates modified LaTeX files and an HTML file from input LaTeX source."""

    def __init__(self):
        self.in_file = None
        self.out_latex = None
        self.out_html = None
        self.out_stat = None
        self.out_slok_count = None
        self.meter_map = {}
        self.poet_map = {}
        self.meter_count_map = {}
        self.poet_count_map = {}
        self.unknown_poet_count = 0
        self.unknown_meter_count = 0
        self.n_slokams = 0
        self.n_mal_slokams = 0
        self.n_san_slokams = 0
        self.index_key_generator = IndexKeyGenerator()
        self.first_letter_map = {}
        self.third_letter_map = {}
        self.first_third_letter_map = {}
        self.both_first_and_thirds = set()
        self.first_part_map = {}

    # def finish(self):
    #     self.out_html.close()
    #     self.out_stat.close()
    #     self.out_slok_count.close()


    def read_people(self, people_file_name):
        with open(people_file_name) as p:
            line = p.readline()
            while line:
                m = people_re.match(line)
                if m:
                    self.poet_map[m.group(1)] = m.group(2)
                line = p.readline()

    def read_meter(self, meter_file_name):
        with open(meter_file_name) as p:
            line = p.readline()
            while line:
                m = meter_re.match(line)
                if m:
                    self.meter_map[m.group(1)] = m.group(2)
                line = p.readline()

    def real_name(self, name):
        m = var_re.match(name)
        if m:
            return self.poet_map[m.group(1)]
        else:
            return name

    def real_meter(self, name):
        m = var_re.match(name)
        if m:
            return self.meter_map[m.group(1)]
        else:
            return name

    def parseAndGenerate(self, input_latex_file_name, output_latex_file_name, html_title):
        """Reads input_file_name and writes output to output_latex_file and self.out_html"""

        self.in_file = open(input_latex_file_name, "r")
        self.out_latex = open(output_latex_file_name, "w")

        self.out_html.write('<h2>%s</h2>\n' % html_title)
        self.out_html.write('<ol>\n')

        slokam_count = 0

        line = self.in_file.readline()

        in_slokam = False
        line_no = 0
        next_slokam = True
        while line:
            line_no += 1
            line = line.strip()

            for f, t in char_map.items():
                line = line.replace(f, t)

            m = slokam_re.match(line)
            if m:
                if in_slokam:
                    print("End slokam missing on line %d in file %s\n" % (line_no, input_latex_file_name))
                    sys.exit(1)
                in_slokam = True
                next_slokam = False
                slokam_count += 1
                line_count = 0
                meter, poet, first_part, rest = m.group(1), m.group(2), m.group(3), m.group(4)

                if first_part in self.first_part_map:
                    print('The slokam "%s..." is on lines %d and %d' % (first_part, self.first_part_map[first_part], line_no))
                    sys.exit(1)
                else:
                    self.first_part_map[first_part] = line_no

 
                if meter == '\\VOth':
                    self.unknown_meter_count += 1
                    meter = self.real_meter(meter)
                else:
                    meter = self.real_meter(meter)
                    self.meter_count_map[meter] = self.meter_count_map.get(meter, 0) + 1

                if poet == '\\Unk':
                    self.unknown_poet_count += 1
                    poet = self.real_name(poet)
                else:
                    poet = self.real_name(poet)
                    self.poet_count_map[poet] = self.poet_count_map.get(poet, 0) + 1

                poet_index = self.index_key_generator.generate(poet)
                meter_index = self.index_key_generator.generate(meter)
                first_part_index = self.index_key_generator.generate(first_part)


                self.out_latex.write('\\begin{IndexedSlokam}{%s}{%s}{%s}{%s}{%s}{%s}%s\n' 
                                     % (meter, meter_index, poet, poet_index, first_part, first_part_index, rest))

                # Print HML.
                self.out_html.write('\n  <li><font color="red">[%s]</font> <font color="darkgreen">(%s)</font><p>\n' % (meter, poet))
                self.out_html.write('  <font color="blue">')

                line = self.in_file.readline()
                continue

            m = line_re.search(line)
            if m:
                if next_slokam:
                    print("Line out of place on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()
                line_count += 1
                if line_count > 3:
                    print("Too many lines on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()
                if not in_slokam:
                    print("Line out of place on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()

                self.out_latex.write('%s\n' % line)

                line = line.replace('\\\\', '')
                line = re.sub(r'\\sam\{(.+)\}', r'\1', line)
                line = re.sub(r'\\samd\{(.+)\}\{.+\}', r'\1', line)
                self.out_html.write('    %s<br>\n' % line)

                line = self.in_file.readline()
                continue


            m = slokam_end_re.match(line)
            if m:
                if not in_slokam:
                    print("Start slokam missing on line %d in file %s\n" % (line_no, input_latex_file_name))
                    sys.exit(1)
                self.out_latex.write('\\end{IndexedSlokam}%s\n' % m.group(1))

                self.out_html.write('  </font>\n')
                self.out_html.write('  <p>\n')
                in_slokam = False
                next_letter = True

                if line_count != 3:
                    print("Not enough lines on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()
                line_count = 0
                line = self.in_file.readline()
                continue

            m = letter_re.match(line)
            if m:
                first, third, rest = m.group(1), m.group(2), m.group(3)
                if line_count != 0 or not next_letter:
                    print("Letter out of place on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()

                self.out_latex.write('\\IndexedLetter{%s}{%s}{%s}{%s}%s\n' % (
                    first, self.index_key_generator.generate(first),
                    third, self.index_key_generator.generate(third),
                    rest
                ))

                if first in self.first_letter_map:
                    self.first_letter_map[first] += 1
                else:
                    self.first_letter_map[first] = 1

                if third in self.third_letter_map:
                    self.third_letter_map[third] += 1
                else:
                    self.third_letter_map[third] = 1

                first_third = '%s $\Rightarrow$ %s' % (first, third)
                if first_third in self.first_third_letter_map:
                    self.first_third_letter_map[first_third] += 1
                else:
                    self.first_third_letter_map[first_third] = 1

                next_letter = False
                next_slokam = True
                line = self.in_file.readline()
                continue

            m = book_re.match(line)
            if m:
                book, rest = m.group(1), m.group(2)
                if line_count != 0:
                    print("Book out of place on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()
                if not next_slokam:
                    print("Book out of place on %d in %s" % (line_no, input_latex_file_name))
                    sys.exit()

                self.out_latex.write('\\IndexedBook{%s}{%s}%s\n' % (
                    book, self.index_key_generator.generate(book), rest
                ))

                self.out_html.write('കൃതി: %s<br>\n' % book) 
                line = self.in_file.readline()
                continue


            m = topic_re.match(line)
            if m:
                topic, rest = m.group(1), m.group(2)
                self.out_latex.write('\\IndexedTopic{%s}{%s}%s\n' % (
                    topic, self.index_key_generator.generate(topic), rest
                ))
                line = self.in_file.readline()
                continue

            self.out_latex.write('%s\n' % line)
            if in_slokam:
                line = re.sub(r'\\sam\{(.+)\}', r'\1', line)
                line = re.sub(r'\\samd\{(.+)\}\{.+\}', r'\1', line)
                self.out_html.write('    %s<br>\n' % line)


            # Read next line.
            line = self.in_file.readline()

        firsts = set(self.first_letter_map.keys())
        thirds = set(self.third_letter_map.keys())
        self.both_first_and_thirds = firsts & thirds

        self.in_file.close()
        self.out_latex.close()
        self.out_html.write('</ol>\n')
        return slokam_count

    def printSlokCounts(self, f, slok_count_f):
        f.write('\\begin{center}\n')
        f.write('\\begin{tabular}{rcr}\n')
        f.write('\\TotalSlokams & = & %d\\\\\n' % self.n_slokams)
        f.write('\\MalSlokams & = & %d \\\\\n' % self.n_mal_slokams)
        f.write('\\SanSlokams & = & %d \\\\\n' % self.n_san_slokams)
        f.write('\\end{tabular}\n')
        f.write('\\end{center}\n\n\n')

        slok_count_f.write('\\newcommand{\\NTotalSlokams}{%d}\n' % self.n_slokams)
        slok_count_f.write('\\newcommand{\\NMalSlokams}{%d}\n' % self.n_mal_slokams)
        slok_count_f.write('\\newcommand{\\NSanSlokams}{%d}\n' % self.n_san_slokams)

    def printMeterStats(self, f):
        # Meters
        self.printTableHeader("\\vruththam", f);
        sr_no = 0
        total_meter_count = 0
        for meter in sorted(self.meter_count_map, key=lambda x: (-self.meter_count_map[x], x)):
            sr_no += 1
            count = self.meter_count_map[meter]
            f.write('%d & %s & $%d$ & ($%.1f$ \\%%)\\\\\n' % (sr_no, meter, count, count * 100.0 / self.n_slokams))
            total_meter_count += count
        f.write(' & & & \\\\\n')
        f.write(' & %s & $%d$ & ($%.1f$ \\%%)\\\\\n' % (
            '\\VOth', self.unknown_meter_count, self.unknown_meter_count * 100.0 / self.n_slokams))
        f.write('\\hline\n')
        f.write(' & \\textbf{%s} & $\\mathbf{%d}$ & \\\\\n' % ('\\TotalCount', total_meter_count + self.unknown_meter_count))

        self.printTableFooter("\\vruththams", f);

        # Poets

    def printTableHeader(self, heading, f):
        f.write('\\begin{table}[H]\n')
        f.write('\\centering\n')
        f.write('\\begin{tabular}{|r|l|rr|}\n')
        f.write('\\hline')
        f.write('\\textbf{\\#} & \\textbf{%s} & \\textbf{\\ennam} & \\textbf{(\\%%)} \\\\\n' % heading)
        f.write('\\hline\n')

    def printTableFooter(self, caption, f):
        f.write('\\hline\n')
        f.write('\\end{tabular}\n')
        f.write('\\caption{%s}\n' % caption)
        f.write('\\end{table}\n')

    def set_out_html_file(self, html_file_name):
        self.out_html = open(html_file_name, 'w')
        self.print_html_header(self.out_html)

    def set_stat_file(self, stat_file_name):
        self.out_stat = open(stat_file_name, 'w')

    def set_slok_count_file(self, slok_count_file_name):
        self.out_slok_count = open(slok_count_file_name, 'w')

    def finish(self):
        self.print_html_footer(self.out_html)
        self.out_html.close()
        self.out_stat.close()
        self.out_slok_count.close()

    def generate(self, in_dir):
        in_mal_file_name = '%s/%s' % (in_dir, 'great-slokams-mal.tex')
        out_mal_file_name = '%s/%s' % (in_dir, 'great-slokams-mal-tex.tex')

        in_san_file_name = '%s/%s' % (in_dir, 'great-slokams-san.tex')
        out_san_file_name = '%s/%s' % (in_dir, 'great-slokams-san-tex.tex')

        # self.read_count('%s/%s' % (in_dir, 'slokam-count.tex'))
        self.read_people('%s/%s' % (in_dir, 'people.tex'))
        self.read_meter('%s/%s' % (in_dir, 'meter-decl.tex'))

        # print(self.poet_map)
        self.set_out_html_file('%s/%s' % (in_dir, 'great-slokams.html'))
        self.set_stat_file('%s/%s' % (in_dir, 'stats.tex'))
        self.set_slok_count_file('%s/%s' % (in_dir, 'slokam-count.tex'))

        self.n_mal_slokams = self.parseAndGenerate(in_mal_file_name, out_mal_file_name, 'Malayalam')
        self.n_san_slokams = self.parseAndGenerate(in_san_file_name, out_san_file_name, 'Sanskrit')
        self.n_slokams = self.n_mal_slokams + self.n_san_slokams

        self.printSlokCounts(self.out_stat, self.out_slok_count)
        self.printMeterStats(self.out_stat)
        self.printPoetStats(self.out_stat)
        self.printLetterStats(self.out_stat)
        self.printMeterComboStats(self.out_stat)

        self.finish()

    def printLetterStats(self, f):
        f.write('\n\n\\begin{table}[H]\n')
        f.write('\\centering\n')
        f.write('\\begin{tabular}{|c|c|}\n')
        f.write('\\hline\n')
        f.write('\\textbf{\\FirstLine} & \\textbf{\\ThirdLine} \\\\\n')
        f.write('\\hline\n')
        f.write('\\begin{tabular}{r|c|rr}')
        f.write('\\textbf{\#} & \\textbf{\\aksharam} & \\textbf{\\ennam} & \\textbf{(\%)}\\\\\n')
        f.write('\\hline\n')
        line_no = 0
        sr_no = 0
        total_first_count = 0
        for letter in sorted(self.first_letter_map, key=lambda x : (-self.first_letter_map[x], x)):
            sr_no += 1
            count = self.first_letter_map[letter]
            total_first_count += count
            if letter in self.both_first_and_thirds:
                f.write('%d & %s & $%d$ & ($%5.1f$ \\%%)\\\\\n' % (sr_no, letter, count, count * 100.0 / self.n_slokams))
            else:
                f.write('%d & \\textbf{*%s} & $%d$ & ($%5.1f$ \\%%)\\\\\n' % (sr_no, letter, count, count * 100.0 / self.n_slokams))
            line_no += 1

        f.write('\\hline\n')
        f.write(' & \\textbf{%s} & $\\mathbf{%d}$ & \\\\\n' % ( '\\TotalCount', total_first_count))
        f.write('\\end{tabular}\n')
        f.write('&\n')
        f.write('\\begin{tabular}{r|c|rr}\n')
        f.write('\\textbf{\#} & \\textbf{\\aksharam} & \\textbf{\\ennam} & \\textbf{(\%)}\\\\\n')
        f.write('\\hline\n')

        sr_no = 0
        total_third_count = 0
        for letter in sorted(self.third_letter_map, key=lambda x : (-self.third_letter_map[x], x)):
            sr_no += 1
            count = self.third_letter_map[letter]
            total_third_count += count
            if letter in self.both_first_and_thirds:
                f.write('%d & %s & $%d$ & ($%5.1f$ \\%%)\\\\\n' % (sr_no, letter, count, count * 100.0 / self.n_slokams))
            else:
                f.write('%d & \\textbf{*%s} & $%d$ & ($%5.1f$ \\%%)\\\\\n' % (sr_no, letter, count, count * 100.0 / self.n_slokams))
            line_no -= 1
        while line_no > 0:
            f.write(' & & \\\\\n')
            line_no -= 1

        f.write('\\hline\n')
        f.write(' & \\textbf{%s} & $\\mathbf{%d}$ & \\\\\n' % ( '\\TotalCount', total_third_count))
        f.write('\\end{tabular}\\\\\n')
        f.write('\\hline\n')
        f.write('\\end{tabular}\n')
        f.write('\\caption{\\Letters}\n')
        f.write('\\end{table} \n\n')


    def printMeterComboStats(self, f):
        line_no = 0
        page_no = 0
        sr_no = 0
        total_order_count = 0
        for letter in sorted(self.first_third_letter_map, key=lambda x : (-self.first_third_letter_map[x], x)):
            sr_no += 1
            if line_no == 0:
                page_no += 1
                f.write('\\begin{table}[H]\n')
                f.write('\\centering\n')
                f.write('\\begin{tabular}{|r|c|rr|}\n')
                f.write('\\hline\n')
                f.write('\\textbf{\#} & \\textbf{\\kramam} & \\textbf{\\ennam} & \\textbf{(\%)} \\\\\n')
                f.write('\\hline\n')

            count = self.first_third_letter_map[letter]
            total_order_count += count
            f.write('%d & %s & $%d$ & ($%5.1f$ \\%%)\\\\\n' % (sr_no, letter, count, count * 100.0 / self.n_slokams))
            line_no += 1

            if line_no == 40:
                f.write('\\hline\n')
                f.write('\\end{tabular}')
                if page_no == 1:
                    f.write('\\caption{\\aksharakramam}\n')
                else:
                    f.write('\\caption{\\aksharakramam{} (Contd...)}\n')
                f.write('\\end{table}\n')

                line_no = 0

        if line_no > 0:
            f.write('\\hline')
            f.write(' & \\textbf{%s} & $\\mathbf{%d}$ & \\\\\n' % ( '\\TotalCount', total_order_count))
            f.write('\\hline\n')
            f.write('\\end{tabular}\n')
            f.write('\\caption{\\aksharakramam{} (Contd...)}\n')
            f.write('\\end{table}\n')


    def printPoetStats(self, f):
        sr_no = 0
        total_poet_count = 0
        line_no = 0
        first = True
        for poet in sorted(self.poet_count_map, key=lambda x: (-self.poet_count_map[x], x)):
            sr_no += 1
            line_no += 1
            if line_no == 1:
                self.printTableHeader("\\kavi", f);
            count = self.poet_count_map[poet]
            f.write('%d & %s & $%d$ & ($%.1f$ \\%%)\\\\\n' % (sr_no, poet, count, count * 100.0 / self.n_slokams))
            total_poet_count += count

            if line_no == 40:
                if first:
                    self.printTableFooter("\\kavis", f)
                else:
                    self.printTableFooter("\\kavis{} (contd...)", f)

                line_no = 0
                first = False
        f.write(' & & & \\\\\n')
        f.write(' & %s & $%d$ & ($%.1f$ \\%%)\\\\\n' % ("\\Unk", self.unknown_poet_count,
                                                    self.unknown_poet_count * 100.0 / self.n_slokams))

        if first:
            self.printTableFooter("\\kavis", f)
        else:
            self.printTableFooter("\\kavis{} (contd...)", f)

    def print_html_header(self, f):
        f.write('<html lang="ml">\n')
        f.write('<head>\n')
        f.write('<meta http-equiv="Content-type" content="text/html; charset=utf-8">\n')
        f.write('<title>Great Slokams</title>\n')
        f.write('</head>\n\n')

        f.write('<body>\n')
        f.write('<center><h1><font color="blue">Great Slokams</font></h1></center>\n')
        f.write('For details, check this <a href="great-slokams.pdf">pdf</a>.  Contact <a href="mailto:umesh.p.narendran@gmail">umesh.p.narendran@gmail.com</a> with corrections and suggestions.\n')
        f.write('<p>\n')
        now = datetime.datetime.now()
        f.write('<i>Last Updated by <b>Umesh P. Narendran</b> on %s %s %s.</i>\n' % (now.year, months[now.month], now.day))

    def print_html_footer(self, f):
        f.write('<p>\n')
        f.write('</body>\n')
        f.write('</html>\n')

if __name__ == '__main__':
    in_dir = os.getcwd()
    generator = SlokamGenerator()
    generator.generate(in_dir)
