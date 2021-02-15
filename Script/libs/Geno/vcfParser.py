"""pseudocode
1.  load in genome vcf as pandas. "filter out alt with ."
2.  load in candidate as csv file
3.  loop through candidate vcf chr/pos, get the record from pandas
4.  If no <M>, then just print out the record with "ForcedReport"
5.  If block with <M>, then gather all the alt, keep record where the row doesn't have <M>
170816 adding alt to sampleAlt[key]
"""
import warnings
import pandas as pd
#from pandas.core.common import SettingWithCopyWarning
#warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
import csv
import re
import getopt
import sys
import math
import SoftClipsSolution
import re
import argparse
import os
import logging

try:
    import cfg
except:
    sys.path.append(r'c:\Gamidor\MyScreen\Script')
    import cfg

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.options.mode.chained_assignment = None

# inputfile = sys.argv[1]
# outputfile = sys.argv[2]
# vcffile = sys.argv[3]

'''
    Purpose: logger - document the analysis steps
    Input: (string) path for the logger file (txt) to be set in
    Output: None
'''
def logger(out, name, logger_name):
    # log_file = "{}/{}-Parser.log".format(out, name)
    # for handler in logging.root.handlers[:]:
    #     logging.root.removeHandler(handler)
    # logging.basicConfig(filename=log_file,
    #                     level=logging.INFO,
    #                     format='%(asctime)s %(levelname)-8s %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # global parser_logger
    # parser_logger = logging.getLogger('{}-Parser.log'.format(name))
    global parser_logger
    parser_logger = logging.getLogger(logger_name)


'''
    Purpose: parse the Pisces's results
    Input:  (string) path of a VCF file (input file)
            (string) path of a VS2 file (output file with same sample-name as the input file)
            (string) path of the Norm VCF file
    Output: VS2 file
'''
def parserMainFunction(inputFile, outputFile, bamFilesDir, vcfFile, input_file_name, logger_name):
    file = open(inputFile, 'r')
    outfile = open(outputFile, 'w')
    row2Skip = 0
    # Extract and count header rows (with "#")
    parser_logger.info("# adding header rows")
    for line in file:
        if re.match("#.*", line):
            outfile.write(line)
            row2Skip += 1
    row2Skip -= 1  # Subtracting 1 because we need to include header for pandas dataframe
    vcf = pd.read_csv(inputFile, sep="\t", skiprows=row2Skip)
    row2SkipPisces = row2Skip + 2  # Scylla output has 2 additional lines
    phasedInputFile = re.sub("genome", "phased.genome", inputFile)
    phasedVcf = pd.read_csv(phasedInputFile, sep="\t", skiprows=row2SkipPisces, dtype={'ALT': str})

    # MNP = Multi Nucleotide Polymorphism
    # this section is a duct tape.  We are reading in phased genotype for these two position.
    # grab info from vcf with anchor var and position
    for mnp, mnp2, alt, anchor in zip((71887766, 91310151, 117232191, 183184686, 122277741, 81534622, 241816967,
                                       51065766, 108196135, 108143539, 158564126, 136221514, 55648503, 117232194,
                                       108196134, 117304854, 241816967, 122277742, 81534624, 51065765), (
                                              71887766, 91310151, 117232197, 183184686, 122277742, 81534624, 241816967,
                                              51065766, 108196135, 108143539, 158564126, 136221514, 55648503, 117232194,
                                              108196135, 117304855, 241816967, 122277743, 81534625, 51065767), (
                                              "ACCCC", "ATTAGATTC", "GA", "CACCAC", "AGA", "GCCT", "CG", "AG", "TCTC",
                                              "CTGAT",
                                              "CTATACT", "TCAT", "CAACAGCACTA", "G", "ATCTC", "CAA", "CG", "GA", "CT",
                                              "AG"), (
                                              "A", "AT", "GA", "CA", "AGA", "C", "CG", "AG", "T", "CTG", "CTATA", "T",
                                              "CA",
                                              "G", "T", "C", "C", "A", "G", "G")):
        gvcf_db_mnp = vcf[(vcf['POS'].between(mnp, mnp2, inclusive=True)) & (vcf['ALT'] == anchor)]
        if not gvcf_db_mnp.empty:
            new_info = gvcf_db_mnp.iloc[0][9]
        # filter the dataframe from the phased gvcf for just the MNP of interest
        if mnp == 117232191:
            gvcf_db_mnp2 = vcf[vcf['POS'] == mnp2]
            if not gvcf_db_mnp2.empty and not gvcf_db_mnp.empty:
                sampleName = gvcf_db_mnp2.columns.values[9]
                if re.match("0/1", gvcf_db_mnp.iloc[0][9]):
                    if re.match("0/1", gvcf_db_mnp2.iloc[0][9]):
                        mnp_index = vcf.index[vcf['POS'] == mnp].tolist()
                        for i in mnp_index:
                            vcf.at[i, 'REF'] = 'GAAGAAATTCAATCCT'
                            vcf.at[i, 'ALT'] = 'GAAAGAAA'
                            vcf.at[i, sampleName] = new_info

        phasedVar = phasedVcf[(phasedVcf['POS'].between(mnp, mnp2, inclusive=True)) & (phasedVcf['ALT'] == alt)]
        sampleName = phasedVar.columns.values[9]
        for index, df in phasedVar.iterrows():
            info = df.iloc[9]
            # this section replace incorrect 1/. call by Pisces to be
            if re.match("1/.", info):
                # phasedVar.set_value(index, sampleName, new_info)
                phasedVar.at[index, sampleName] = new_info

        # filter the gvcf for everything but the MNP
        # Do not filter or else we will not find the var
        # vcf=vcf[vcf['POS']!=mnp]
        # combine phased MNP + gvcf
        vcf = pd.concat([vcf, phasedVar])

    for pos, ref, alt in zip((122277742, 81534624, 241816967, 51065766, 66565297), ("AC", "AG", "GC", "GA", "GC"),
                             ("GA", "CT", "CG", "AG", "TT")):
        vcfMNV = vcf[(vcf['POS'] == pos) & (vcf['REF'] == ref) & (vcf['ALT'] == ".")]
        if vcfMNV.empty:  # if vcf file doen't contain the 4 mnv, we will copy the information from first base and alter ref/alt and inject it to our vcf file
            vcfMNV2 = vcf[(vcf['POS'] == pos)]
            for i, df in vcfMNV2.iterrows():
                vcfMNV2.at[i, 'REF'] = ref
                vcfMNV2.at[i, 'ALT'] = alt
            vcf = pd.concat([vcf, vcfMNV2])

    # Initialize some dictionaries
    sampleRecord = {}
    sampleAlt = {}
    qual = {}
    strandBias = {}

    # Keep track of two indels AG1998 and AG3268 - DATE 190401
    AG1998_part1 = ''
    AG1998_part1_df = pd.DataFrame()
    AG3268_part1 = ''
    AG3268_part1_df = pd.DataFrame()

    # read in and start to loop in candidate vcf file and search for these candidates in our gVCF file
    with open(vcfFile, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter="\t")
        for row in csv_reader:
            # ignore header matching "#"
            if re.match('^#.*', row[0]) or row[4] == ".":
                continue
            chr = row[0]
            pos = row[1]
            ref = row[3]
            var = row[4]
            key = chr + "." + pos + "." + ref + "." + var # create a key for dictionary
            altCand = row[4]
            sampleAlt[key] = altCand  # here we add the alternative we are looking for to our final output
            sampleAltList = altCand.split(",")
            qual[key] = 0
            strandBias[key] = "0.0000"
            # here we find the chr and pos of gvcf.  Note, we may have more than one record per chr and pos
            eachRecord = vcf[(vcf['#CHROM'] == chr) & (vcf['POS'] == int(pos)) & (vcf['REF'] == ref) & ((vcf['ALT'] == var) | (vcf['ALT'].str.contains(var+",<M>")) | (vcf['ALT'].str.contains("<M>,"+var)))]
            # Now we loop through the gVCF of the specific chr and pos
            for i, (index, df) in enumerate(eachRecord.iterrows()):
                if df.iloc[4] != '.':
                    parser_logger.info("# analyzing variation {}-{}-{}-{}".format(str(df.iloc[0]), str(df.iloc[1]), df.iloc[3], df.iloc[4]))
                qual[key] = df.iloc[5]  # capture the quality regardless if it pass  otherwise, single record would have 0
                sample = df.iloc[9]  # sample is the last column of the gVCF containing the sample information.
                alt = df.iloc[4]
                alt = re.sub(',*<M>,*', "", alt)  # replace all <M> which is vcf way of saying "something else" in alt
                info = df.iloc[6]  # info is column 7
                # this section replaces Quality and SB with right record from "." in alt
                if altCand == alt:
                    if not key in sampleRecord.keys():
                        sampleRecord[key] = sample
                if re.match("PASS", info):
                    qual[key] = df.iloc[5]  # capture quality
                    samples = sample.split(":")
                    strandBias[key] = samples[-1]  # capture strand bias
                if (re.match("0/1", sample)) or (re.match("1/0", sample)) or (re.match("1/1", sample)):
                    # here we are calling alt and to avoid adding 2 alt with identical entry, delete old entry
                    if alt in sampleAltList:
                        sampleAltList.remove(alt)
                    sampleRecord[key] = sample
                    sampleAltList.insert(0, alt)
                # if it is not het or hom alt then record alt as second alt i.e. "misc",alt
                elif re.match("2/2", sample):
                    if i + 1 == len(eachRecord) and not key in sampleRecord:
                        # we will capture 2/2 record if this is the last record and we have not yet captured any sampleRecord
                        sampleRecord[key] = sample
                    if not alt in sampleAltList:  # however, if we already has alt ignore it.
                        sampleAltList.append(alt)
                else:  # capture 0/0  Here the addAlt need to add alternative to as a secondary variant
                    if not altCand.startswith(alt):
                        sample = re.sub("/1", "/2", sample)
                    if not key in sampleRecord:  # if a sampleRecord doesn't exist, capture it.
                        sampleRecord[key] = sample
                    if re.match(".*ForcedReport", info) or re.match("\.\/\.", sampleRecord[key]):  # if we see ForcedReport, we will use the sample info
                        sampleRecord[key] = sample
                    if (not re.match("\.", alt)) and (not alt in sampleAltList):  # here if alt is not "." we add alt
                        sampleAltList.extend(alt)
                # if we are at the last record, print out the chr/pos of interest below
                if i + 1 == len(eachRecord):  # reached last record
                    if re.match("\./\.", sampleRecord[key]) or re.match("0/\.", sampleRecord[key]):  # fixes ./. to be NNNN
                        sampleAltList.insert(0, "NNN")
                        sampleRecord[key] = re.sub("0/\.", "0/1", sampleRecord[key])
                        sampleRecord[key] = re.sub("\./\.", "1/1", sampleRecord[key])
                    if re.match("2/2", sampleRecord[key]):
                        sampleRecord[key] = re.sub("2/2", "0/0", sampleRecord[key])
                    if re.match("1/\.", sampleRecord[key]):  # fixes 1/. to be NNN
                        sampleAltList.insert(0, "NNN")
                        sampleRecord[key] = re.sub("1/\.", "2/1", sampleRecord[key])

                    df.iloc[4] = ",".join(sampleAltList)
                    df.iloc[8] = re.sub("GQ", "GQX", df.iloc[8])  # replace GQ with GQX
                    df.iloc[9] = sampleRecord[key]
                    if key in qual:
                        df.iloc[5] = qual[key]

                    # Keep track of indel AG1998 - DATE 190401
                    if df.iloc[1] == 20763658:  # We are in chr13_20763658_TCCAATGCTGG_T
                        AG1998_part1_alt = df.iloc[4]  # Keep track for NNN (no calls).
                        AG1998_part1 = df.iloc[9]  # Keep track of genotype.
                        AG1998_part1_df = df  # Save df.
                        continue  # Next loop will be chr13_20763669_TG_T
                    if df.iloc[1] == 20763669:  # We are in chr13_20763669_TG_T
                        AG1998_part2_alt = df.iloc[4]  # Get alt variants (for NNN if exists).
                        AG1998_part2 = df.iloc[9]
                        AG1998_part1_GT = AG1998_part1.split(":")[0]  # Get genotype.
                        AG1998_part2_GT = AG1998_part2.split(":")[0]  # Get genotype.
                        if AG1998_part1_GT == AG1998_part2_GT:  # Both parts of the mutation have equal genotypes, we combine into one.
                            df.iloc[1] = "20763658"  # Position.
                            df.iloc[3] = "TCCAATGCTGGTG"  # Ref.
                            if ("NNN" in AG1998_part1_alt) or ("NNN" in AG1998_part2_alt):  # Check if mutation is no call.
                                df.iloc[4] = "NNN,TT"  # Alt (no call).
                            else:
                                df.iloc[4] = "TT"  # Alt.
                            AG1998_part1_VF = AG1998_part1.split(":")[4]  # Get variant frequency.
                            AG1998_part2_VF = AG1998_part2.split(":")[4]  # Get variant frequency.
                            if AG1998_part1_VF > AG1998_part2_VF:  # Take stats with higher variant frequency.
                                df.iloc[9] = AG1998_part1
                        else:  # Mutation parts have different genotypes, keep them seperate for vcf.
                            x = AG1998_part1_df.to_string(header=False, index=False).split('\n')
                            vals = [",".join(ele.split()) for ele in x]
                            outfile.write("\t".join(vals) + "\n")  # Write AG1998_part1 first.

                    # Keep track of indel AG3268 - DATE 190401
                    if df.iloc[1] == 51890841:  # We are in chr6_51890841_TG_T
                        AG3268_part1_alt = df.iloc[4]  # Keep track for NNN (no calls).
                        AG3268_part1 = df.iloc[9]  # Keep track of genotype.
                        AG3268_part1_df = df  # Save df.
                        continue  # Next loop will be chr6_51890847_G_C
                    if df.iloc[1] == 51890847:  # We are in chr6_51890847_G_C
                        AG3268_part2_alt = df.iloc[4]  # Get alt variants (for NNN if exists).
                        AG3268_part2 = df.iloc[9]
                        AG3268_part1_GT = AG3268_part1.split(":")[0]  # Get genotype.
                        AG3268_part2_GT = AG3268_part2.split(":")[0]  # Get genotype.
                        if AG3268_part1_GT == AG3268_part2_GT:  # Both parts of the mutation have equal genotypes, we combine into one.
                            df.iloc[1] = "51890845"  # Position.
                            df.iloc[3] = "GGG"  # Ref.
                            if ("NNN" in AG3268_part1_alt) or (
                                    "NNN" in AG3268_part2_alt):  # Check if mutation is no call.
                                df.iloc[4] = "NNN,GC"  # Alt (no call).
                            else:
                                df.iloc[4] = "GC"  # Alt.
                            AG3268_part1_VF = AG3268_part1.split(":")[4]  # Get variant frequency.
                            AG3268_part2_VF = AG3268_part2.split(":")[4]  # Get variant frequency.
                            if AG3268_part1_VF > AG3268_part2_VF:  # Take stats with higher variant frequency.
                                df.iloc[9] = AG3268_part1
                        else:  # Mutation parts have different genotypes, keep them seperate for vcf.
                            x = AG3268_part1_df.to_string(header=False, index=False).split('\n')
                            vals = [",".join(ele.split()) for ele in x]
                            outfile.write("\t".join(vals) + "\n")  # Write AG3268_part1 first.

                    # The medium CNVs dealt separately because of soft clipped reads
                    medium_cnvs = ['chr1-196716420-TATCCAACTTGTGCAAAAAGATAGA-T', 'chr1-235564867-TGGGAGCCACGAA-T',
                                   'chr10-13699443-C-CCTGGGACTCCAGG', 'chr7-143036379-ATACCCTGCGGAGGC-A',
                                   'chr6-66204879-CTCAGCCACTTAGAAT-C', 'chr3-53265545-C-CCAGAAGATAAGGAGGTAG']
                    mutation = str(df.iloc[0]) + '-' + str(df.iloc[1]) + '-' + df.iloc[3] + '-' + df.iloc[4]
                    if mutation in medium_cnvs:
                        df = SoftClipsSolution.Parser_AnalysisWithSoftClips(inputFile, bamFilesDir, df, mutation, sampleName, logger_name)
                        # logger_path = re.sub('[^\\\/]+\.genome\.vcf', '', inputFile)
                        # logger(logger_path, input_file_name)
                    parser_logger.info("# writing mutation's data to output file")

                    x = df.to_string(header=False, index=False).split('\n')
                    vals = [",".join(ele.split()) for ele in x]
                    outfile.write("\t".join(vals) + "\n")
                    # print ("\t".join(vals)+"\n")


'''
    Purpose: wrap the parser so it can be run as a standalone module
    Input: (string) VCF files path, (string) VS2 files path, (string) MyScreen version, (string) BAM files path
    Output: None (the output is created in parserMainFunction)
'''
def MAIN_ParserWrapper(input_file, output_path, myscreen_version, logger_name, bam_files_path=''):
    if 'phased' in input_file:
        return
    genome_input_file_name = re.findall('[^\\\/]+\.genome\.vcf', input_file)
    input_file_name = re.sub('\.genome\.vcf', '', genome_input_file_name[len(genome_input_file_name)-1])
    input_file_dir = re.sub('[^\\\/]+\.genome\.vcf', '', input_file)
    if bam_files_path == '':
        bam_files_path = re.sub(r'{}_RESULTS.+'.format(myscreen_version), '', input_file)
    if os.path.isdir(input_file_dir):
        logger(input_file_dir, input_file_name, logger_name)
    else:
        parser_logger.error(Exception("Invalid input path"))
        raise Exception("Invalid input path")  # throw exception
    if not os.path.isdir(output_path):
        parser_logger.error(Exception("Invalid output path"))
        raise Exception("Invalid output path")  # throw exception
    if not os.path.isdir(bam_files_path):
        parser_logger.error(Exception("Invalid BAM files path"))
        raise Exception("Invalid BAM files path")  # throw exception

    parser_logger.info("**Starting to parse sample: {}**".format(input_file_name))
    parser_logger.info('file\'s path: {}'.format(input_file_dir))
    parser_logger.info('----------------------------------------------------')
    norm_vcf_file = cfg.norm_vcf
    output_file = os.path.join(output_path, input_file_name + '.genome.VS2.vcf')
    parserMainFunction(input_file, output_file, bam_files_path, norm_vcf_file, input_file_name, logger_name)
    parser_logger.info("Finished parsing\n")
    print("Finished parsing sample: {}".format(input_file_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('vcf_file', help='Path of a specific vcf file')
    parser.add_argument('output_dir', help='Directory of the VS2 files (output)')
    parser.add_argument('MyScreen_version', help='MyScreen version and version date (for reports)')
    parser.add_argument('-b', '--bams_path', help='Directory where the BAM files reside (optional)', default='')
    args = parser.parse_args()

    if args.bams_path:
        bams_dir = args.bams_path
    else:
        bams_dir = ''

    MAIN_ParserWrapper(args.vcf_file, args.output_dir, args.MyScreen_version, bams_dir)
