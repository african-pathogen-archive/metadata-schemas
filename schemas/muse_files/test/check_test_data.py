#!/usr/bin/env python3

import argparse
import csv
import json
import re
import string
import sys

def replacement(match):
    return f'${{{match.group(1).replace(" ", "_")}}}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check test data')
    parser.add_argument('tsv_template_file', type=argparse.FileType(), help='TSV template file')
    parser.add_argument('tsv_data_file', type=argparse.FileType(), help='TSV data file')
    parser.add_argument('json_schema_file', type=argparse.FileType(), help='JSON schema file')
    parser.add_argument('json_doc_template_file', type=argparse.FileType(), help='JSON document template file')
    args = parser.parse_args()

    field_info = json.load(args.tsv_template_file)
    header = next(args.tsv_data_file).strip().split('\t')
    del header[1] # remove the fasta header name column
    # sample recieved data should be sample received date
    # geo_loc name (country)

    lookup = {
        'study_ID': 'study_id',
        'geo_loc name (country)': 'geo loc country',
        'geo_loc name (state/province/territory)': 'geo loc province',
        'vibrio cholerae RDT test': 'vibrio cholerae rdt test',
        'vibrio cholerae RDT test date': 'vibrio cholerae rdt test date',
        'vibrio cholerae RDT result': 'vibrio cholerae rdt result',
        'diagnostic pcr Ct value 1': 'diagnostic pcr ct value 1',
        'diagnostic pcr Ct value 2': 'diagnostic pcr ct value 2',
        'host (scientific name)': 'host scientific name',
        'host residence geo_loc name (country)': 'host residence geoloc country',
        'location of exposure geo_loc name (country)': 'location of exposure geoloc country',
        'destination of most recent travel (city)': 'destination of most recent travel',
        'destination of most recent travel (state/province/territory)': 'destination of most recent travel geoloc province',
        'destination of most recent travel (country)': 'destination of most recent travel geoloc country',
    }
    field_info_dict = {}
    for i, field in enumerate(field_info):
        if field['name'] != header[i]:
            print(f'Error: {field["name"]} != {header[i]}', file=sys.stderr)
            sys.exit(1)
        key = lookup.get(field['name'], field['name'])
        field_info_dict[key] = field
    
    tsv_data_filename = args.tsv_data_file.name
    args.tsv_data_file.close()
    args.tsv_data_file = open(tsv_data_filename, 'r')

    substr_re = re.compile(r'\$\{([^}]+)\}')
    json_doc_template_source = args.json_doc_template_file.read()
    json_doc_template_source = substr_re.sub(replacement, json_doc_template_source)
    json_doc_template = string.Template(json_doc_template_source)
    tsv_reader = csv.DictReader(args.tsv_data_file, delimiter='\t')
    for row in tsv_reader:
        resolved_row = {}
        for key in row:
            if key == 'fasta header name':
                continue
            resolved_key = lookup.get(key, key)
            subst_resolved_key = resolved_key.replace(' ', '_')
            if field_info_dict[resolved_key]['valueType'] == 'string':
                if row[key] == '':
                    resolved_row[subst_resolved_key] = 'null'
                else:
                    resolved_row[subst_resolved_key] = f'"{row[key]}"'
            elif field_info_dict[resolved_key]['valueType'] == 'number':
                try:
                    resolved_row[subst_resolved_key] = float(row[key])
                except ValueError:
                    resolved_row[subst_resolved_key] = 'null'
        print(resolved_row, file=sys.stderr)
        json_doc = json_doc_template.substitute(resolved_row)
        print(json_doc)
        break
