#coding: utf8
import zipfile

dest_file = r"w:\enhance_data_13Q2\13Q2_MJO\USA_AZ_PHOENIX.zip"
dest_path = r"d:\o"

zipContents = zipfile.ZipFile(dest_file, 'r').namelist()

#print zipContents
zipfile.ZipFile(dest_file).extractall(dest_path)

# IOError: [Errno 2] No such file or directory: 'd:\\o\\TEXTURES\\NAVTEQ'
