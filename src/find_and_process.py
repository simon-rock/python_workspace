#coding: utf8
import glob
import os
import os.path
import sys
from optparse import OptionParser
global all_paths
all_paths = []
def make_dir(path, clean=False):
    '''make directory'''
    if not os.path.exists(path):
        os.makedirs(path)
    elif clean:
        shutil.rmtree(path)
        os.makedirs(path)


def traverse_handle(indir, out, handle_folder_process, handle_file_process, build_tree = True):
    make_dir(out)
    for o in os.listdir(indir):
        o_path = os.path.join(indir, o)
        if build_tree:
            o_out = os.path.join(out, o)
        else:
            o_out = out
        if os.path.isdir(o_path):            
            handle_folder_process(o_path, o_out, handle_folder_process, handle_file_process, build_tree)
        if os.path.isfile(o_path):
            handle_file_process(o_path, out)

def traverse_handle_for_dir(indir, out, handle_folder_process, handle_file_process, build_tree = True):
    make_dir(out)
    for o in os.listdir(indir):
        o_path = os.path.join(indir, o)
        if build_tree:
            o_out = os.path.join(out, o)
        else:
            o_out = out
        if os.path.isdir(o_path):
            if not cmp(o, "clipped"):
                #print o_path
                all_paths.append(o_path)
            else:
                handle_folder_process(o_path, o_out, handle_folder_process, handle_file_process, build_tree)

def landmark_process(file, out):
#    print "[", file, "]  ==>>  [", out,"]"
    if file.endswith("obj.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        args = [gzout, '-d', out]
        obj2bin.main(args)
        path, filename = os.path.split(gzout)
        pt, ext = os.path.splitext(filename)
        if not lm_table.has_key(pt):
            lm_table[pt] = ",0,0\n"
        #table_path = os.path.join(out, "landmark_table.txt")
        #fp = open(table_path, "a")
        #fp.write("%s,,0,0\n"%pt)
        #fp.close()
    elif file.endswith("jpg.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        png_path = gzout.replace(".jpg", ".PNG")
        path, filename = os.path.split(png_path)
        png_path = os.path.join(out, TEMP_PNG,filename)
        args = [CONVERT, gzout, png_path]
        runprog(args)
    elif file.endswith("png.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        png_path = gzout.replace(".png", ".PNG")
        path, filename = os.path.split(png_path)
        png_path = os.path.join(out, TEMP_PNG,filename)
        args = [CONVERT, gzout, png_path]
        runprog(args)
    elif file.endswith("_link.xml.gz"):
        print "process : ", file
        gzout = file[0:file.index(".gz")]
        ungzip(file, gzout)
        load_landmark_reference_point(gzout)

def get_options(args=None):
    '''get options'''
    parser = OptionParser()
    #parser.add_option('-d', '--outputdir',action='store', dest='outdir', default='.', help='*.BIN files output directory')
    #parser.add_option('-t', '--TT', action="store_true", dest='tt_nt', default=False, help='process TT landmark, default NT')
    #parser.add_option('-p', '--processconfig', action="store_true", dest='processconfig', default=False, help='only process landmark_table')
    
    global HELP
    HELP = parser.format_help().strip()
    (options, argvs) = parser.parse_args(args)

    if len(argvs) < 1:
        parser.error("Please specify the directory of the file to be processed.")

    return options, argvs

def main(args=None):
    "main"
    (options, argvs) = get_options(args)
    print argvs
    print options
    dbf_path = argvs[0]
    target_path = "."
    traverse_handle_for_dir(dbf_path, target_path, traverse_handle_for_dir, landmark_process, False)

    print "start write info to file"
    out = open("output", "a")
    for elem in all_paths:
        out.write("<task id = \"dump_polygon\" path = \"%s\" fn = \"polygons\" type =\"0\" xl=\"-180\" yl=\"-90\" xh=\"180\" yh=\"90\"></task>\n"%elem)
if __name__ == '__main__':
    main()
