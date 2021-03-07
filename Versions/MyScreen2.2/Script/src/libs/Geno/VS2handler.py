import sys, os, time, datetime
import argparse
import logging
import xlsxwriter
import pandas as pd
import numpy as np
from multiprocessing import Pool
import warnings
warnings.filterwarnings("ignore")

try:
    import cfg
    import libs.tools as tools
    import libs.Geno.VCF as VCF
    import libs.Geno.verifyAGID as verifyAGID
except:
    sys.path.append(r'c:\Gamidor\MyScreen\Script\src')
    sys.path.append(r'c:\Gamidor\MyScreen\Script\src\libs')
    import cfg
    import tools
    import VCF
    import verifyAGID

date = datetime.datetime.now().strftime("%d-%m-%Y")

AGIDs = cfg.ver2_agids
anno_pkl = cfg.anno_pkl
bed_pkl = cfg.bed_pkl
anno_excel = cfg.anno_excel


def convergeComplexedMutations(df, type, anno):
    dict = {}
    targetRowAnno = anno.loc[(anno.AGID == 'AG5316')]
    for row in df.itertuples():
        sample = row.Sample
        if sample in dict:
            dict[sample].add(row.AGID)
        else:
            dict[sample] = {row.AGID}
    for item in dict.items():
        if 'AG3373' in item[1] and 'AG3379' in item[1]:
            targetRowPositive = df[(df['Sample'] == item[0]) & (df['AGID'] == 'AG3373')]
            targetRowPositive_index = targetRowPositive.index[0]
            oldVariant = targetRowPositive['Variant'].get(targetRowPositive_index)
            newVariant = oldVariant.replace('CTCAGCCACTTAGAAT','CTCAGCCACTTAGAATTAACAGT').replace('>C/','>CTAAAAG/').replace('/C\b','/CTAAAAG')
            targetRowPositive['AGID'] = targetRowAnno['AGID'].iloc[0]
            targetRowPositive['Chr'] = targetRowAnno['Chr'].iloc[0]
            targetRowPositive['Coordinate'] = targetRowAnno['Position'].iloc[0]
            targetRowPositive['Gene'] = targetRowAnno['annotation1'].iloc[0].split(':')[0]
            targetRowPositive['Variant'] = newVariant
            targetRowPositive['Custom Annotation'] = targetRowAnno['annotation1'].iloc[0]
            targetRowPositive['Custom Annotation 2'] = targetRowAnno['annotation2'].iloc[0]
            targetRowPositive['Custom Annotation 3'] = targetRowAnno['annotation3'].iloc[0]
            targetRowPositive['Custom Annotation 4'] = targetRowAnno['annotation4'].iloc[0]
            targetRowPositive['gdna'] = targetRowAnno['gdna'].iloc[0]
            smallMutationindexNames = df[(df['Sample'] == item[0]) & ((df['AGID'] == 'AG3373') | (df['AGID'] == 'AG3379'))].index
            largeMutationindexNames = df[(df['Sample'] == item[0]) & (df['AGID'] == 'AG5316')].index
            if type == 'positive':
                df.drop(smallMutationindexNames, inplace=True)
            df.drop(largeMutationindexNames, inplace=True)
            df = df.append(targetRowPositive, ignore_index=True)
    return df

def CYBA_HEXB_AGXT_cor(positive, complete):
    if positive.empty:
        return positive

    cyba_agids = ['AG1476', 'AG4982', 'AG4810', 3]
    hexb_agids = ['AG3456', 'AG5049', 'AG5048', 3]
    agxt_agids = ['AG2466', 'AG5317', 2]
    agid_sets = [cyba_agids, hexb_agids, agxt_agids]

    for agid_set in agid_sets:
        df = positive.where(positive.AGID == agid_set[0])
        df.dropna(how='all', inplace=True)
        if not df.empty:
            i = df.index[0]
            if df.loc[i, 'Classification'] == 'WT' and df.loc[i, 'Problem'] == '-Problem':
                first_avf = df.loc[i, 'Alt Variant Freq']

                second_df = complete.where(complete.AGID == agid_set[1])
                second_df.dropna(how='all', inplace=True)
                second_avf = second_df.loc[second_df.index[0], 'Alt Variant Freq']

                if agid_set[-1] == 3:
                    third_df = complete.where(complete.AGID == agid_set[2])
                    third_df.dropna(how='all', inplace=True)
                    third_avf = third_df.loc[third_df.index[0], 'Alt Variant Freq']

                    if first_avf < 7.0 and (second_avf > 7.0 or third_avf > 7.0):
                        positive.loc[i, 'Problem'] = " - Low GQX - NON_REPORTED variant in the same loc"
                else:
                    if first_avf < 7.0 and second_avf > 7.0:
                        positive.loc[i, 'Problem'] = " - Low GQX - NON_REPORTED variant in the same loc"

    return positive


def reorder(vcf):
    vcf['Classification'] = vcf['Classification'] + vcf['Problem'] + vcf['SoftClipped Reads']
    vcf.drop(columns=['Problem', 'var', 'REF', 'ALT', 'GT', 'AD', 'VF', 'QUAL'], inplace=True)
    vcf.rename(columns={'CHROM': 'Chr', 'POS': 'Coordinate'}, inplace=True)
    return vcf

class Engine():
    def __init__(self, inputpath, anno, bed, vs2_logger):
        self.input_path = inputpath
        self.anno = anno
        self.bed = bed
        self.vs2_logger = vs2_logger
        # self.Output = Output

    def __call__(self, filename):
        vcf_bed = pd.DataFrame()
        vcf_wt = pd.DataFrame()
        vcf_gender = pd.DataFrame()
        vcf_non = pd.DataFrame()
        vcf_positive = pd.DataFrame()
        vcf_complete = pd.DataFrame()

        sample = filename.split('.')[0].strip()
        self.vs2_logger.info("Processing VS2 {}".format(sample))
        print("Processing VS2 {}".format(sample))
        # self.Output.insert(END, "Annotating sample {}\n".format(sample))
        # self.Output.yview_pickplace("end")

        vcf = VCF.dataframe(self.input_path + '/' + filename, large=False)
        vcf.drop(columns=['ID', 'FILTER'], inplace=True)
        vcf.insert(0, 'AGID', np.nan)
        vcf.insert(0, 'Sample', sample)
        vcf.insert(4, 'Gene', np.nan)
        vcf.insert(5, 'Variant', np.nan)
        vcf.insert(6, 'Custom Annotation', np.nan)
        vcf.insert(7, 'Custom Annotation 2', np.nan)
        vcf.insert(8, 'Custom Annotation 3', np.nan)
        vcf.insert(9, 'Custom Annotation 4', np.nan)
        vcf.insert(10, 'gdna', np.nan)
        vcf.insert(11, 'Classification', np.nan)
        vcf.insert(12, 'Problem', np.nan)
        vcf.insert(13, 'Type', np.nan)
        vcf.insert(14, 'Genotype', np.nan)
        gqx = vcf['GQX']
        vcf.drop(labels=['GQX'], axis=1, inplace = True)
        vcf.insert(15, 'GQX', gqx)
        vcf.insert(16, 'Alt Variant Freq', np.nan)
        dp = vcf['DP']
        vcf.drop(labels=['DP'], axis=1, inplace = True)
        vcf.insert(17, 'Read Depth', dp)
        vcf.insert(18, 'Alt Read Depth', np.nan)
        vcf.insert(19, 'Allelic Depths', np.nan)
        vcf.insert(20, 'var', np.nan)
        vcf.insert(21, 'Clalit Disease Makat', np.nan)
        vcf.insert(22, 'Clalit Mutation Makat', np.nan)
        vcf.insert(23, 'SoftClipped Reads', '')

        for index, row in vcf.iterrows():
            avf = float(row.VF)*100
            vcf.loc[index, 'Alt Variant Freq'] = avf
            if isinstance(row.AD, list):
                vcf.loc[index, 'Allelic Depths'] = ','.join(row.AD)
            else:
                vcf.loc[index, 'Allelic Depths'] = row.AD

            try:
                ard = row.AD[1]
            except:
                ard = 0
            vcf.loc[index, 'Alt Read Depth'] = ard

            vars = []
            vars.append(row.REF)
            if isinstance(row.ALT, str):
                vars.append(row.ALT)
            else:
                vars.extend(row.ALT)

            allel1 = int(row.GT[0])
            allel2 = int(row.GT[1])
            vcf.loc[index, 'var'] = vars[allel2]

            if allel1 == allel2:
                vcf.loc[index, 'Genotype'] = 'hom'
            else:
                vcf.loc[index, 'Genotype'] = 'het'

            vcf.loc[index, 'Variant'] = "{}>{}/{}".format(vars[0], vars[allel1], vars[allel2])

            if allel1 == 0 and allel2 == 0:
                vcf.loc[index, 'Type'] = 'reference'
            if vars[allel1] == 'NNN' and vars[allel2] == 'NNN':
                vcf.loc[index, 'Type'] = 'complex'
            if vars[0] != vars[allel2]:
                vcf.loc[index, 'Type'] = 'snv'
            if len(vars[allel1]) > len(vars[allel2]):
                vcf.loc[index, 'Type'] = 'deletion'
            if len(vars[allel1]) < len(vars[allel2]):
                vcf.loc[index, 'Type'] = 'insertion'

            pos = np.int64(row.POS)
            cur_anno = self.anno.loc[(self.anno.Chr == row.CHROM) & (self.anno.Position == pos)
                & (self.anno.REF == vars[0]) & (self.anno.variant == vars[1])
                & (self.anno.GT1 == allel1) & (self.anno.GT2 == allel2)]
            cur_anno.reset_index(drop=True, inplace=True)

            if not cur_anno.empty:
                gene = cur_anno.annotation1[0].split(':')[0]
                vcf.loc[index, 'Gene'] = gene
                vcf.loc[index, 'AGID'] = cur_anno.AGID[0]
                cust_an = cur_anno.annotation1[0]
                vcf.loc[index, 'Custom Annotation'] = cust_an
                vcf.loc[index, 'Custom Annotation 2'] = cur_anno.annotation2[0]
                vcf.loc[index, 'Custom Annotation 3'] = cur_anno.annotation3[0]
                vcf.loc[index, 'Custom Annotation 4'] = cur_anno.annotation4[0]
                clas = cur_anno.Classification[0]
                vcf.loc[index, 'Classification'] = clas
                vcf.loc[index, 'gdna'] = cur_anno.gdna[0]
                vcf.loc[index, 'Clalit Disease Makat'] = cur_anno['Clalit Disease Makat'][0]
                vcf.loc[index, 'Clalit Mutation Makat'] = cur_anno['Clalit Mutation Makat'][0]
            else:
                gene = None
                cust_an = None
                clas = None
                vcf.loc[index, 'AGID'] = 'AGID Not Found'

            read_depth = int(row['Read Depth'])
            gqx = int(row['GQX'])
            chr = row['CHROM']

            # small-medium indel cases
            indels = ['AG2408', 'AG2508', 'AG2846', 'AG5105', 'AG3373', 'AG4652']
            if vcf.loc[index, 'AGID'] in indels and vcf.loc[index,'QUAL'] == "-1":
                vcf.loc[index, 'SoftClipped Reads'] = " - With soft-clipped reads"

            if (((gqx < 15) or ((avf > 7) and (avf < 30)) or (clas == 'ERROR')
            or (clas == 'NO_CALL') or (clas == cust_an)) and (clas != 'MALE')
            and (clas != 'FEMALE') and (clas != 'NON_REPORTED') and (gene != 'SMN1')):
                vcf.loc[index, 'Problem'] = "-Problem"
            else:
                vcf.loc[index, 'Problem'] = ""

            cur_bed = self.bed.loc[(self.bed.Chr == row.CHROM) & (self.bed.Start == pos)]
            cur_bed.reset_index(drop=True, inplace=True)
            if not cur_bed.empty:

                vcf_bed = vcf_bed.append(vcf.loc[index].to_frame().T,
                    ignore_index=True)

                if (((((gqx < 15 ) or ((avf > 10) and (avf < 30 )))
                or (clas == 'CARRIER') or (clas == 'CARRIER-Non-Ashkenazi')
                or (clas == 'CARRIER-Georgian') or (clas == 'CARRIER-Druze')
                or (clas == 'ERROR') or (clas == 'NO_CALL') or (clas == cust_an)
                or (clas == 'HOM')) and (clas != 'MALE') and (clas != 'FEMALE'))
                and (clas != 'NON_REPORTED') and (gene != 'SMN1')):
                    vcf_positive = vcf_positive.append(vcf.loc[index].to_frame().T,
                        ignore_index=True)

                if (clas == 'WT' or clas == 'POLYMORPHISM'):
                    vcf_wt = vcf_wt.append(vcf.loc[index].to_frame().T,
                        ignore_index=True)

                if (chr == 'chrY'):
                    vcf_gender = vcf_gender.append(vcf.loc[index].to_frame().T,
                        ignore_index=True)

                if (((clas == 'NON_REPORTED' )) or (((clas == 'WT' )
                or (clas == 'ERROR') or (clas == 'NO_CALL' )) and ((avf > 15 )))):
                    vcf_non = vcf_non.append(vcf.loc[index].to_frame().T,
                        ignore_index=True)

        vcf_complete = vcf_complete.append(vcf, ignore_index=True)
        vcf_positive = CYBA_HEXB_AGXT_cor(vcf_positive, vcf_complete)
        self.vs2_logger.info("Finished processesing VS2 {}".format(sample))
        # self.Output.insert(END, "Finished annotating sample {}\n".format(sample))
        # self.Output.yview_pickplace("end")
        return [vcf_bed, vcf_wt, vcf_gender, vcf_non, vcf_positive, vcf_complete]

def VS2parser(input_path, main_out, extra_info, logger_name):

    vs2_logger = logging.getLogger(logger_name)
    vs2_logger.info('VS2Handler session started')
    vs2_logger.info('input path: {}'.format(input_path))

    def newPickle():
        anno = pd.read_excel(anno_excel, sheet_name=cfg.GenoAnno)
        anno[['GT1', 'GT2']] = anno.Genotyping.str.split("/",expand=True,)
        anno.GT1 = anno.GT1.astype('int64')
        anno.GT2 = anno.GT2.astype('int64')
        bed = pd.read_excel(anno_excel, sheet_name=cfg.GenoBED)
        anno.to_pickle(anno_pkl)
        bed.to_pickle(bed_pkl)
        vs2_logger.info('Created new pickles')
        return anno, bed

    def oldPickle():
        try:
            anno = pd.read_pickle(anno_pkl)
            bed = pd.read_pickle(bed_pkl)
            vs2_logger.info('Using pickles')
            return anno, bed
        except Exception as e:
            vs2_logger.error("Missing pickles in path\n{}".format(e))
            print("Missing pickles in path")
            os.exit()


    if os.path.exists(anno_excel) and os.path.exists(anno_pkl):
        if os.path.getmtime(anno_excel) > os.path.getmtime(anno_pkl):
            vs2_logger.info('New anno excel file')
            anno, bed = newPickle()
        else:
            anno, bed = oldPickle()
    elif os.path.exists(anno_excel) and not os.path.exists(anno_pkl):
        vs2_logger.info('No pickles')
        anno, bed = newPickle()
    else:
        anno, bed = oldPickle()

    vcf_bed = pd.DataFrame()
    vcf_wt = pd.DataFrame()
    vcf_gender = pd.DataFrame()
    vcf_non = pd.DataFrame()
    vcf_positive = pd.DataFrame()
    vcf_complete = pd.DataFrame()

    files = []
    for filename in os.listdir(input_path):
        if filename.endswith(".vcf"):
            files.append(filename)

    # pool = Pool(cfg.n_workrs)
    # engine = Engine(input_path, anno, bed, vs2_logger)
    # data_outputs = pool.map(engine, files)
    # pool.close()
    # pool.join()
    try:
        pool = Pool(cfg.n_workrs)
        engine = Engine(input_path, anno, bed, vs2_logger)
        data_outputs = pool.map(engine, files)
    except Exception as e:
        vs2_logger.error("# WARNING: Error occured while excuting multiprocessing VS2handler\n{}".format(e))
    finally:
        pool.close()
        pool.join()

    for data in data_outputs:
        vcf_bed = vcf_bed.append(data[0], ignore_index=True)
        vcf_wt = vcf_wt.append(data[1], ignore_index=True)
        vcf_gender = vcf_gender.append(data[2], ignore_index=True)
        vcf_non = vcf_non.append(data[3], ignore_index=True)
        vcf_positive = vcf_positive.append(data[4], ignore_index=True)
        vcf_complete = vcf_complete.append(data[5], ignore_index=True)

    vcf_complete = reorder(vcf_complete)
    tools.compressed_pickle('{}/{}'.format(input_path, cfg.FullGeno), vcf_complete)
    vs2_logger.info("Pickled compressed full Norm genotyping")

    vcf_positive = reorder(vcf_positive)
    # vcf_positive.to_csv('{}/positiveResults.tsv'.format(extra_info) , sep='\t',
    #                     encoding='utf-8', index=False)

    vcf_bed = reorder(vcf_bed)
    # vcf_bed.to_pickle('{}/vcf_bed.pkl'.format(extra_info))
    try:
        missing = verifyAGID.missingAGIDs(AGIDs, vcf_bed, anno_pkl)
    except Exception as e:
        vs2_logger.error("Unable to verify missing AGIDs\n{}".format(e))

    if missing:
        with open("{}/errors.log".format(main_out), 'a+') as f:
            for item in missing:
                f.write("%s\n" % item)

    try:
        vcf_wt = reorder(vcf_wt)
    except:
        vs2_logger.info('No WT Data')

    try:
        vcf_gender = reorder(vcf_gender)
    except:
        vs2_logger.info('No Gender Data')

    try:
        vcf_non = reorder(vcf_non)
    except:
        vs2_logger.info('No NON_REPORTED Data')

    # writer = pd.ExcelWriter('{}Genotyping.xlsx'.format(input_path), engine='xlsxwriter')
    # vcf_bed.to_excel(writer, sheet_name='All', index=False)
    # vcf_positive.to_excel(writer, sheet_name='positiveResults', index=False)
    # vcf_wt.to_excel(writer, sheet_name='WT and POLYMORPHISM', index=False)
    # vcf_gender.to_excel(writer, sheet_name='Gender', index=False)
    # vcf_non.to_excel(writer, sheet_name='Non Reported', index=False)
    # writer.save()

    vcf_bed = convergeComplexedMutations(vcf_bed, 'all', anno)
    vcf_bed = vcf_bed.sort_values(by=['Sample', 'Chr', 'Coordinate'])
    vcf_positive = convergeComplexedMutations(vcf_positive, 'positive', anno)
    vcf_positive = vcf_positive.sort_values(by=['Sample', 'Chr', 'Coordinate'])

    pickles = cfg.GenoPickles
    dfs = {pickles[0]: vcf_bed, pickles[1]: vcf_positive, pickles[2]: vcf_wt,
           pickles[3]: vcf_gender, pickles[4]: vcf_non}
    for name, df in dfs.items():
        # df.to_pickle('{}/{}.pkl'.format(VS2_log_path, name))
        tools.compressed_pickle('{}/{}'.format(extra_info, name), df)
        vs2_logger.info("Pickled compressed {}".format(name))

    vs2_logger.info('Completed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('VS2_files_path', help='Directory Contains VS2 vcf files')
    parser.add_argument('main_out', help='Main results directory')
    parser.add_argument('extra_info', help='Directory for log')
    parser.add_argument('logger_name', help='Log file name')
    # parser.add_argument('Output', help='Text widget')
    args = parser.parse_args()

    VS2parser(args.VS2_files_path, args.main_out, args.extra_info, args.logger_name)
