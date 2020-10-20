import subprocess
import os
import logging
import warnings
import pandas as pd
#from pandas.core.common import SettingWithCopyWarning
#warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
import re
import csv
import argparse

pd.set_option('display.max_colwidth', None)

'''
    Purpose: create informative error for the user based on given parameters
    Input: (string) mutation {chr-position-ref-alt}, (string) the issue subject, (string) error message
    Output: (exception) throw an error based on given parameters
'''
def getError(mutation, issue, error=''):
    e = Exception("# WARNING: Error occurred with the " + issue + " while analyzing mutation " + mutation + ":" + error + "\nGenotyping Analysis failed to complete.")
    soft_clips_logger.error(e)
    raise e

'''
    Purpose: to check if the read is relevant based on it's attributes
    Input: (string) flag - a binary number when each bit represent another attribute (based on Samltools convention)
    Output: (boolean) true - if the read is relevant, false- otherwise
'''
def isLegalRead(flag):
    flag = str(flag.lstrip('0b'))
    length = len(flag)
    if length < 2:
        return False
    if flag[length - 1] == '0' or flag[length - 2] == '0':
        return False
    if length >= 10:
        return False
    return True


'''
    Purpose: calculate GT (genotyping)
    Input: (float) ratio between positive reads and total reads
    Output: (string) 1/1 - if it's hom/NNN, 0/1 - if it's het, 0/0 - if it's WT
'''
def GTCalculator(ratio):
    if ratio >= 0.7:
        return "1/1"
    if ratio >= 0.2:
        return "0/1"
    if ratio > 0:
        return "1/1"
    else:
        return "0/0"


'''
    Purpose: calculate GQX (quality)
    Input: (float) ratio between positive reads and total reads
    Output: (string) 0 - if 0<ratio<0.2, 20 - if 0.2<=ratio<0.3, 100 - if ratio>=0.3
'''
def GQXCalculator(ratio):
    if 0.2 > ratio > 0:
        return '0'
    if 0.3 > ratio >= 0.2:
        return '20'
    else:
        return '100'


'''
    Purpose: logger - document the analysis steps
    Input: (string) path for the logger file (txt) to be set in
    Output: None
'''
def logger(out, logger_name):
    # log_file = "{}SoftClipsSolution.log".format(out)
    # for handler in logging.root.handlers[:]:
    #     logging.root.removeHandler(handler)
    # logging.basicConfig(filename=log_file,
    #                     level=logging.INFO,
    #                     format='%(asctime)s %(levelname)-8s %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # global soft_clips_logger
    # soft_clips_logger = logging.getLogger('SoftClipsSolution.log')
    global soft_clips_logger
    soft_clips_logger = logging.getLogger(logger_name)


'''
    Purpose: calculate ratio between positive reads and total reads (covering the whole indel)
    Input: (string) bam files path, (string) chromosome, (int) position, (string) ref, (string) alt, (string) smaple's name, (string) mutation {chr-position-ref-alt}
    Output: array with number of het read(positive and soft-clipped)[0], and number of total reads covering the whole indel[1]
'''
def refAltRatioCalculator(bam_files_dir, chr, position, ref, alt, sampleName, mutation):
    # Create variables relevant for analysis
    softClipsReads = []
    totalReads = []
    readsWithIndel = []
    indelLength = abs(len(ref) - len(alt))
    mutationSize = indelLength
    if position == 196716420:
        mutationSize += 1

    # Start the analysis
    os.chdir(bam_files_dir)
    soft_clips_logger.info("# Fetching Samtools results")
    for locus in range(position, position + mutationSize + 2):
        positionCommand = """samtools view {} {}:{}-{}""".format(sampleName, chr, locus, locus)  # | awk '{if(($5)!=0) {if($6 ~ /S/) {i++}}} END {print(i)}'"""
        positionResult = subprocess.Popen(positionCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        results, error = positionResult.communicate()
        if error.decode() != '':
            getError(mutation, "Samtools", error.decode().rstrip())  # throw exception
        readsPerLocus = []
        for row in results.decode().splitlines():
            rowFixed = row.split('\t')
            if isLegalRead(bin(int(rowFixed[1]))):
                if not rowFixed[0] in readsPerLocus and int(rowFixed[4]) > 0:
                    readsPerLocus.append(rowFixed[0])
                if not rowFixed[0] in softClipsReads and "S" in rowFixed[5] and int(rowFixed[4]) > 0:
                    softClipsReads.append(rowFixed[0])
                if not rowFixed[0] in readsWithIndel and str(indelLength) + "D" in rowFixed[5] and int(rowFixed[4]) > 0:
                    readsWithIndel.append(rowFixed[0])
                if not rowFixed[0] in readsWithIndel and str(indelLength) + "I" in rowFixed[5] and int(rowFixed[4]) > 0:
                    readsWithIndel.append(rowFixed[0])
        totalReads.append(readsPerLocus)
    soft_clips_logger.info("# Calculating number of reads covering the whole indel")
    totalReadsNum = len(set(totalReads[0]).intersection(*totalReads))
    soft_clips_logger.info("# Calculating number of positive reads, including soft-clipped ones")
    totalHetReadsNum = len(softClipsReads) + len(readsWithIndel)
    return [totalReadsNum, totalHetReadsNum]


'''
    Purpose: manage the soft-cliped reads analysis and integrate the various functions
    Input:  (string) bam files path,
            (dataframe) df - with all the data of the analyzed mutation from Pisces,
            (string) sample's name
    Output: new df with the new data
'''
def AnalysisWithSoftClippedReads(bam_files_dir, df, sampleName):
    # Create first variables
    sampleData = df.iloc[9].split(':')
    chr = df.iloc[0]
    pos = int(df.iloc[1])
    ref = df.iloc[3]
    alt = df.iloc[4]
    mutation = str(chr) + '-' + str(pos) + '-' + ref + '-' + alt

    # Check for positive reads. if there are'nt no analysis is needed
    if float(sampleData[len(sampleData) - 1]) == 0:
        soft_clips_logger.info("No positive reads for the mutation were found in this sample based on Genotyping results.")
        soft_clips_logger.info("Therefore no further calculations were done")
        return df

    # Start the analysis
    soft_clips_logger.info("Found positive reads for the mutation")
    soft_clips_logger.info("Calculating positive reads (including soft-clipped reads)/total reads ratio:")
    newData = refAltRatioCalculator(bam_files_dir, chr, pos, ref, alt, sampleName, mutation)
    if newData[0] != 0:
        ratio = round(newData[1] / newData[0], 3)
    else:
        getError(mutation, "ratio calculation", "total reads=0 causing division by zero")  # throw exception
    soft_clips_logger.info("Calculating GT")
    sampleData[0] = GTCalculator(ratio)
    soft_clips_logger.info("Calculating GQ")
    sampleData[1] = GQXCalculator(ratio)
    sampleData[2] = str(newData[0] - newData[1]) + ',' + str(newData[1])
    sampleData[3] = str(newData[0])
    sampleData[4] = str(ratio)
    if newData[1] != 0 and (':'.join(sampleData)) != df.iloc[9]:
        soft_clips_logger.info("Editing Genotyping raw data according to the new calculated ratio")
        if sampleData[1] == '0':
            df.iloc[4] = 'NNN,' + df.iloc[4]
        df.iloc[7] = 'DP=' + str(newData[0])
        df.iloc[9] = ':'.join(sampleData)
        df.iloc[5] = -1 # indicator to mark "-With soft clipped reads" or not
    else:
        getError(mutation, "ratio calculation", "ratio calculated as 0 although positive reads were found")  # throw exception

    # finished the analysis
    return df


'''
    Purpose: the main function to run the soft-clipped analysis from the parser
    Input:  (string) input_file (for logger's path),
            (string) bam files path (to extract BAM file ahead),
            (dataframe) df - with all the data of the analyzed mutation from Pisces,
            (string) mutation,
            (string) sample's name
    Output: new df with the new data (AnalysisWithSoftClippedReads's output)
'''
def Parser_AnalysisWithSoftClips(input_file, bam_files_dir, df, mutation, sampleName, logger_name):
    # check for legal path
    logger_path = re.sub('[^\\\/]+\.genome\.vcf', '', input_file)
    if os.path.isdir(logger_path):
        logger(logger_path, logger_name)
    else:
        getError(mutation, "input path")  # throw exception

    soft_clips_logger.info('Starting to analyze mutation {} in sample: {}'.format(mutation, sampleName))
    result_df = AnalysisWithSoftClippedReads(bam_files_dir, df, sampleName)
    soft_clips_logger.info('')
    # return analysis results
    return result_df


'''
    Purpose: wrap the analysis with soft-clipped reads solution so it can be run as a standalone module
    Input: (string) VS2 files path, (string) MyScreen version, (string) BAM files path
    Output: new VS2 files with the new data
'''
def MAIN_AnalysisWithSoftClipsWrapper(input_path, myscreen_version, logger_name, bam_files_path=''):
    if bam_files_path == '':
        bam_files_path = re.sub(r'{}_RESULTS.+'.format(myscreen_version), '', input_path)
    mutations_list = ['chr1-196716420-TATCCAACTTGTGCAAAAAGATAGA-T', 'chr1-235564867-TGGGAGCCACGAA-T', 'chr10-13699443-C-CCTGGGACTCCAGG', 'chr7-143036379-ATACCCTGCGGAGGC-A']

    # check for legal paths
    logger_path = os.path.join(input_path, 'Logs' + os.sep)
    if os.path.isdir(logger_path):
        logger(logger_path, logger_name)
    else:
        logger(input_path, logger_name)
    if not os.path.isdir(input_path):
        soft_clips_logger.error(Exception("Invalid input path"))
        raise Exception("Invalid input path")  # throw exception
    if not os.path.isdir(bam_files_path):
        soft_clips_logger.error(Exception("Invalid BAM files path"))
        raise Exception("Invalid BAM files path")  # throw exception
    soft_clips_logger.info("**Analysis with soft-clipped reads session started**")
    soft_clips_logger.info('input path: {}'.format(input_path))
    soft_clips_logger.info('----------------------------------------------------')

    # create a list of all the VS2 files in the path
    files = []
    for filename in os.listdir(input_path):
        if filename.endswith(".VS2.vcf"):
            files.append(filename)

    # start analyzing each sample in iteration
    for vcfFile in files:
        os.chdir(input_path)
        lines = []
        with open(vcfFile, 'r+') as csv_file:
            sampleName = re.sub('\.genome.+', '.bam', vcfFile)
            soft_clips_logger.info('checking sample: {}'.format(sampleName))
            csv_reader = csv.reader(csv_file, delimiter="\t")
            for row in csv_reader:
                if re.match('^#.*', row[0]):  # ignore header matching "#"
                    lines.append(row)
                    continue
                df = pd.Series(row).to_frame().T
                df = df.iloc[0]
                mutation = str(df.iloc[0]) + '-' + str(df.iloc[1]) + '-' + df.iloc[3] + '-' + str(df.iloc[4]).replace('NNN,', '')
                if mutation in mutations_list:
                    soft_clips_logger.info('Starting to analyze mutation {}'.format(mutation))
                    df = AnalysisWithSoftClippedReads(bam_files_path, df, sampleName)
                x = df.to_string(header=False, index=False).split('\n')
                vals = [",".join(ele.split()) for ele in x]
                lines.append(vals)
            soft_clips_logger.info('finished analyzing sample: {} with soft-clipped reads\n'.format(sampleName))
            csv_file.close()
            os.chdir(input_path)
            writeBackFile = open(vcfFile, 'w')
            for line in lines:
                writeBackFile.write("\t".join(line) + "\n")
            writeBackFile.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('VS2_files_path', help='Directory Contains VS2 vcf files')
    parser.add_argument('MyScreen_version', help='MyScreen version and version date (for reports)')
    parser.add_argument('logger', help='logger name')
    parser.add_argument('-b', '--bams_path', help='Directory where the BAM files reside (optional)', default='')
    args = parser.parse_args()

    if args.bams_path:
        bams_path = args.bams_path
    else:
        bams_path = ''
    MAIN_AnalysisWithSoftClipsWrapper(args.VS2_files_path, args.MyScreen_version, args.logger, bams_path)
