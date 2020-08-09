import os
import argparse
import subprocess
import sys
import logging
import pandas as pd
import numpy as np
import re
import xlsxwriter

import tools
import cfg

bf_limit_min = cfg.bf_limit_min
bf_limit_max = cfg.bf_limit_max
sexDepth_limit = cfg.sexDepth_limit
cnv_limit = cfg.cnv_limit

sam_cmd = "samtools depth -r chrY:6736783-6736783 {}"
sam_cmd_michal = "C:/samtools/samtools.exe depth -r chrY:6736783-6736783 {}"


def returnSex(string):
    if int(string) < sexDepth_limit:
        return "Female"
    else:
        return "Male"

def SampleDepth(string):
    return string.split('\t')[-1].strip()

def getFPKM(string):
    return string.split(':')[1].strip()

def getInfo(string):
    return re.findall(r"[-+]?\d*\.\d+|\d+", string)

def SampleName(string):
    return string.split('\\')[-1].strip()

def tag_clas(cnv, row, index, cnv_option):
    if pd.isna(row['Classification']):
        cnv.loc[index, 'Classification'] = cnv_option
    else:
        cnv.loc[index, 'Classification'] = cnv_option + ' ' + str(cnv.loc[index, 'Classification'])


def DECoNparser(PATHS):
    input_path = PATHS["DIR_TREE"][6]
    out_dir = PATHS["DIR_TREE"][5]
    anno_pkl = cfg.annotCNV
    targets_pkl = cfg.bedCNV
    targets_excel = cfg.cnvTargets
    fail_file = input_path + "/DECoN_Failures.txt"
    custom_file = input_path + "/DECoN_custom.txt"
    sex_path = input_path + "/sex.txt"

    parser_logger = tools.logger(input_path, 'DECoNParser')
    parser_logger.info('DECoN Output Handler session started')

    try:
        if os.path.getmtime(targets_excel) > os.path.getmtime(targets_pkl):
            parser_logger.info('New targets excel file')
            raise Exception
        annotation = pd.read_pickle(anno_pkl)
        targetsExon = pd.read_pickle(targets_pkl)
        parser_logger.info('Using pickles')
    except:
        annotation = pd.read_excel(targets_excel, sheet_name=cfg.CNVAnno)
        annotation['del_length'] = annotation['Stop'] - annotation['Start']

        targetsExon_raw = pd.read_excel(targets_excel, sheet_name=cfg.CNVtargets)
        targetsExon_raw.index = np.arange(1, len(targetsExon_raw)+1)
        targetsExon = targetsExon_raw.dropna()

        annotation.to_pickle(anno_pkl)
        targetsExon.to_pickle(targets_pkl)
        parser_logger.info('Created new pickles')


    sex_file = open(sex_path, 'w')
    for filename in os.listdir(PATHS["BAM_PATH"]):
        if filename.endswith(".bam"):
            file_path = "{}/{}".format(PATHS["BAM_PATH"], filename)
            try:
                out = subprocess.check_output(sam_cmd.format(file_path),
                        stderr=subprocess.STDOUT, shell=True)
            except:
                try:
                    out = subprocess.check_output(sam_cmd_michal.format(file_path),
                            stderr=subprocess.STDOUT, shell=True)
                except:
                    print("Unable to run samtools {}".format(filename))
                    parser_logger.info("Unable to run samtools {}".format(filename))
                    exit(1)

            out = out.decode('utf-8')
            sex_file.write("{}\n".format(filename.split('.bam')[0]))
            sex_file.write("{}".format(out))
        else:
            continue

    sex_file.close()

    try:
        sex_raw = pd.DataFrame(pd.read_csv(sex_path, sep=' ',header=None))
    except:
        print("Unable to open sex.txt...")
        parser_logger.error("Unable to open sex.txt")
        exit(0)
    sex_mask = sex_raw[0].str.contains("chr")
    depth = sex_raw[sex_mask]
    sample = sex_raw[~sex_mask]
    sample = sample.rename(columns={0:'Sample'})
    depth = pd.DataFrame(depth[0].apply(SampleDepth), columns=[0])
    depth.loc[:, 0] = depth[0].apply(returnSex)
    depth = depth.rename(columns={0:'Gender'})
    depth.index -= 1
    sampleSex = sample.join(depth, sort=False)
    cnv_frame = sampleSex.fillna("Female")
    parser_logger.info('Cnv frame created')


    try:
        failures = pd.DataFrame(pd.read_csv(fail_file, sep='\t'))
    except:
        print("Unable to locate DECoN_Failures.txt...")
        parser_logger.error("Unable to locate DECoN_Failures.txt")
        exit(0)
    failures = failures[~failures.Gene.str.contains("gene")]
    failures.set_index('Exon', inplace=True)

    failed_exon_mask = failures.Type == "Whole exon"
    failures_exon = failures[failed_exon_mask]
    failures_sample = failures[~failed_exon_mask]

    failures_exon.insert(len(failures_exon.columns),'FPKM',
        failures_exon.Info.apply(getFPKM))
    failures_exon = failures_exon.drop(columns=['Type', 'Info'])

    failures_sample.insert(0, 'Sample_short', failures_sample.Sample.apply(SampleName))
    failures_sample.insert(len(failures_sample.columns), 'Info_list',
        failures_sample.Info.apply(getInfo))
    tags = failures_sample.Info_list.apply(pd.Series)
    tags.rename(columns = {0:'Correlation', 1:'median FPKM'}, inplace=True)
    failures_sample = pd.concat([failures_sample[:], tags[:]], axis=1)
    failures_sample.drop(columns=['Info', 'Info_list', 'Type', 'Sample'], inplace=True)
    failures_sample.rename(columns = {'Sample_short':'Sample'}, inplace=True)
    parser_logger.info('Processed failing samples and exons')


    custom_failed_exons = pd.DataFrame()
    custom_exons = targetsExon.index.tolist()
    for index, row in failures_exon.iterrows():
        index = int(index)
        if index in custom_exons:
            cust_ex = int(targetsExon.loc[index]['Custom.Exon'])
            chr = targetsExon.loc[index].Chr
            start = targetsExon.loc[index].Start
            stop = targetsExon.loc[index].End
            temp_df = pd.DataFrame({'Sample': [row.Sample], 'Gene': [row.Gene],
                'Exon': [cust_ex], 'FPKM': [row.FPKM], 'Chr': [chr],
                'Start': [start], 'Stop': [stop]})
            custom_failed_exons = custom_failed_exons.append(temp_df)


    try:
        custom = pd.DataFrame(pd.read_csv(custom_file, sep='\t'))
    except:
        print("Unable to locate DECoN_Custom.txt...")
        parser_logger.error("Unable to locate DECoN_Custom.txt")
        exit(0)
    custom.Sample = custom.Sample.apply(SampleName)
    custom.drop(columns=['CNV.ID', 'Start.b', 'End.b'], inplace=True)
    custom['cnv_length'] = custom.End - custom.Start


    cnv_frame_ext = pd.merge(custom, cnv_frame, on='Sample')
    cnv_frame_ext.insert(0,'Genotype', np.nan, allow_duplicates=True)
    cnv_frame_ext.insert(0,'AGID', np.nan, allow_duplicates=True)
    cnv_frame_ext.insert(0,'Classification', np.nan, allow_duplicates=True)
    # cnv_frame_ext = cnv_frame_ext[(cnv_frame_ext['BF'] > bf_limit_min)]

    femaleDMD = cnv_frame_ext[(cnv_frame_ext.Gender == 'Female') & (cnv_frame_ext.Gene == 'DMD')].copy(deep=True)
    femaleDMD.iloc[:, 1] = 'AG5062'
    femaleDMD.insert(len(femaleDMD.columns),'Annotation1', 'DMD:Duchenne muscular dystrophy', allow_duplicates=True)
    femaleDMD.reset_index(drop=True, inplace=True)
    # femaleDMD = femaleDMD[(femaleDMD['BF'] > bf_limit_min)]

    del_notDMD = cnv_frame_ext[(cnv_frame_ext['CNV.type'] == 'deletion') & (cnv_frame_ext.Gene != 'DMD')]

    del_cftr = del_notDMD[(del_notDMD.Gene == 'CFTR')]
    del_cftr = del_cftr[(del_cftr['BF'] > bf_limit_min)]
    del_notDMD = del_notDMD[~(del_notDMD.Gene == 'CFTR')]

    del_smn = del_notDMD[(del_notDMD.Gene == 'SMN1')].copy(deep=True)
    del_smn.iloc[:, 1] = 'AG3522'
    del_smn.insert(len(del_smn.columns),'Annotation1', 'SMN1:Spinal muscular atrophy-1', allow_duplicates=True)
    del_smn.reset_index(drop=True, inplace=True)
    del_notDMD = del_notDMD[~(del_notDMD.Gene == 'SMN1')]
    del_notDMD = del_notDMD[(del_notDMD['BF'] > bf_limit_min)]

    for index, row in del_notDMD.iterrows():
        subset = annotation.where(annotation.Gene == row.Gene)
        subset.dropna(inplace=True, how='all')
        subset.reset_index(drop=True, inplace=True)
        if row.Gene == 'ATM1':
            row.Gene = 'ATM'
        if (row['Custom.first'] != subset.loc[0,'Custom.first'] and row['Custom.first'] != (subset.loc[0,'Custom.first']+1)) \
         or (row['Custom.last'] != subset.loc[0,'Custom.last'] and row['Custom.last'] != (subset.loc[0,'Custom.last']-1)):
            del_notDMD.loc[index, 'Classification'] = 'Big Del Boundaries Different as Reported'
        if int(row.BF) < bf_limit_min:
            del_notDMD = del_notDMD.drop(index)
        else:
            del_notDMD.loc[index, 'AGID'] = subset.loc[0, 'AGID']
            del_notDMD.loc[index, 'Annotation1'] = subset.loc[0, 'Annotation1']
    del_notDMD.reset_index(drop=True, inplace=True)

    cftr_subset = annotation.where(annotation.Gene == 'CFTR')
    cftr_subset.dropna(inplace=True)
    for index, row in del_cftr.iterrows():
        try:
            subset = cftr_subset.where(cftr_subset['Custom.first'] == row['Custom.first'])
            subset = cftr_subset.where(cftr_subset['Custom.last'] == row['Custom.last'])
            subset.dropna(inplace=True)
            subset.reset_index(drop=True, inplace=True)
            if int(row.BF) < bf_limit_min:
                del_cftr.drop(index, inplace=True)
            else:
                del_cftr.loc[index, 'AGID'] = subset.loc[0, 'AGID']
                del_cftr.loc[index, 'Annotation1'] = subset.loc[0, 'Annotation1']
        except:
            try:
                subset = cftr_subset.where(cftr_subset['Custom.first'] == row['Custom.first'])
                subset.dropna(inplace=True)
                subset.reset_index(drop=True, inplace=True)
                if int(row.BF) < bf_limit_min:
                    del_cftr.drop(index, inplace=True)
                else:
                    del_cftr.loc[index, 'AGID'] = subset.loc[0, 'AGID']
                    del_cftr.loc[index, 'Annotation1'] = subset.loc[0, 'Annotation1']
            except:
                subset = cftr_subset.where(cftr_subset['Custom.last'] == row['Custom.last'])
                subset.dropna(inplace=True)
                subset.reset_index(drop=True, inplace=True)
                if int(row.BF) < bf_limit_min:
                    del_cftr.drop(index, inplace=True)
                else:
                    del_cftr.loc[index, 'AGID'] = subset.loc[0, 'AGID']
                    del_cftr.loc[index, 'Annotation1'] = subset.loc[0, 'Annotation1']
            if (row['Custom.first'] != subset.loc[0,'Custom.first'] and row['Custom.first'] != (subset.loc[0,'Custom.first']+1)) \
             or (row['Custom.last'] != subset.loc[0,'Custom.last'] and row['Custom.last'] != (subset.loc[0,'Custom.last']-1)):
                del_cftr.loc[index, 'Classification'] = 'Big Del Boundaries Different as Reported'
    del_cftr.reset_index(drop=True, inplace=True)

    cnv = pd.concat([del_notDMD, del_cftr, femaleDMD, del_smn], sort=False)
    cnv.reset_index(drop=True, inplace=True)
    for index, row in cnv.iterrows():
        if int(row.BF) < bf_limit_max:
            tag_clas(cnv, row, index, 'CNV-Problem')
        else:
            tag_clas(cnv, row, index, 'CNV')

        if row['Reads.ratio'] <= 0.08:
            cnv.loc[index, 'Genotype'] = 'hom'
        elif row['Reads.ratio'] > 0.29 and row['Reads.ratio'] < 0.71:
            cnv.loc[index, 'Genotype'] = 'het'
        elif row['Reads.ratio'] >= 0.71 and row['Reads.ratio'] < 1.3:
            cnv.loc[index, 'Genotype'] = 'het'
            tag_clas(cnv, row, index, 'CNV-Problem')
        elif row['Reads.ratio'] >= 1.3 and row['Reads.ratio'] < 1.71:
            cnv.loc[index, 'Genotype'] = 'het'
        else:
            cnv.loc[index, 'Genotype'] = 'het'
            tag_clas(cnv, row, index, 'CNV-Problem')

        if row.Sample in failures_sample.Sample.tolist():
            cnv.loc[index, 'Info'] = 'Failed Sample'
            tag_clas(cnv, row, index, 'CNV-Problem')

    cnv.reset_index(drop=True, inplace=True)
    cnv.rename(columns = {'End':'Observed Stop', 'Start':'Observed Start'}, inplace=True)
    parser_logger.info('Processed CNVs')

    cnv.insert(0, 'Annotation2', np.nan)
    cnv.insert(0, 'Annotation3', np.nan)
    cnv.insert(0, 'Annotation4', np.nan)
    cnv.insert(0, 'gdna', np.nan)
    cnv.insert(0, 'Clalit Disease Makat', np.nan)
    cnv.insert(0, 'Clalit Mutation Makat', np.nan)
    for index, row in cnv.iterrows():
        subset = annotation.where(annotation['AGID'] == row['AGID'])
        subset.dropna(inplace=True, how='all')
        subset.reset_index(drop=True, inplace=True)
        cnv.loc[index, 'Annotation2'] = subset.loc[0, 'Annotation2']
        cnv.loc[index, 'Annotation3'] = subset.loc[0, 'Annotation3']
        cnv.loc[index, 'Annotation4'] = subset.loc[0, 'Annotation4']
        cnv.loc[index, 'gdna'] = subset.loc[0, 'gdna']
        cnv.loc[index, 'Clalit Disease Makat'] = subset.loc[0, 'Clalit Disease Makat']
        cnv.loc[index, 'Clalit Mutation Makat'] = subset.loc[0, 'Clalit Mutation Makat']

    cnv_excel = cnv.reindex(columns=['Sample', 'AGID', 'Annotation1', 'CNV.type', 'Gene', 'Genotype',
        'Custom.first', 'Custom.last', 'Chromosome', 'Observed Start' , 'Observed Stop', 'Correlation',
        'N.comp', 'BF', 'Reads.expected', 'Reads.observed', 'Reads.ratio', 'Gender',
        'Classification', 'Info', 'Annotation2', 'Annotation3', 'Annotation4', 'gdna',
        'Clalit Disease Makat', 'Clalit Mutation Makat'])
    cnv_excel.sort_values(by=['Classification'], inplace=True)

    cnv_tsv = pd.merge(cnv, cnv_frame, on=['Sample', 'Gender'], how='right')
    cnv_tsv = cnv_tsv.reindex(columns=['Sample', 'AGID', 'Annotation1', 'CNV.type',
        'Gene', 'Genotype', 'Custom.first', 'Custom.last', 'Chromosome', 'Observed Start' ,
        'Observed Stop', 'Correlation', 'N.comp', 'BF', 'Reads.expected', 'Reads.observed',
        'Reads.ratio', 'Gender', 'Classification', 'Info', 'Annotation2',
        'Annotation3', 'Annotation4', 'gdna', 'Clalit Disease Makat', 'Clalit Mutation Makat'])

    # cnv_tsv.to_csv(out_dir + '/DECoN_results.tsv', sep='\t', encoding='utf-8', index=False)
    # parser_logger.info('Generated tsv')

    # cnv_tsv.to_pickle("{}/{}.pkl".format(out_dir, cfg.FullCNV))
    tools.compressed_pickle("{}/{}".format(out_dir, cfg.FullCNV), cnv_tsv)
    parser_logger.info('Generated compressed DECoN results')

    pickles = cfg.CNVPickles
    dfs = {pickles[0]: cnv_excel, pickles[1]: failures_sample,
           pickles[2]: custom_failed_exons}
    for name, df in dfs.items():
        # df.to_pickle('{}/{}.pkl'.format(input_path, name))
        tools.compressed_pickle('{}/{}'.format(input_path, name), df)
        parser_logger.info("Pickled compressed {}".format(name))

    # writer = pd.ExcelWriter(out_dir + '/CNV-DECoN.xlsx', engine='xlsxwriter')
    # cnv_excel.to_excel(writer, sheet_name='Calls', index=False)
    # failures_sample.to_excel(writer, sheet_name='Failures_samples', index=False)
    # custom_failed_exons.to_excel(writer, sheet_name='Failures_exons', index=False)
    # writer.save()
    # parser_logger.info('Generated excel')
    parser_logger.info('Completed')

    # print("CNV detection completed!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('PATHS', help='List of paths')
    args = parser.parse_args()

    DECoNparser(args.PATHS)
