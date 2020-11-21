import os
import pandas as pd
import bz2
import pickle
import _pickle as cPickle
# Pickle a file and then compress it into a file with extension
def compressed_pickle(title, data):
    with bz2.BZ2File(title + '.pbz2', 'w') as f:
        cPickle.dump(data, f)

# Load any compressed pickle file
def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data

HospitalCode = {
'Zer':['MN00742', 'M05987'],
'Soroka':['M05987'],
'Belinson':['MN00937', 'M04441'],
'Carmel':['MN00885'],
'Maccabi':['M06216'],
'Meir':['MN01010', 'MN01026'],
'Meuhedet':['MN01006']
}

hospitalCodes_list=list(HospitalCode.values())
hospitalCodes_list = [item for sublist in list(HospitalCode.values()) for item in sublist]
# flatten = lambda t: [item for sublist in t for item in hospitalCodes_list]
print(flat_list)
# df = pd.read_excel(open('ver2.xlsx', 'rb'), sheet_name='Sheet1')
# print(df)
# last_vcf = None
# last_key = None
# agids = []
# for index, row in df.iterrows():
#     cur_vcf = row.vcf
#     cur_key = row.key
#     if cur_vcf == last_vcf and cur_key == last_key:
#         agid = agids.pop()
#         agids.append(agid + '/' + row.agid)
#     else:
#         agids.append(row.agid)
#     last_vcf = cur_vcf
#     last_key = cur_key
# print(agids)
# compressed_pickle('Clalit.AGID', agids)
# Clalit = pd.DataFrame(agids, columns =['AGID'])
# # print(Clalit)
# Clalit.to_csv('Clalit.Panel', index=False)
# data = decompress_pickle('Bedouin.AGID.pbz2')
# # print(len(data))
# data = [agid for line in data for agid in line.split('/')]
# # print(data)
# # print(len(data))
# Bedouin = pd.DataFrame(data, columns =['AGID'])
# # print(Bedouin)
# agids = []
# sex = ['AG3763', 'AG3764', 'AG3765', 'AG3766/AG3767']
# for a in data:
#     df_c = df.where(df.vcf == df.loc[df.agid == a]['vcf'].values[0])
#     df_c.dropna(how='all', inplace=True)
#     df_c.reset_index(inplace=True)
#     if len(df_c) <= 1:
#         agids.append(a)
#     elif len(df_c) > 1:
#         tmp = df_c.agid.to_list()
#         agids.append('/'.join(tmp))
# for s in sex:
#     agids.append(s)
# print(agids)
# print(len(agids))
# compressed_pickle('Bedouin.AGID', agids)
# Bedouin = pd.DataFrame(agids, columns =['AGID'])
# Bedouin.to_csv('Bedouin.Panel', index=False)

# for file in ['Bedouin.Panel', 'Clalit.Panel']:
#     bedouin = pd.read_csv(file)
#     print(bedouin)
#     bedouin['AGID2'] = bedouin.AGID.str.split('/')
#     bedouin = bedouin.explode('AGID2')
#     merged_df = pd.DataFrame(list(bedouin.AGID2) + list(set(list(bedouin.AGID)) - set(list(bedouin.AGID2))), columns=['AGID'])
#     merged_df.drop_duplicates(inplace=True)
#     merged_df.to_csv(file, index=False)
#     print(merged_df)
#     s = list(merged_df.AGID)
#     compressed_pickle(file, s)
#     with open(file + '.txt', 'w') as filehandle:
#         for listitem in s:
#             filehandle.write('%s\n' % listitem)
    # print(s)
# bedouin = decompress_pickle('Bedouin.Panel.pbz2')
# clalit = decompress_pickle('Clalit.Panel.pbz2')
#
# for file in os.listdir():
#     if file.endswith('.pbz2') and "Panel" not in file:
#         print(file)
#         df = decompress_pickle(file)
#         samples = set(list(df.Sample))
#         for sample in samples:
#             tmp = df.groupby(['Sample'])
#             print(tmp)
#         # print(df)
