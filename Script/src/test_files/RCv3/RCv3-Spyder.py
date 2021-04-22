# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

try:
    import cfg
    import tools
except:
    sys.path.append(r'c:\Gamidor\MyScreen\Script')
    sys.path.append(r'c:\Gamidor\MyScreen\Script\libs')
    import cfg
    import tools


csv_cols = ['Sample', 'Test Code', 'Test Name', 'Disease', 'Gene', 'Mutation', 
            'MOH', 'Ethnicity', 'Classification', 'Clalit Disease Makat', 
            'Clalit Mutation Makat', 'Remark', 'GQX', 'Alt Variant Freq', 
            'Read Depth', 'Alt Read Depth', 'Allelic Depths', 'Correlation', 
            'N comp', 'Custom First', 'Custom Last', 'BF', 'Reads Expected', 
            'Reads Observed', 'Reads Ratio', 'Analyzed Gender', 'Reported Gender', 
            'Sample Source', 'Mother Ethnicity', 'Father Ethnicity', 
            'Partner Sample','AGID', 'IGV Link (open IGV before)', 'Result 2']


def split_rows(df):
    
    s = df["AGID"].str.split('/', expand=True).stack()
    i = s.index.get_level_values(0)
    df2 = df.loc[i].copy()
    df2["AGID"] = s.values
    
    return df2


def get_panels_agids():
    
    panels_agids = {}
    for panel in cfg.Panels_names:
        panel_set = tools.decompress_pickle(
            "{}/{}.AGID.reported.pbz2".format(cfg.path_to_panel, panel))
        panels_agids[panel] = pd.DataFrame(list(panel_set), columns=['AGID'])
        panels_agids[panel].set_index('AGID', inplace=True)
    
    return panels_agids


def get_annos():
    
    geno_anno = pd.read_pickle(cfg.anno_pkl)
    geno_anno_wt = geno_anno[geno_anno['Classification'] == 'WT'].copy()
    geno_anno_wt['Mutation'] = geno_anno_wt[['annotation2', 'gdna']].agg('\n'.join, axis=1)
    ganno = geno_anno_wt[['AGID', 'Mutation']]
    ganno.set_index('AGID', inplace=True)
    
    cnv_anno = pd.read_pickle(cfg.annotCNV)
    cnv_anno['Disease'] = cnv_anno['Annotation1'].apply(lambda x: x.split(':')[1])
    cnv_anno['Mutation'] = cnv_anno[['Annotation2', 'gdna']].agg('\n'.join, axis=1)
    cnv_anno.rename(columns={'Annotation3':'MOH', 'Annotation4':'Ethnicity'}, inplace=True)
    cnv_anno[['Correlation', 'N comp', 'Custom First', 'Custom Last', 'BF', 'Reads Expected', 'Reads Observed', 'Reads Ratio']] = np.nan
    cnv_anno.drop(columns=['Chr', 'Start', 'Stop', 'gdna', 'Custom.first', 'Custom.last', 'Annotation1', 'Annotation2', 'del_length'], inplace=True)
    cnv_anno['Classification'], cnv_anno['Genotype'] = 'WT', 'hom'
    cnv_anno.set_index('AGID', inplace=True)
    
    return ganno, cnv_anno


def create_summary_csv(**data):

    All_split = split_rows(tools.decompress_pickle(data["All"]))
    All_split[['Sample', 'S']] = All_split.Sample.str.split('_S',expand=True)
    All_split['Disease'] = All_split['Custom Annotation'].apply(lambda x : x.split(':')[1])
    All_split.rename(columns={'Custom Annotation 3':'MOH', 'Custom Annotation 4':'Ethnicity'}, inplace=True)
    All_split.drop(columns=['Coordinate', 'Variant', 'Chr', 'gdna', 'Custom Annotation', 'Custom Annotation 2', 'Type', 'SoftClipped Reads'], inplace=True)
    All_split.set_index('AGID', inplace=True)
    
    summary = pd.read_excel(data["summary"], engine = 'openpyxl', skiprows=4)
    summary.set_index('AGID', inplace = True)
    
    summary_csv = pd.DataFrame(columns=summary.columns)
    
    ganno, cnv_anno = get_annos()
    
    annotated = All_split.join(ganno, how='left')
    
    panels_agids = get_panels_agids()
    
    same_cols = set(summary.columns) - set(annotated.columns) - set(cnv_anno.columns)
    
    for sample in set(annotated.Sample.tolist()):
        sample =str(sample) 
        cur = annotated[annotated.Sample == sample]
        cur = pd.concat([cur, cnv_anno])
        
        cur['Sample'] = sample
        cur['S'] = cur.iloc[0]['S']
        
        in_positive = summary[summary['Sample'].astype('str') == sample]
        
        panel = in_positive.iloc[0]['Test Name']
        pos = in_positive.index.tolist()
        
        cur_panel = panels_agids[panel].join(cur, how='left')
        if pos != ['AG0000']:
            pos = [x.split('_')[0] for x in pos]
            cur_panel.drop(pos, inplace=True)
            cur_panel = pd.concat([in_positive, cur_panel])
            
        for col in same_cols:
            cur_panel[col] = in_positive.iloc[0][col]
        
        if in_positive.iloc[0]['Classification'] == 'SAMPLE FAILED':
            cur_panel['Classification'] = 'SAMPLE FAILED'
        
        cur_panel.reset_index(inplace=True)
        cur_panel['AGID'] = cur_panel['AGID'].apply(lambda x: x.split('_')[0])
        dmd = cur_panel[cur_panel.Gene == 'DMD']
        for ag in dmd.AGID.unique():
            dmd_ag = dmd[dmd.AGID == ag]
            for i,(index,row) in enumerate(dmd_ag.iterrows(), 1):
                cur_panel.loc[index, 'AGID'] = f'{row.AGID}_{i}'
                cur_panel.loc[index, 'Result 2'] = cur_panel.loc[index, 'Mutation']
        cur_panel.set_index('AGID', inplace=True)
        
        summary_csv = summary_csv.append(cur_panel)
        
    summary_csv.rename(columns={'Genotype':'Remark'}, inplace=True)
    summary_csv.index.rename('AGID', inplace=True)
    summary_csv.reset_index(inplace=True)
    summary_csv.fillna('---', inplace=True)
    
    header = ",Data Analysis Version,,Run Name,,Analysis Date,,,,,,,,,,,,,,,,,,,,,,,,,,,\n \
        ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n \
        ,{},,{},,{},,,,,,,,,,,,,,,,,,,,,,,,,,, \n \
        ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n \
        ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,, \n \
        ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,".format(data["v"], data["r"], data["d"])
    
    with open('summary_csv.csv', 'w', newline='', encoding='utf-8') as fp:
        fp.write(header)
        summary_csv[csv_cols].to_csv(fp, index=False)
    
    with open('summary_csv.psv', 'w', newline='', encoding='utf-8') as fp:
        fp.write(header.replace(',', '|'))
        summary_csv[csv_cols].to_csv(fp, index=False, sep="|")

if __name__ == "__main__":
    
    
    all_path = r'c:\Users\hadas\AGcloud\AGshared\Gamidor\Capture_Panel\HospitalRuns\Belinson\210121_MN00937_0057_A000H37MCG\MyScreen_Analysis_v2.2_RESULTS\Info\Genotyping\Logs\All.filtered.pbz2'
    summary_path = r'c:\Users\hadas\AGcloud\AGshared\Gamidor\Capture_Panel\HospitalRuns\Belinson\210121_MN00937_0057_A000H37MCG\MyScreen_Analysis_v2.2_RESULTS\sample_summary-17-02-2021.xlsx' 
    
    ver = "MyScreen_Analysis_v2.1"
    run = "201101_MN00742_0104_A000H37LNW"
    date = "30-Nov-20"
    
    create_summary_csv(All = all_path, summary = summary_path, v = ver, r = run, d = date)
    
    