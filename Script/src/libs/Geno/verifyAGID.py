import pandas as pd
import argparse

def missingAGIDs(file, genotyping, anno_pkl):
    missing = []
    agids_df = pd.read_csv(file, sep='\t')
    agids = agids_df.AGID.to_list()

    anno = pd.read_pickle(anno_pkl)
    split_data = anno.AGID.str.split("/")
    data = split_data.to_list()
    max_l = max(len(l) for l in data)
    names = ["AGID-{}".format(i) for i in range(max_l)]
    anno = pd.DataFrame(data, columns=names)
    anno.sort_values('AGID-1', ascending=False, inplace=True)
    anno.drop_duplicates(subset='AGID-0', keep='first', inplace=True)

    samples = genotyping.Sample.unique()
    for sample in samples:
        cur = genotyping.where(genotyping.Sample == sample)
        cur.dropna(how='all', inplace=True)
        cur_agids = []
        for index, row in cur.iterrows():
            now = row.AGID.split("/")
            for n in now:
                cur_agids.append(n)
        for agid in agids:
            if agid not in cur_agids:
                df = anno[anno.eq(agid).any(1)]
                df.reset_index(drop=True, inplace=True)
                ags = list(filter(None.__ne__, df.iloc[0].values.tolist()))
                S1 = set(cur_agids)
                S2 = set(ags)
                if not S1.intersection(S2):
                    print("{} is missing in sample {}".format(agid, sample))
                    missing.append("{} is missing in sample {}".format(agid, sample))
    return missing

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('AGIDs', help='Tab Separted File Containing List of AGIDs')
    parser.add_argument('Genotyping', help='DataFrame Genotyping-All')
    parser.add_argument('anno_pkl', help='Anno Pickle')
    args = parser.parse_args()

    genotyping = pd.read_pickle(args.Genotyping)
    missing = missingAGIDs(args.AGIDs, genotyping, args.anno_pkl)
