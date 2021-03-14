import sys, os, time, datetime

# Number of working threads
n_workrs = 5

# Path to output CSV and PSV results
# For example: CSV_dir = r"C:\Gamidor\csv directory name"
CSV_dir = r"path\to\directory"

# Working directory and date time
curdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
date = datetime.datetime.now().strftime("%d-%m-%Y")

#Global Strings to incoopraite in GUI and to change in version update
MyScreen_Ver = "MyScreen_Analysis_v2.2"
Label = "MyScreen Analysis v2.2 - Gamidor AppliedGenomics"
Main_Dir = "{}_RESULTS".format(MyScreen_Ver)
MutPDF = "Ver-{}[November2020]".format(MyScreen_Ver.split('v')[-1]) #Mutation PDF update date
AG_DB = os.path.join('C:\\', 'Gamidor', 'Appendix', 'AG_DB')
AG_DB_excel = os.path.join('C:\\', 'Gamidor', 'Appendix', 'db_statistics-v2.xlsx')

# Hospitals
Hospitals = os.path.join(curdir, 'docs', 'word_templates')
HospitalCode = {
'Zer':['MN00742'],
'Soroka':['M05987'],
'Belinson':['MN00937', 'M04441'],
'Carmel':['MN00885'],
'Maccabi':['M06216'],
'Meir':['MN01010'],
'Bnei-Zion':['M02633']
}
# נספחים ופרוטוקולים
vald_pos = os.path.join(curdir, '..', 'נספחים ופרוטוקולים', 'MyScreen_DISCLOSE-Postive_(11-03-2021).xlsx')
appnote = os.path.join(curdir, '..', 'נספחים ופרוטוקולים', 'MyScreen.V2.2_App.Note.pdf')
mut_list = os.path.join(curdir, '..', 'נספחים ופרוטוקולים')

# Avilable panels
Panels = [['Extended', '0001'], ['Clalit', '0002'], ['Bedouin', '0003']]
Panels_names = [item[0] for item in Panels]
path_to_panel = os.path.join(curdir, 'docs')

# DMD mutation makats
DMD = {
    'AG5062_1':149201,
    'AG5062_2':149220,
    'AG5062_3':149221,
    'AG5062_4':149222,
    'AG5062_5':149223,
    'AG5100_1':149204,
    'AG5100_2':149226,
    'AG5100_3':149227,
    'AG5100_4':149228,
    'AG5100_5':149229
    }


# Images
AG_logo = os.path.join(curdir, 'images', 'ag_logo.ico')
MyScreen_png = os.path.join(curdir, 'images', 'myscreen-canva.png')
MyScreen_Summary = os.path.join(curdir, 'images', 'myscreen.summary.png')

# Files
norm_vcf = os.path.join(curdir, 'docs', 'Norm.RC.sort.vcf')
norm_txt = os.path.join(curdir, 'docs', 'Norm.RC.sort.txt')
anno_excel = os.path.join(curdir, 'docs', 'anno.xlsx')
GenoAnno = 'GenoAnno'
GenoBED = 'GenoBED'
bed_pkl = os.path.join(curdir, 'docs', 'GenoBED.pkl')
anno_pkl = os.path.join(curdir, 'docs', 'GenoAnno.pkl')
ver2_agids = os.path.join(curdir, 'docs', 'ver2.agids')

hg19 = os.path.join('C:\\', 'Gamidor', 'Appendix', 'Genotyping', 'genome.fa')
cnvBED = os.path.join(curdir, 'docs', 'CNVtargets.bed')
cnvCustomExons = os.path.join(curdir, 'docs', 'CNVcustom.txt')
cnvTargets = os.path.join(curdir, 'docs', 'anno.xlsx')
CNVtargets = 'CNVtargets'
CNVAnno = 'CNVAnno'
annotCNV = os.path.join(curdir, 'docs', 'CNVAnno.pkl')
bedCNV = os.path.join(curdir, 'docs', 'CNVtargets.pkl')


""" Genotyping """
pisces = os.path.join('C:\\', 'Gamidor', 'Appendix', 'Genotyping', '5.2.8.44', 'Pisces', 'Pisces.dll')
genome_dir = os.path.join('C:\\', 'Gamidor', 'Appendix', 'Genotyping')
pisces_cmd = "dotnet " + pisces + " -SBFilter 1000 -Bam {} -G " + genome_dir + " --minvq 10 \
    -MinMapQuality 0 -diploidsnvgenotypeparameters 0.20,0.90,0.80 \
    -diploidindelgenotypeparameters 0.20,0.90,0.80 -MinBaseCallQuality 12  \
    -VQFilter 10 -CallMNVs false -MinDepth 5 -Ploidy diploid -OutFolder \
    \"{}_RESULTS\\Info\\Genotyping\\Logs\" -forcedalleles " + norm_vcf + " -crushvcf false -IntervalPaths " + norm_txt

scylla_cmd = "dotnet C:\\Gamidor\\Appendix\\Genotyping\\5.2.5.20\\Scylla\\Scylla.dll -b 10 -bam {} -vcf \
        {}_RESULTS\\Info\\Genotyping\\Logs\\{}.genome.vcf"

GenoPickles = ['All', 'PositiveGenotype', 'WT_Poly', 'Gender', 'NonReported']
FullGeno = 'GenoParsed'


""" CNV """
decon_master = os.path.join('C:\\', 'Gamidor', 'Appendix', 'DECoN-master')

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

template_dict = os.path.join(curdir, 'docs', 'word_templates')
template_sick = template_dict + '\\{}\\template_sick.docx'
template_norm = template_dict + '\\{}\\template_norm.docx'
template_carrier = template_dict + '\\{}\\template_carrier.docx'
template_carrier_and_sick = template_dict + '\\{}\\template_carrier_and_sick.docx'

# Classifictions
Classifictions = {
"WT" : ["WT",  "WT - With soft-clipped reads",  "WT - Low GQX - NON_REPORTED variant in the same loc"],
"PROBLEM" : ["WT-Problem",  "WT-Problem - With soft-clipped reads",  "NO_CALL",
           "NO_CALL-Problem",  "CARRIER-Problem", "CARRIER-Georgian-Problem",
           "CARRIER-Druze-Problem",  "CARRIER-Problem - With soft-clipped reads",
           "CARRIER-Georgian-Problem - With soft-clipped reads", "HOM-Problem",
           "CNV-Problem", "CNV Big Del Boundaries Different as Reported-Problem"],
"NON_REPORTED" : ["NON_REPORTED", "NON_REPORTED-Problem", "POLYMORPHISM", "POLYMORPHISM-Problem"],
"CARRIER" : ["CARRIER" , "CARRIER-Georgian", "CARRIER-Druze",  "CARRIER - With soft-clipped reads",
           "CARRIER-Georgian - With soft-clipped reads",  "CNV",  "CNV Big Del Boundaries Different as Reported"],
"HOM" : ["HOM", "HOM - With soft-clipped reads", "HOM-Problem - With soft-clipped reads"]
}

Classifictions_star = {
"WT" : ["WT", '---'],
"CARRIER" : ["CARRIER", "CNV"],
"HOM" : ["HOM"]
}
