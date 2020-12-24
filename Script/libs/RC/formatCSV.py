import sys
import pandas as pd

try:
    import cfg
    import tools
except:
    sys.path.append(r'c:\Gamidor\MyScreen\Script')
    sys.path.append(r'c:\Gamidor\MyScreen\Script\libs')
    import cfg
    import tools


def csv_dumper(sample_summary_excel):
    anno_geno = pd.read_pickle(cfg.anno_pkl)
    anno_cnv = pd.read_pickle(cfg.annotCNV)

    raw = pd.read_excel(sample_summary_excel, sheet_name='Sheet1', header=4)
    UniqueSamples = raw.Sample.unique()
    dfDict = {elem : pd.DataFrame for elem in UniqueSamples}
    for key in dfDict.keys():
        dfDict[key] = raw[:][raw.Sample == key]
    for k,v in dfDict.items():
        dfDict[k].reset_index(inplace=True)
        cases = dfDict[k].AGID.unique()
        print(cases)
        panel = dfDict[k].loc[0, 'Test Name']
        try:
            ags = tools.decompress_pickle(f'{cfg.path_to_panel}{panel}.AGID.pbz2')
        except:
            ags_df = pd.read_csv(cfg.ver2_agids)
            ags = ags_df.AGID.unique()
        ags_filter = [x for x in ags if "/" not in x]
        to_keep = []
        for agid in ags_filter:
            sub = anno_geno[anno_geno.AGID == agid].dropna(how='all')
            classes = sub.Classification.unique()
            if any('CARRIER' in x for x in classes) or not len(classes):
                to_keep.append(agid)
            else:
                if agid in cases:
                    print(sub.Classification.unique(), agid)
        agids = pd.DataFrame(to_keep, columns=['AGID'])

        # agids = [agid for line in agids for agid in line.split('/')]
        # print(agids)
        # print(k, panel)
        # print(cases)
        full = dfDict[k].merge(agids, on='AGID', how='outer').reset_index()
        # print(full)
        full.to_csv('test.csv')
        print()
        # break


if __name__ == "__main__":
    csv_dumper(r'c:\Users\hadas\AGcloud\AGshared\Gamidor\Capture_Panel\HospitalRuns\Zer\201122_MN00742_0106_A000H37LVW\MyScreen_Analysis_v2.1_RESULTS\sample_summary-14-12-2020.xlsx')
