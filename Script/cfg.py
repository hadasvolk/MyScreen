import sys, os, time, datetime

curdir = os.path.dirname(os.path.realpath(__file__))
date = datetime.datetime.now().strftime("%d-%m-%Y")

# Number of working threads
n_workrs = 3

#Global Strings to incoopraite in GUI and to change in version update
MyScreen_Ver = "MyScreen_Analysis_v2.0.c"
Label = "MyScreen Analysis v2.0.c - Gamidor AppliedGenomics"
Main_Dir = "{}_RESULTS".format(MyScreen_Ver)
Hospitals = '{}/docs/word_templates'.format(curdir)
MutPDF = "Ver-{}[October2020]".format(MyScreen_Ver.split('v')[-1]) #Mutation PDF update date
AG_DB = "C:/Gamidor/Appendix/AG_DB"
AG_DB_excel = 'C:/Gamidor/Appendix/db_statistics-v2.xlsx'

# נספחים ופרוטוקולים
vald_pos = '{}/../נספחים ופרוטוקולים/MyScreen_VALIDATED-Postive.xlsx'.format(curdir)
appnote = '{}/../נספחים ופרוטוקולים/MyScreen.V2.0.c_App.Note2000714.pdf'.format(curdir)
mut_list = '{}/../נספחים ופרוטוקולים/(2020-08-11) Ver 2.0.c - רשימת מחלות ומוטציות גירסה.pdf'.format(curdir)

# Avilable panels
Panels = ('Bedouin', 'Extended')
path_to_panel = '{}/docs/'.format(curdir)

# Images
AG_logo = '{}/images/ag_logo.ico'.format(curdir)
MyScreen_png = '{}/images/myscreen-canva.png'.format(curdir)
MyScreen_Summary = '{}/images/myscreen.summary.png'.format(curdir)

# Files
norm_vcf = '{}/docs/Norm.RC.sort.vcf'.format(curdir)
norm_txt = '{}/docs/Norm.RC.sort.txt'.format(curdir)
anno_excel = '{}/docs/anno.xlsx'.format(curdir)
GenoAnno = 'GenoAnno'
GenoBED = 'GenoBED'
bed_pkl = '{}/docs/GenoBED.pkl'.format(curdir)
anno_pkl = '{}/docs/GenoAnno.pkl'.format(curdir)
ver2_agids = '{}/docs/ver2.agids'.format(curdir)

hg19 = "C:/Gamidor/Appendix/Genotyping/genome.fa"
cnvBED = '{}/docs/CNVtargets.bed'.format(curdir)
cnvCustomExons = '{}/docs/CNVcustom.txt'.format(curdir)
cnvTargets = '{}/docs/anno.xlsx'.format(curdir)
CNVtargets = 'CNVtargets'
CNVAnno = 'CNVAnno'
annotCNV = '{}/docs/CNVAnno.pkl'.format(curdir)
bedCNV = '{}/docs/CNVtargets.pkl'.format(curdir)


""" Genotyping """
pisces = "C:/Gamidor/Appendix/Genotyping/5.2.8.44/Pisces/Pisces.dll"
genome_dir = "C:/Gamidor/Appendix/Genotyping"
pisces_cmd = "dotnet " + pisces + " -SBFilter 1000 -Bam {} -G " + genome_dir + " --minvq 10 \
    -MinMapQuality 0 -diploidsnvgenotypeparameters 0.20,0.90,0.80 \
    -diploidindelgenotypeparameters 0.20,0.90,0.80 -MinBaseCallQuality 12  \
    -VQFilter 10 -CallMNVs false -MinDepth 5 -Ploidy diploid -OutFolder \
    \"{}_RESULTS/Info/Genotyping/Logs\" -forcedalleles " + norm_vcf + " -crushvcf false -IntervalPaths " + norm_txt

scylla_cmd = "dotnet C:/Gamidor/Appendix/Genotyping/5.2.5.20/Scylla/Scylla.dll -b 10 -bam {} -vcf \
        {}_RESULTS/Info/Genotyping/Logs/{}.genome.vcf"

GenoPickles = ['All', 'PositiveGenotype', 'WT_Poly', 'Gender', 'NonReported']
FullGeno = 'GenoParsed'


""" CNV """
decon_master = "C:/Gamidor/Appendix/DECoN-master/"

# Correlation threshold
mincorr = '0.95'
# Coverage threshold
mincov = '85'
brca = 'FALSE'
# Transition probability
tp = '0.05'
# DECoN Parser parameters
bf_limit_min = 9.9
bf_limit_max = 15
sexDepth_limit = 20
cnv_limit = 0.5
bf_limit_SMN_DMD = 5

CNVPickles = ['Calls', 'Failures_samples', 'Failures_exons']
FullCNV = 'DECoNParsed'


""" Summary """
full_results = ['Geno Full', 'Geno Positive', 'Geno WT Poly', 'Geno Gender',
                'Geno NonReported', 'CNV Calls', 'CNV Fail Samples',
                'CNV Fail Exons']

template_dict = '{}/docs/word_templates/'.format(curdir)
template_sick = template_dict + '{}/template_sick.docx'
template_norm = template_dict + '{}/template_norm.docx'
template_carrier = template_dict + '{}/template_carrier.docx'
template_carrier_and_sick = template_dict + '{}/template_carrier_and_sick.docx'
